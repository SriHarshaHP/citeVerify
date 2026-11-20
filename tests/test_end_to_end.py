import pytest
from pathlib import Path
from app.pipeline.orchestrator import run_verification_pipeline
from app.export.exporters import export_json, export_csv, export_standalone_html
from app.schemas import FlagEnum

def test_demo_document_end_to_end():
    demo_path = Path("app/demo/demo_doc.txt")
    with open(demo_path, "rb") as f:
        file_bytes = f.read()

    report = run_verification_pipeline(file_bytes, "demo_doc.txt")

    assert report.total_claims == 8
    assert report.total_pages == 2
    assert report.citation_style == "numeric"
    assert report.citation_health_indicator > 0.0
    assert report.items_needing_review_count > 0

    cards_by_id = {c.claim.id: c for c in report.claim_cards}

    # Verify all 8 planted cases
    assert cards_by_id["C1"].primary_verdict.label == "SUPPORTED"
    assert cards_by_id["C2"].primary_verdict.label == "PARTIALLY_SUPPORTED"
    assert FlagEnum.NUMBER_MISMATCH in cards_by_id["C2"].primary_verdict.flags

    assert cards_by_id["C3"].primary_verdict.label == "PARTIALLY_SUPPORTED"
    assert FlagEnum.SCOPE_OVERGENERALIZED in cards_by_id["C3"].primary_verdict.flags

    assert cards_by_id["C4"].primary_verdict.label == "UNSUPPORTED"

    assert cards_by_id["C5"].primary_verdict.label == "UNVERIFIABLE"
    assert cards_by_id["C5"].primary_verdict.unverifiable_reason.value == "reference_not_found"

    assert cards_by_id["C6"].primary_verdict.label == "UNCITED"

    assert cards_by_id["C7"].primary_verdict.label == "POSSIBLY_OUTDATED"

    assert FlagEnum.RETRACTED_SOURCE in cards_by_id["C8"].primary_verdict.flags
    assert FlagEnum.NEEDS_HUMAN_REVIEW in cards_by_id["C8"].primary_verdict.flags

    # Test exports
    json_str = export_json(report)
    csv_str = export_csv(report)
    html_str = export_standalone_html(report)

    assert "CiteVerify" in json_str
    assert "C1" in csv_str
    assert "<!DOCTYPE html>" in html_str
