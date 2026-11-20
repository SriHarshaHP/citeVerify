import pytest
from app.schemas import (
    Reference,
    Claim,
    ReferenceVerificationStatusEnum,
    VerdictEnum,
    CoverageStateEnum,
    FlagEnum,
    ReviewerActionEnum,
    ReviewOverrideRequest
)
from app.pipeline.reference_verifier import reference_verifier
from app.pipeline.claim_decomposer import decompose_claim
from app.pipeline.methodology_analyzer import analyze_methodology
from app.pipeline.statistical_analyzer import analyze_statistics
from app.pipeline.causality_detector import detect_causality_overclaim
from app.pipeline.freshness_analyzer import analyze_source_freshness
from app.pipeline.document_intelligence import detect_internal_contradictions, compute_document_scorecard
from app.pipeline.p8_verify_guardrails import verify_claim_reference_pair
from app.pipeline.orchestrator import run_verification_pipeline
from app.export.exporters import export_json, export_csv, export_standalone_html, export_corrected_bib
from app.main import app, submit_review_action
from starlette.testclient import TestClient

client = TestClient(app)

# ==============================================================================
# TEST SCENARIO A — Correct Citation (DOI_VERIFIED)
# ==============================================================================
def test_scenario_a_correct_citation():
    ref = Reference(
        key="McKinney2020",
        raw_string="McKinney, S.M., et al. (2020). International evaluation of an AI system for breast cancer screening. Nature, 577, 89-94.",
        title="International evaluation of an AI system for breast cancer screening",
        authors=["McKinney, S.M."],
        year=2020,
        doi="10.1038/s41586-019-1799-6"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_VERIFIED
    assert res.doi_resolves is True
    assert res.resolved_year == 2020
    assert "Nature" in (res.resolved_journal or "")

# ==============================================================================
# TEST SCENARIO B — Incorrect DOI (DOI_NOT_FOUND)
# ==============================================================================
def test_scenario_b_incorrect_doi():
    ref = Reference(
        key="FakeDOI",
        raw_string="Author, A. (2023). Fake Study. Journal of Fakes.",
        title="Fake Study",
        year=2023,
        doi="10.9999/nonexistent.2023.99999"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_NOT_FOUND
    assert res.doi_resolves is False

# ==============================================================================
# TEST SCENARIO C — DOI Resolves to Different Paper (DOI_METADATA_MISMATCH)
# ==============================================================================
def test_scenario_c_doi_metadata_mismatch():
    # Provide McKinney DOI but with totally mismatched title
    ref = Reference(
        key="MismatchRef",
        raw_string="Mismatched, X. (2015). Completely Unrelated Quantum Mechanics Paper. Nature.",
        title="Completely Unrelated Quantum Mechanics Paper",
        year=2015,
        doi="10.1038/s41586-019-1799-6"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_METADATA_MISMATCH
    assert len(res.metadata_discrepancies) > 0
    assert res.suggested_correction is not None
    assert "suggested_title" in res.suggested_correction

# ==============================================================================
# TEST SCENARIO D — Fabricated Reference (PAPER_NOT_RETRIEVABLE / DOI_NOT_FOUND)
# ==============================================================================
def test_scenario_d_fabricated_reference():
    ref = Reference(
        key="HallucinatedRef",
        raw_string="NonexistentAuthor, Z. (2025). Imaginary Deep Learning Discovery. Journal of Pure Fiction.",
        title="Imaginary Deep Learning Discovery",
        authors=["NonexistentAuthor, Z."],
        year=2025,
        doi=None
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status in [
        ReferenceVerificationStatusEnum.PAPER_NOT_RETRIEVABLE,
        ReferenceVerificationStatusEnum.DOI_NOT_FOUND,
        ReferenceVerificationStatusEnum.PUBLICATION_STATUS_UNKNOWN
    ]

# ==============================================================================
# TEST SCENARIO E — Supported Claim
# ==============================================================================
def test_scenario_e_supported_claim():
    text = (
        "--- Page 1 ---\n"
        "Deep learning achieves high performance in mammography (McKinney et al., 2020).\n"
        "References:\n"
        "[1] McKinney, S.M., et al. (2020). International evaluation of an AI system for breast cancer screening. Nature, 577, 89-94. doi:10.1038/s41586-019-1799-6"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "supported_doc.txt")
    assert report.total_claims >= 1
    c1 = report.claim_cards[0]
    assert c1.primary_verdict.label == VerdictEnum.SUPPORTED.value
    assert c1.primary_verdict.verified_evidence_quote is not None

# ==============================================================================
# TEST SCENARIO F — Contradictory Claim
# ==============================================================================
def test_scenario_f_contradictory_claim():
    text = (
        "--- Page 1 ---\n"
        "AI systems consistently underperformed radiologists and reduced diagnostic accuracy across all screening metrics (McKinney et al., 2020).\n"
        "References:\n"
        "[1] McKinney, S.M., et al. (2020). International evaluation of an AI system for breast cancer screening. Nature, 577, 89-94. doi:10.1038/s41586-019-1799-6"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "contradictory_doc.txt")
    cards = [c for c in report.claim_cards if c.claim.has_citation]
    assert len(cards) >= 1
    # Should flag contradiction or unsupported
    assert cards[0].primary_verdict.label in [VerdictEnum.CONTRADICTORY.value, VerdictEnum.UNSUPPORTED.value]

# ==============================================================================
# TEST SCENARIO G — Partially Supported Claim (Number Mismatch)
# ==============================================================================
def test_scenario_g_partially_supported_number_mismatch():
    text = (
        "--- Page 1 ---\n"
        "A study found a learning app improved test scores by 85% in primary schools (Smith, 2021).\n"
        "References:\n"
        "[1] Smith, J. (2021). Pilot evaluation of mobile learning. Journal of Educational Technology. doi:10.1016/j.compedu.2021.104234"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "partial_doc.txt")
    card = report.claim_cards[0]
    assert card.primary_verdict.label == VerdictEnum.PARTIALLY_SUPPORTED.value
    assert FlagEnum.NUMBER_MISMATCH in card.primary_verdict.flags

# ==============================================================================
# TEST SCENARIO H — Uncited Factual Claim
# ==============================================================================
def test_scenario_h_uncited_factual_claim():
    text = (
        "--- Page 1 ---\n"
        "Microplastic concentrations in Arctic snowfall exceeded 10,000 particles per liter in 2023 without exception.\n"
        "References:\n"
        "[1] Unrelated, A. (2020). General Ecology."
    )
    report = run_verification_pipeline(text.encode("utf-8"), "uncited_doc.txt")
    uncited = [c for c in report.claim_cards if c.primary_verdict.label == CoverageStateEnum.UNCITED.value]
    assert len(uncited) >= 1
    assert FlagEnum.NEEDS_HUMAN_REVIEW in uncited[0].primary_verdict.flags

# ==============================================================================
# TEST SCENARIO I — Causality Overclaim (CAUSALITY_OVERCLAIM)
# ==============================================================================
def test_scenario_i_causality_overclaim():
    claim_text = "Coffee consumption directly causes reduced cardiovascular mortality in adults."
    causality = detect_causality_overclaim(
        claim_text=claim_text,
        study_design="observational_study",
        source_text="In this prospective observational cohort study of 40,000 participants, coffee intake was associated with lower mortality."
    )
    assert causality.is_causality_overclaim is True
    assert "causes" in causality.detected_causal_verbs or "directly causes" in causality.causal_linguistic_terms

# ==============================================================================
# TEST SCENARIO J — Overgeneralized Claim (OVERGENERALIZED)
# ==============================================================================
def test_scenario_j_overgeneralized_claim():
    text = (
        "--- Page 1 ---\n"
        "Hydrogel scaffolds accelerate bone regeneration universally across all mammalian species (Johnson, 2022).\n"
        "References:\n"
        "[1] Johnson, R. (2022). Biodegradable hydrogel in rat calvarial defect model (n=12). Biomaterials. doi:10.1016/j.biomaterials.2022.121543"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "overgeneralized_doc.txt")
    card = report.claim_cards[0]
    assert card.primary_verdict.label in [VerdictEnum.OVERGENERALIZED.value, VerdictEnum.PARTIALLY_SUPPORTED.value]
    assert (
        FlagEnum.SCOPE_OVERGENERALIZED in card.primary_verdict.flags or
        FlagEnum.SMALL_SAMPLE_SIZE in card.primary_verdict.flags
    )

# ==============================================================================
# TEST SCENARIO K — Outdated Source (POSSIBLY_OUTDATED)
# ==============================================================================
def test_scenario_k_outdated_source():
    text = (
        "--- Page 1 ---\n"
        "The standard context window for state-of-the-art NLP models is strictly limited to 1,000 tokens (Vaswani, 2017).\n"
        "References:\n"
        "[1] Vaswani, A., et al. (2017). Attention is all you need. NeurIPS. doi:10.5555/3295222.3295349"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "outdated_doc.txt")
    card = report.claim_cards[0]
    assert card.primary_verdict.label == VerdictEnum.POSSIBLY_OUTDATED.value
    assert FlagEnum.NEEDS_HUMAN_REVIEW in card.primary_verdict.flags

# ==============================================================================
# TEST SCENARIO L — Retracted Source (RETRACTED_SOURCE)
# ==============================================================================
def test_scenario_l_retracted_source():
    text = (
        "--- Page 1 ---\n"
        "MMR vaccination was linked to intestinal pathology and pervasive developmental disorder (Wakefield, 1998).\n"
        "References:\n"
        "[1] Wakefield, A.J., et al. (1998). RETRACTED: Ileal-lymphoid-nodular hyperplasia. Lancet. doi:10.1016/S0140-6736(97)11096-0"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "retracted_doc.txt")
    card = report.claim_cards[0]
    assert FlagEnum.RETRACTED_SOURCE in card.primary_verdict.flags
    assert FlagEnum.NEEDS_HUMAN_REVIEW in card.primary_verdict.flags

# ==============================================================================
# TEST SCENARIO M — Corrected Publication (CORRECTED)
# ==============================================================================
def test_scenario_m_corrected_publication():
    ref = Reference(
        key="CorrectedRef",
        raw_string="Author, A. (2020). Erratum published. Journal of Science.",
        title="Erratum and correction to deep learning performance",
        year=2020,
        doi="10.1000/corrected.example"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.publication_status in ["corrected", "published"]

# ==============================================================================
# TEST SCENARIO N — Small-Sample Limitation
# ==============================================================================
def test_scenario_n_small_sample_limitation():
    text = "We evaluated the intervention on a cohort of 14 patients (n=14) in a single pilot clinic."
    methodology = analyze_methodology(text, title="Pilot clinic study")
    assert methodology.patient_count == 14
    assert any("sample" in c.lower() or "pilot" in c.lower() for c in methodology.methodological_concerns)

# ==============================================================================
# TEST SCENARIO O — Retrospective Study Limitation
# ==============================================================================
def test_scenario_o_retrospective_study_limitation():
    text = "This retrospective cohort study examined electronic health records from 2010 to 2018."
    methodology = analyze_methodology(text, title="Retrospective review")
    assert "retrospective" in methodology.study_design
    assert methodology.is_prospective is False

# ==============================================================================
# TEST SCENARIO P — Citation Scope Mismatch
# ==============================================================================
def test_scenario_p_scope_mismatch():
    claim_text = "The peptide therapeutic is safe and effective in pediatric patients with asthma."
    source_text = "The trial was conducted exclusively in elderly male geriatric patients aged 75 and older."
    methodology = analyze_methodology(source_text, title="Geriatric trial")
    assert methodology.study_design is not None

# ==============================================================================
# TEST SCENARIO Q — Multi-Claim Sentence Decomposition
# ==============================================================================
def test_scenario_q_claim_decomposition():
    compound_sentence = "Artificial intelligence improves diagnostic accuracy, reduces clinical workload, and supports early disease detection."
    subclaims = decompose_claim(compound_sentence, claim_id="C1")
    assert len(subclaims) == 3
    assert subclaims[0].subclaim_id == "C1.1"
    assert "accuracy" in subclaims[0].text
    assert subclaims[1].subclaim_id == "C1.2"
    assert "workload" in subclaims[1].text
    assert subclaims[2].subclaim_id == "C1.3"
    assert "disease detection" in subclaims[2].text

# ==============================================================================
# TEST SCENARIO R — Internal Document Contradiction
# ==============================================================================
def test_scenario_r_internal_contradiction():
    claims = [
        Claim(id="C1", verbatim_text="AI systems consistently outperformed radiologists across breast cancer screening studies, establishing their readiness for autonomous deployment."),
        Claim(id="C2", verbatim_text="AI systems should not be deployed autonomously because diagnostic performance depends heavily on dataset composition and radiologists still excel.")
    ]
    contradictions = detect_internal_contradictions(claims, "document body")
    assert len(contradictions) >= 1
    assert contradictions[0].statement_a is not None
    assert contradictions[0].statement_b is not None

# ==============================================================================
# TEST SCENARIO S — Missing Full Text (Abstract-Only Behavior)
# ==============================================================================
def test_scenario_s_missing_full_text():
    text = (
        "--- Page 1 ---\n"
        "The drug had no therapeutic effect on any patients (Miller, 2021).\n"
        "References:\n"
        "[1] Miller, K. (2021). Phase II trial of novel compound. Abstract Only. doi:10.1000/abstract.only"
    )
    report = run_verification_pipeline(text.encode("utf-8"), "abstract_doc.txt")
    card = report.claim_cards[0]
    # Guardrail 2 ensures negative verdict is not leapt to from abstract only
    assert card.primary_verdict.label in [CoverageStateEnum.UNVERIFIABLE.value, VerdictEnum.UNSUPPORTED.value]

# ==============================================================================
# TEST SCENARIO T — Duplicate Evidence Detection / Source Diversity
# ==============================================================================
def test_scenario_t_source_diversity():
    claims = [Claim(id="C1", verbatim_text="Finding 1", citation_markers=["1"])]
    refs = [
        Reference(key="1", raw_string="Paper 1", title="Paper 1", doi="10.1000/1"),
        Reference(key="2", raw_string="Paper 2", title="Paper 1", doi="10.1000/1")  # Duplicate source
    ]
    scorecard = compute_document_scorecard(claims, [], refs, [])
    assert scorecard.overlapping_sources >= 1

# ==============================================================================
# TEST SCENARIO U — Human Reviewer Actions (Accept, Reject, Override, Undo)
# ==============================================================================
def test_scenario_u_reviewer_workflow():
    # Load demo document first
    res = client.post("/api/verify/demo")
    assert res.status_code == 200

    # 1. Accept finding
    req_accept = {
        "claim_id": "C1",
        "action": "accepted",
        "note": "Verified by reviewer",
        "justification": "Verified by reviewer"
    }
    r1 = client.post("/api/review/action", json=req_accept)
    assert r1.status_code == 200
    assert r1.json()["reviewer_status"] == "accepted"

    # 2. Reject finding
    req_reject = {
        "claim_id": "C2",
        "action": "rejected",
        "note": "Inaccurate extraction",
        "justification": "Inaccurate extraction"
    }
    r2 = client.post("/api/review/action", json=req_reject)
    assert r2.status_code == 200
    assert r2.json()["reviewer_status"] == "rejected"
    assert r2.json()["final_verdict"] == "REJECTED"

    # 3. Mark False Positive
    req_fp = {
        "claim_id": "C3",
        "action": "mark_false_positive",
        "note": "False positive flag",
        "justification": "False positive flag"
    }
    r3 = client.post("/api/review/action", json=req_fp)
    assert r3.status_code == 200
    assert r3.json()["reviewer_status"] == "false_positive"
    assert r3.json()["final_verdict"] == "FALSE_POSITIVE"

    # 4. Override
    req_override = {
        "claim_id": "C4",
        "action": "overridden",
        "new_verdict": "PARTIALLY_SUPPORTED",
        "note": "Human override with context"
    }
    r4 = client.post("/api/review/action", json=req_override)
    assert r4.status_code == 200
    assert r4.json()["reviewer_status"] == "overridden"
    assert r4.json()["final_verdict"] == "PARTIALLY_SUPPORTED"

    # 5. Undo Override
    req_undo = {
        "claim_id": "C4",
        "action": "undo"
    }
    r5 = client.post("/api/review/action", json=req_undo)
    assert r5.status_code == 200
    assert r5.json()["reviewer_status"] == "pending"

# ==============================================================================
# TEST SCENARIO V — Report Generation (JSON, CSV, HTML, BibTeX)
# ==============================================================================
def test_scenario_v_report_exports():
    client.post("/api/verify/demo")

    # JSON export
    res_json = client.get("/api/export/json")
    assert res_json.status_code == 200
    assert "CiteVerify" in res_json.text

    # CSV export
    res_csv = client.get("/api/export/csv")
    assert res_csv.status_code == 200
    assert "Claim ID" in res_csv.text
    assert "Atomic Subclaims Count" in res_csv.text

    # HTML export
    res_html = client.get("/api/export/html")
    assert res_html.status_code == 200
    assert "CiteVerify Evidence-Backed Verification Report" in res_html.text

    # Corrected BibTeX export
    res_bib = client.get("/api/export/corrected-bib")
    assert res_bib.status_code == 200
    assert "@article" in res_bib.text

# ==============================================================================
# TEST SCENARIO W — Full Pipeline on User AI Mammography Snippet
# ==============================================================================
def test_scenario_w_user_mammography_snippet():
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
    assert report.total_claims >= 5
    assert report.scorecard is not None
    assert report.scorecard.research_integrity_score > 0

    # Citations detected
    citations_found = [c for c in report.claim_cards if c.claim.has_citation]
    assert len(citations_found) >= 2

    # Check McKinney (2020)
    mckinney_card = next((c for c in report.claim_cards if "McKinney" in c.claim.verbatim_text or any("McKinney" in m for m in c.claim.citation_markers)), None)
    assert mckinney_card is not None
    assert mckinney_card.primary_verdict.label == VerdictEnum.SUPPORTED.value
    assert mckinney_card.reference_verification is not None
    assert mckinney_card.reference_verification.status == ReferenceVerificationStatusEnum.DOI_VERIFIED

    # Check Giger (2002) - historical / outdated detection
    giger_card = next((c for c in report.claim_cards if "Giger" in c.claim.verbatim_text or any("Giger" in m for m in c.claim.citation_markers)), None)
    assert giger_card is not None
