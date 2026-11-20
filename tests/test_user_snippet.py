from app.pipeline.orchestrator import run_verification_pipeline

def test_user_snippet():
    text = (
        "Artificial intelligence (AI) has increasingly been investigated as a transformative technology for improving diagnostic accuracy, reducing clinical workload, and supporting early disease detection in healthcare. "
        "Studies on mammography suggest that deep-learning systems can achieve diagnostic performance comparable to or exceeding that of radiologists under selected evaluation conditions (McKinney et al., 2020). "
        "However, these findings should not be generalized to all clinical specialties, as diagnostic performance depends on dataset composition, disease prevalence, imaging quality, and clinical setting. "
        "Freeman et al. (2021) reported that AI systems consistently outperformed radiologists across breast cancer screening studies, establishing their readiness for autonomous deployment. "
        "Earlier computer-aided diagnosis research, including Giger (2002), similarly demonstrated that automated image analysis could substantially improve clinical decision-making, supporting the view that AI has long been clinically validated. "
        "Furthermore, high sensitivity and specificity in retrospective datasets indicate that AI-assisted diagnostic systems can reliably reduce unnecessary investigations and prevent missed diagnoses in routine healthcare. "
        "Although concerns regarding algorithmic bias, explainability, and external validation remain, these limitations are primarily technical barriers rather than fundamental obstacles to clinical adoption. "
        "The integration of AI into diagnostic workflows is therefore expected to reduce dependence on specialist interpretation, improve consistency between hospitals, and enable faster clinical decisions. "
        "Recent advances in computational imaging and large-scale training datasets have further strengthened the argument that automated diagnosis can become more dependable than traditional clinical assessment. "
        "Nevertheless, successful implementation requires appropriate evaluation, regulatory oversight, and clinician training. "
        "Overall, the literature indicates that AI has established itself as a reliable replacement for conventional diagnostic methods, with its remaining challenges likely to be resolved through technological refinement and wider deployment."
    )
    report = run_verification_pipeline(text.encode("utf-8"), "user_ai_doc.txt")
    print(f"DOCUMENT: {report.document_name}")
    print(f"CITATION STYLE: {report.citation_style}")
    print(f"TOTAL CLAIMS: {report.total_claims}")
    print(f"SUMMARY COUNTS: {report.summary_counts}")
    print(f"HEALTH INDEX: {report.citation_health_indicator:.1f}%")
    print(f"ITEMS NEEDING REVIEW: {report.items_needing_review_count}")
    print("\n--- EXTRACTED CLAIM CARDS ---")
    for card in report.claim_cards:
        c = card.claim
        v = card.primary_verdict
        print(f"[{c.id}] {v.label} (Strength: {v.evidence_strength_score}) Markers: {c.citation_markers}")
        print(f"     Claim: {c.verbatim_text[:80]}...")
        print(f"     Reason: {v.reason}")
        if v.verified_evidence_quote:
            print(f"     Quote: \"{v.verified_evidence_quote}\"")
        if v.flags:
            print(f"     Flags: {[f.value for f in v.flags]}")
        print()

if __name__ == "__main__":
    test_user_snippet()
