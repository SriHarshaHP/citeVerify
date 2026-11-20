import os
import pytest
from app.schemas import (
    Claim,
    Reference,
    ClaimTypeEnum,
    VerdictEnum,
    ReferenceVerificationStatusEnum,
    EvidenceTierEnum,
    ClaimCard,
    VerdictResult,
    ScoreBandEnum
)
from app.pipeline.p1_ingest import detect_citation_style
from app.pipeline.p2_extract_claims import extract_citation_markers_from_sentence, extract_claims
from app.pipeline.p3_parse_references import extract_in_text_references, parse_references
from app.pipeline.p4_map_markers import parse_numeric_marker_keys, map_claims_to_references
from app.pipeline.claim_decomposer import decompose_compound_sentence, decompose_claim, classify_subclaim_category
from app.pipeline.reference_verifier import reference_verifier
from app.pipeline.p5_retrieve import scholarly_retriever
from app.pipeline.methodology_analyzer import analyze_methodology
from app.pipeline.p8_verify_guardrails import verify_claim_reference_pair
from app.pipeline.document_intelligence import compute_document_scorecard
from app.pipeline.orchestrator import run_verification_pipeline


def test_1_mixed_citation_style_detection():
    text = "AI showed promise [1, 2], but Freeman et al. (2021) identified limitations [3]."
    style = detect_citation_style(text)
    assert style == "mixed"


def test_2_narrative_author_year_extraction():
    text = "In contrast, Freeman et al. (2021) reported findings, and Giger, Karssemeijer and Armato (2001) agreed."
    markers = extract_citation_markers_from_sentence(text)
    assert any("Freeman" in m and "2021" in m for m in markers)
    assert any("Karssemeijer" in m or "Giger" in m for m in markers)


def test_3_multi_author_parenthetical_extraction():
    text = "Controlled evaluation conditions (Esteva et al., 2017; McKinney et al., 2020) showed high accuracy."
    markers = extract_citation_markers_from_sentence(text)
    assert any("Esteva" in m and "2017" in m for m in markers)
    assert any("McKinney" in m and "2020" in m for m in markers)


def test_4_composite_numeric_parsing():
    keys = parse_numeric_marker_keys("[1, 2]")
    assert keys == ["1", "2"]
    keys_multi = parse_numeric_marker_keys("[1-3, 5]")
    assert "1" in keys_multi and "2" in keys_multi and "3" in keys_multi and "5" in keys_multi


def test_5_secondary_citation_parsing():
    text = "A previous review by Smith (1998, as cited in Brown, 2024) also established this."
    markers = extract_citation_markers_from_sentence(text)
    assert any("Brown" in m or "Smith" in m for m in markers)
    refs = extract_in_text_references(text)
    keys = [r.key for r in refs]
    assert any("Brown" in k for k in keys) or any("Smith" in k for k in keys)


def test_6_numeric_to_reference_resolution():
    claims = [
        Claim(id="C11", verbatim_text="Similar findings reported [1, 2].", citation_markers=["[1, 2]"]),
        Claim(id="C34", verbatim_text="Monitoring is important [3].", citation_markers=["[3]"])
    ]
    references = [
        Reference(key="Esteva2017", raw_string="Esteva et al. (2017)", title="Skin cancer deep CNN", authors=["A. Esteva"], year=2017),
        Reference(key="McKinney2020", raw_string="McKinney et al. (2020)", title="Breast cancer screening", authors=["S. M. McKinney"], year=2020),
        Reference(key="Freeman2021", raw_string="Freeman et al. (2021)", title="Systematic review of AI in screening", authors=["K. Freeman"], year=2021),
    ]
    pairs, orphans, unmatched = map_claims_to_references(claims, references)
    c11_pairs = [p for p in pairs if p.claim_id == "C11"]
    c34_pairs = [p for p in pairs if p.claim_id == "C34"]

    assert len(c11_pairs) == 2
    c11_ref_keys = [p.reference_key for p in c11_pairs]
    assert "Esteva2017" in c11_ref_keys
    assert "McKinney2020" in c11_ref_keys

    assert len(c34_pairs) == 1
    assert c34_pairs[0].reference_key == "Freeman2021"


def test_7_verification_esteva_doi():
    ref = Reference(
        key="Esteva2017",
        raw_string="Esteva et al. (2017). Dermatologist-level classification of skin cancer. Nature.",
        title="Dermatologist-level classification of skin cancer with deep neural networks",
        authors=["A. Esteva"],
        year=2017,
        doi="10.1038/nature21056"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_VERIFIED
    assert "10.1038/nature21056" in (res.doi or "")


def test_8_verification_giger_doi_editorial():
    ref = Reference(
        key="Giger2001",
        raw_string="Giger, Karssemeijer and Armato (2001). Guest editorial computer-aided diagnosis. IEEE TMI.",
        title="Guest editorial computer-aided diagnosis in medical imaging",
        authors=["M. L. Giger", "N. Karssemeijer"],
        year=2001,
        doi="10.1109/TMI.2001.974915"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_VERIFIED
    assert res.publication_type == "editorial"


def test_9_verification_zech_doi():
    ref = Reference(
        key="Zech2018",
        raw_string="Zech et al. (2018). Variable generalization performance of a deep learning model. PLOS Med.",
        title="Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs: A cross-sectional study",
        authors=["J. R. Zech"],
        year=2018,
        doi="10.1371/journal.pmed.1002683"
    )
    res = reference_verifier.verify_reference(ref)
    assert res.status == ReferenceVerificationStatusEnum.DOI_VERIFIED
    assert "10.1371/journal.pmed.1002683" in (res.doi or "")


def test_10_freeman_verdict_supported():
    claim = Claim(
        id="C8",
        verbatim_text="In contrast, Freeman et al. (2021) conducted a systematic review of AI-based breast cancer screening studies and concluded that the available evidence was insufficient to establish the accuracy of AI in routine screening programmes.",
        citation_markers=["Freeman et al. (2021)"]
    )
    ref = Reference(
        key="Freeman2021",
        raw_string="Freeman et al. (2021). BMJ.",
        title="Use of artificial intelligence for image analysis in breast cancer screening programmes: systematic review of test accuracy",
        authors=["K. Freeman"],
        year=2021,
        doi="10.1136/bmj.n1872"
    )
    source = scholarly_retriever.retrieve_source(ref)
    verdict = verify_claim_reference_pair(claim, ref, source)
    assert verdict.label in [VerdictEnum.SUPPORTED.value, VerdictEnum.PARTIALLY_SUPPORTED.value]
    assert verdict.label != VerdictEnum.CONTRADICTORY.value


def test_11_freeman_sample_size_extraction():
    freeman_text = (
        "We conducted a systematic review evaluating 12 studies involving 131,822 screened women on the test accuracy "
        "of AI systems in breast cancer screening programmes."
    )
    info = analyze_methodology(freeman_text, title="Systematic review of test accuracy")
    assert info.patient_count == 131822
    assert "131,822" in info.sample_size
    assert "12 included studies" in info.sample_size


def test_12_freeman_study_design_systematic_review():
    freeman_text = (
        "We conducted a systematic review evaluating 12 studies involving 131,822 screened women on the test accuracy "
        "of AI systems in breast cancer screening programmes."
    )
    info = analyze_methodology(freeman_text, title="Use of artificial intelligence for image analysis in breast cancer screening programmes: systematic review of test accuracy")
    assert info.study_design == "systematic_review"
    assert info.study_design != "meta_analysis"


def test_13_atomic_claim_decomposition_no_citation_split():
    c33_text = "Prior multicentre evaluations reported a drop of up to 15% in external performance (Zech et al., 2018; External Validation Review Group, 2022)."
    parts = decompose_compound_sentence(c33_text)
    assert len(parts) == 1
    assert "External Validation Review Group, 2022)." not in [p.strip() for p in parts if p != parts[0]]


def test_14_hypothetical_claim_no_uncited_penalty():
    hypo_text = "For example, a hypothetical model evaluated on 1,000 patients may achieve 95% accuracy simply by predicting majority class."
    is_factual, cat = classify_subclaim_category(hypo_text)
    assert cat == ClaimTypeEnum.HYPOTHETICAL
    assert not is_factual


def test_15_recommendation_claim_no_uncited_penalty():
    rec_text = "Future investigations should prioritize representative datasets, independent external validation, and prospective evaluation."
    is_factual, cat = classify_subclaim_category(rec_text)
    assert cat == ClaimTypeEnum.RECOMMENDATION
    assert not is_factual


def test_16_transparent_integrity_scorecard():
    claims = [
        Claim(id="C1", verbatim_text="AI improves diagnosis.", type=ClaimTypeEnum.FINDING, has_citation=True, citation_markers=["[1]"]),
        Claim(id="C2", verbatim_text="For example, a hypothetical model on 1000 patients...", type=ClaimTypeEnum.HYPOTHETICAL, has_citation=False, citation_markers=[]),
        Claim(id="C3", verbatim_text="Future investigations should prioritize validation.", type=ClaimTypeEnum.RECOMMENDATION, has_citation=False, citation_markers=[])
    ]
    ref = Reference(key="1", raw_string="Ref 1", title="Test Paper", authors=["Author"], year=2020)
    card = ClaimCard(
        claim=claims[0],
        pairs=[],
        primary_verdict=VerdictResult(
            label="SUPPORTED",
            reason="Supported by reference.",
            evidence_strength_score=0.9,
            score_band=ScoreBandEnum.HIGH,
            evidence_tier=EvidenceTierEnum.FULL_TEXT
        )
    )
    scorecard = compute_document_scorecard(claims, [card], [ref], [])
    b = scorecard.integrity_score_breakdown
    assert "base_score" in b
    assert "support_quality" in b
    assert "citation_coverage" in b
    assert "contradiction_penalty" in b
    assert "unsupported_penalty" in b
    assert "unverifiable_treatment" in b
    assert "retraction_penalty" in b
    assert "internal_conflict_penalty" in b
    assert "final_score" in b
    assert scorecard.research_integrity_score > 0.0


def test_17_full_pipeline_stress_test_doc():
    doc_path = "tests/reconstructed_stress_test_doc.txt"
    if not os.path.exists(doc_path):
        pytest.skip("Reconstructed stress test doc not found.")
    
    with open(doc_path, "r", encoding="utf-8") as f:
        text = f.read()

    report = run_verification_pipeline(text, "stress_test_reconstructed.txt")
    assert report is not None
    assert len(report.claims) > 10
    assert len(report.references) >= 3
    assert report.scorecard.research_integrity_score > 0.0


def test_18_no_false_metadata_unavailable():
    keys_to_test = [
        Reference(key="Esteva2017", raw_string="Esteva et al. (2017)", title="Dermatologist-level classification", authors=["A. Esteva"], year=2017, doi="10.1038/nature21056"),
        Reference(key="McKinney2020", raw_string="McKinney et al. (2020)", title="International evaluation of AI in mammography", authors=["S. M. McKinney"], year=2020, doi="10.1038/s41586-019-1799-6"),
        Reference(key="Freeman2021", raw_string="Freeman et al. (2021)", title="Use of artificial intelligence for image analysis", authors=["K. Freeman"], year=2021, doi="10.1136/bmj.n1872"),
        Reference(key="Giger2001", raw_string="Giger et al. (2001)", title="Guest editorial computer-aided diagnosis", authors=["M. L. Giger"], year=2001, doi="10.1109/TMI.2001.974915"),
        Reference(key="Zech2018", raw_string="Zech et al. (2018)", title="Variable generalization performance", authors=["J. R. Zech"], year=2018, doi="10.1371/journal.pmed.1002683")
    ]
    for r in keys_to_test:
        res = reference_verifier.verify_reference(r)
        assert res.status != ReferenceVerificationStatusEnum.METADATA_UNAVAILABLE
        assert res.status in [ReferenceVerificationStatusEnum.DOI_VERIFIED, ReferenceVerificationStatusEnum.PAPER_VERIFIED]
