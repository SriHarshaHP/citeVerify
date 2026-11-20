import pytest
from app.schemas import (
    Claim,
    Reference,
    SourcePackage,
    EvidenceTierEnum,
    ClaimTypeEnum,
    FlagEnum,
    VerdictEnum,
    CoverageStateEnum,
    TextChunk
)
from app.pipeline.p8_verify_guardrails import verify_claim_reference_pair

def test_guardrail_uncited_claim():
    claim = Claim(
        id="C_uncited",
        verbatim_text="General neural architectures require less supervision.",
        type=ClaimTypeEnum.GENERAL,
        page=1,
        section="Intro",
        citation_markers=[],
        has_citation=False
    )
    result = verify_claim_reference_pair(claim, None, None)
    assert result.label == CoverageStateEnum.UNCITED.value
    assert result.evidence_strength_score == 0.0
    assert FlagEnum.NEEDS_HUMAN_REVIEW in result.flags

def test_guardrail_unverifiable_missing_reference():
    claim = Claim(
        id="C_unfound",
        verbatim_text="Synthetic oncolytic virus OX-40 cured 100% of cases.",
        type=ClaimTypeEnum.FINDING,
        page=1,
        section="Results",
        citation_markers=["[5]"],
        has_citation=True
    )
    ref = Reference(key="5", raw_string="[5] Nonexistent (2025)", title="Nonexistent")
    pkg = SourcePackage(reference_key="5", evidence_tier=EvidenceTierEnum.NOT_FOUND)
    
    result = verify_claim_reference_pair(claim, ref, pkg)
    assert result.label == CoverageStateEnum.UNVERIFIABLE.value
    assert result.unverifiable_reason.value == "reference_not_found"
    assert result.evidence_strength_score == 0.0
    assert FlagEnum.NEEDS_HUMAN_REVIEW in result.flags

def test_guardrail_retracted_source_forces_review():
    claim = Claim(
        id="C_retract",
        verbatim_text="Hydrogel micro-scaffolds loaded with peptide conjugates stimulate bone matrix regeneration within three weeks of implantation.",
        type=ClaimTypeEnum.FINDING,
        page=2,
        citation_markers=["[7]"]
    )
    ref = Reference(key="7", raw_string="[7] Vane et al. (2018)", title="Accelerated osteogenesis")
    text = "Histological evaluation demonstrated robust bone matrix deposition and mineralized osteoid formation within three weeks post-implantation."
    pkg = SourcePackage(
        reference_key="7",
        title_match_score=95.0,
        text_chunks=[TextChunk(chunk_id="c0", page=1, text=text)],
        full_text=text,
        evidence_tier=EvidenceTierEnum.FULL_TEXT,
        retraction_flag=True,
        retraction_details="Paper retracted due to figure duplication."
    )
    result = verify_claim_reference_pair(claim, ref, pkg)
    assert FlagEnum.RETRACTED_SOURCE in result.flags
    assert FlagEnum.NEEDS_HUMAN_REVIEW in result.flags

def test_guardrail_number_mismatch_caps_at_partially_supported():
    claim = Claim(
        id="C_mismatch",
        verbatim_text="The implementation of interactive coding feedback increased final exam passing rates by 45% across all engineering cohorts.",
        type=ClaimTypeEnum.STATISTIC,
        page=1,
        citation_markers=["[2]"]
    )
    ref = Reference(key="2", raw_string="[2] Smith (2021)", title="Feedback in CS")
    text = "Students receiving real-time automated feedback demonstrated an 18% increase in final exam passing rates compared to the control cohort."
    pkg = SourcePackage(
        reference_key="2",
        title_match_score=98.0,
        text_chunks=[TextChunk(chunk_id="c0", page=1, text=text)],
        full_text=text,
        evidence_tier=EvidenceTierEnum.FULL_TEXT,
        retraction_flag=False
    )
    result = verify_claim_reference_pair(claim, ref, pkg)
    assert result.label == VerdictEnum.PARTIALLY_SUPPORTED.value
    assert FlagEnum.NUMBER_MISMATCH in result.flags
