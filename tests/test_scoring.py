import pytest
from app.core.scoring import compute_evidence_strength_score
from app.schemas import EvidenceTierEnum, ScoreBandEnum, FlagEnum

def test_full_text_perfect_score():
    score, band, breakdown, flags = compute_evidence_strength_score(
        evidence_tier=EvidenceTierEnum.FULL_TEXT,
        retrieval_match_score=100.0,
        quote_verified=True,
        quote_partial=False,
        number_check_result="ok",
        model_certainty="high"
    )
    assert score >= 0.90
    assert band == ScoreBandEnum.HIGH
    assert FlagEnum.NEEDS_HUMAN_REVIEW not in flags

def test_abstract_only_cap():
    score, band, breakdown, flags = compute_evidence_strength_score(
        evidence_tier=EvidenceTierEnum.ABSTRACT_ONLY,
        retrieval_match_score=100.0,
        quote_verified=True,
        quote_partial=False,
        number_check_result="ok",
        model_certainty="high"
    )
    # Score must be capped at 0.60 per Section 4 & DECISIONS.md
    assert score <= 0.60
    assert FlagEnum.ABSTRACT_ONLY in flags

def test_not_found_zero_score():
    score, band, breakdown, flags = compute_evidence_strength_score(
        evidence_tier=EvidenceTierEnum.NOT_FOUND,
        retrieval_match_score=0.0,
        quote_verified=False,
        quote_partial=False,
        number_check_result="no_numbers",
        model_certainty="low"
    )
    assert score == 0.0
    assert band == ScoreBandEnum.LOW
    assert FlagEnum.NEEDS_HUMAN_REVIEW in flags

def test_low_score_triggers_needs_review():
    score, band, breakdown, flags = compute_evidence_strength_score(
        evidence_tier=EvidenceTierEnum.METADATA_ONLY,
        retrieval_match_score=50.0,
        quote_verified=False,
        quote_partial=False,
        number_check_result="missing_fulltext",
        model_certainty="low"
    )
    assert score < 0.50
    assert band == ScoreBandEnum.LOW
    assert FlagEnum.NEEDS_HUMAN_REVIEW in flags
