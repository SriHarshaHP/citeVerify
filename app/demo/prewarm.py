from pathlib import Path
from app.pipeline.orchestrator import run_verification_pipeline
from app.export.exporters import export_json, export_csv, export_standalone_html

def prewarm_demo_cache():
    print("Pre-warming CiteVerify cache with demo document...")
    demo_file = Path(__file__).parent / "demo_doc.txt"
    with open(demo_file, "rb") as f:
        file_bytes = f.read()

    def progress(stage, pct):
        print(f"[{pct}%] {stage}")

    report = run_verification_pipeline(file_bytes, "demo_doc.txt", progress_callback=progress)

    print("\n--- Pre-warm Summary ---")
    print(f"Document: {report.document_name}")
    print(f"Total Claims: {report.total_claims}")
    print(f"Citation Health Indicator: {report.citation_health_indicator:.1f}%")
    print(f"Items Needing Review: {report.items_needing_review_count}")
    print("Verdicts Breakdown:", report.summary_counts)
    print("Retrieval Summary:", report.retrieval_summary)

    # Validate all 8 planted cases
    print("\n--- Validating 8 Planted Demo Cases ---")
    cards = {c.claim.id: c for c in report.claim_cards}
    
    # 1. Correct citation -> SUPPORTED
    c1 = cards.get("C1")
    assert c1 and c1.primary_verdict.label == "SUPPORTED", f"Case 1 failed: {c1.primary_verdict.label if c1 else 'None'}"
    print("Case 1 (Correct citation): SUPPORTED [PASSED]")

    # 2. Right paper, wrong number -> PARTIALLY_SUPPORTED with NUMBER_MISMATCH
    c2 = cards.get("C2")
    assert c2 and c2.primary_verdict.label == "PARTIALLY_SUPPORTED", f"Case 2 failed: {c2.primary_verdict.label if c2 else 'None'}"
    assert "NUMBER_MISMATCH" in [f.value for f in c2.primary_verdict.flags], "Case 2 NUMBER_MISMATCH flag missing"
    print("Case 2 (Wrong number 45% vs 18%): PARTIALLY_SUPPORTED + NUMBER_MISMATCH [PASSED]")

    # 3. Overgeneralized claim -> PARTIALLY_SUPPORTED with SCOPE_OVERGENERALIZED
    c3 = cards.get("C3")
    assert c3 and c3.primary_verdict.label == "PARTIALLY_SUPPORTED", f"Case 3 failed: {c3.primary_verdict.label if c3 else 'None'}"
    assert "SCOPE_OVERGENERALIZED" in [f.value for f in c3.primary_verdict.flags], "Case 3 SCOPE_OVERGENERALIZED flag missing"
    print("Case 3 (Overgeneralized pilot): PARTIALLY_SUPPORTED + SCOPE_OVERGENERALIZED [PASSED]")

    # 4. Real but unrelated paper -> UNSUPPORTED
    c4 = cards.get("C4")
    assert c4 and c4.primary_verdict.label == "UNSUPPORTED", f"Case 4 failed: {c4.primary_verdict.label if c4 else 'None'}"
    print("Case 4 (Real but unrelated): UNSUPPORTED [PASSED]")

    # 5. Nonexistent reference -> UNVERIFIABLE (reference_not_found)
    c5 = cards.get("C5")
    assert c5 and c5.primary_verdict.label == "UNVERIFIABLE", f"Case 5 failed: {c5.primary_verdict.label if c5 else 'None'}"
    print("Case 5 (Unverifiable reference): UNVERIFIABLE (reference_not_found) [PASSED]")

    # 6. Uncited claim -> UNCITED
    c6 = cards.get("C6")
    assert c6 and c6.primary_verdict.label == "UNCITED", f"Case 6 failed: {c6.primary_verdict.label if c6 else 'None'}"
    print("Case 6 (Strong uncited claim): UNCITED [PASSED]")

    # 7. Old source for time-sensitive claim -> POSSIBLY_OUTDATED
    c7 = cards.get("C7")
    assert c7 and c7.primary_verdict.label == "POSSIBLY_OUTDATED", f"Case 7 failed: {c7.primary_verdict.label if c7 else 'None'}"
    print("Case 7 (Old source for time-sensitive claim): POSSIBLY_OUTDATED [PASSED]")

    # 8. Retracted paper -> RETRACTED_SOURCE flag + NEEDS_HUMAN_REVIEW
    c8 = cards.get("C8")
    assert c8 and "RETRACTED_SOURCE" in [f.value for f in c8.primary_verdict.flags], "Case 8 RETRACTED_SOURCE flag missing"
    print("Case 8 (Retracted publication): RETRACTED_SOURCE [PASSED]")

    # Test Exports
    json_out = export_json(report)
    csv_out = export_csv(report)
    html_out = export_standalone_html(report)
    assert len(json_out) > 500
    assert len(csv_out) > 200
    assert len(html_out) > 1000
    print("Exports (JSON, CSV, HTML) generated successfully [PASSED]")
    print("\nPre-warm complete. All 8 planted cases verified!")

if __name__ == "__main__":
    prewarm_demo_cache()
