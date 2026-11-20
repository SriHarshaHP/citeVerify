import os
import io
import json
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from app.config import settings
from app.schemas import (
    VerificationReport,
    ReviewOverrideRequest,
    ReviewerActorEnum,
    ReviewerActionEnum,
    AuditEntry
)
from app.pipeline.orchestrator import run_verification_pipeline
from app.export.exporters import export_json, export_csv, export_standalone_html, export_corrected_bib
from app.core.audit import audit_manager

app = FastAPI(
    title=settings.APP_NAME,
    description="Scientific Claim and Citation Verification System — Academic Integrity Copilot",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active session report
active_report: Optional[VerificationReport] = None

class VerifyTextRequest(BaseModel):
    text: str
    filename: Optional[str] = "pasted_document.txt"

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "offline_demo": settings.OFFLINE_DEMO,
        "llm_provider": settings.LLM_PROVIDER
    }

@app.post("/api/verify/text", response_model=VerificationReport)
async def verify_text_endpoint(req: VerifyTextRequest):
    global active_report
    try:
        content = req.text.encode("utf-8")
        filename = req.filename or "pasted_document.txt"
        report = run_verification_pipeline(content, filename)
        active_report = report
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@app.post("/api/verify/upload", response_model=VerificationReport)
async def verify_upload(file: UploadFile = File(...)):
    global active_report
    try:
        content = await file.read()
        filename = file.filename or "uploaded_document.pdf"
        report = run_verification_pipeline(content, filename)
        active_report = report
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@app.post("/api/verify/demo", response_model=VerificationReport)
async def verify_demo():
    global active_report
    demo_file = Path(__file__).parent / "demo" / "demo_doc.txt"
    if not demo_file.exists():
        raise HTTPException(status_code=404, detail="Demo document not found.")
    
    with open(demo_file, "rb") as f:
        content = f.read()

    report = run_verification_pipeline(content, "demo_doc.txt")
    active_report = report
    return report

@app.get("/api/reports/latest")
async def get_latest_report():
    global active_report
    if not active_report:
        # Pre-warm with demo report if none loaded yet
        return await verify_demo()
    return active_report

@app.post("/api/review/action")
async def submit_review_action(req: ReviewOverrideRequest):
    global active_report
    if not active_report:
        raise HTTPException(status_code=400, detail="No active report loaded.")

    card = next((c for c in active_report.claim_cards if c.claim.id == req.claim_id), None)
    if not card:
        raise HTTPException(status_code=404, detail=f"Claim {req.claim_id} not found in report.")

    before_val = {
        "label": card.primary_verdict.label,
        "final_verdict": card.final_verdict,
        "score": card.primary_verdict.evidence_strength_score,
        "status": card.reviewer_status
    }

    user_note = req.note or req.justification

    # Apply actions
    if req.action == ReviewerActionEnum.ACCEPTED:
        card.reviewer_status = "accepted"
        card.reviewer_action = "accepted"
        card.final_verdict = card.primary_verdict.label
        note = user_note or "Reviewer verified and accepted automated finding."
    elif req.action == ReviewerActionEnum.REJECTED:
        card.reviewer_status = "rejected"
        card.reviewer_action = "rejected"
        card.final_verdict = "REJECTED"
        note = user_note or "Reviewer rejected the automated verification result."
    elif req.action == ReviewerActionEnum.MARK_FALSE_POSITIVE:
        card.reviewer_status = "false_positive"
        card.reviewer_action = "mark_false_positive"
        card.final_verdict = "FALSE_POSITIVE"
        note = user_note or "Reviewer marked this finding as a false positive."
    elif req.action == ReviewerActionEnum.OVERRIDDEN:
        if not req.new_verdict:
            raise HTTPException(status_code=400, detail="New verdict is required for override action.")
        card.reviewer_override = req.new_verdict
        card.reviewer_status = "overridden"
        card.reviewer_action = "overridden"
        card.final_verdict = req.new_verdict
        card.primary_verdict.label = req.new_verdict
        note = user_note or f"Reviewer manually changed verdict to {req.new_verdict}."
    elif req.action == ReviewerActionEnum.UNDO:
        card.reviewer_status = "pending"
        card.reviewer_action = None
        card.reviewer_override = None
        card.reviewer_note = None
        if card.ai_verdict:
            card.primary_verdict.label = card.ai_verdict
            card.final_verdict = card.ai_verdict
        note = user_note or "Reviewer reverted human edits back to initial automated verdict."
    else:  # NOTED
        card.reviewer_status = "noted"
        card.reviewer_action = "noted"
        card.reviewer_note = user_note
        note = user_note or "Reviewer attached annotation."

    if user_note:
        card.reviewer_note = user_note

    after_val = {
        "label": card.primary_verdict.label,
        "final_verdict": card.final_verdict,
        "score": card.primary_verdict.evidence_strength_score,
        "status": card.reviewer_status
    }

    # Record in SQLite audit log
    entry = audit_manager.record_entry(
        claim_id=card.claim.id,
        pair_id=req.pair_id,
        actor=ReviewerActorEnum.REVIEWER,
        action=req.action,
        before_value=before_val,
        after_value=after_val,
        note=note
    )

    card.audit_history.append(entry)
    return {
        "status": "success",
        "claim_id": card.claim.id,
        "reviewer_status": card.reviewer_status,
        "final_verdict": card.final_verdict,
        "audit_entry": entry
    }

@app.get("/api/audit/claim/{claim_id}")
async def get_claim_audit(claim_id: str):
    entries = audit_manager.get_entries_for_claim(claim_id)
    return {"claim_id": claim_id, "entries": entries}

@app.get("/api/benchmark")
async def get_benchmark_results():
    bm_path = Path("BENCHMARK_RESULTS.json")
    if bm_path.exists():
        with open(bm_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Benchmark results not yet generated"}

@app.get("/api/export/json")
async def export_json_endpoint():
    global active_report
    if not active_report:
        await verify_demo()
    json_data = export_json(active_report)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=citeverify_report_{active_report.document_name}.json"}
    )

@app.get("/api/export/csv")
async def export_csv_endpoint():
    global active_report
    if not active_report:
        await verify_demo()
    csv_data = export_csv(active_report)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=citeverify_report_{active_report.document_name}.csv"}
    )

@app.get("/api/export/html", response_class=HTMLResponse)
async def export_html_endpoint():
    global active_report
    if not active_report:
        await verify_demo()
    html_content = export_standalone_html(active_report)
    return HTMLResponse(content=html_content)

@app.get("/api/export/corrected-bib")
async def export_corrected_bib_endpoint():
    global active_report
    if not active_report:
        await verify_demo()
    bib_data = export_corrected_bib(active_report)
    return Response(
        content=bib_data,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=corrected_references_{active_report.document_name}.bib"}
    )

# Mount frontend build if exists
dist_dir = Path(__file__).parent.parent / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")
