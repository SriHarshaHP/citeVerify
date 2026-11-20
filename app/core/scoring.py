from typing import List, Tuple, Optional
from app.config import settings
from app.schemas import (
    EvidenceTierEnum,
    ScoreBandEnum,
    ScoreBreakdown,
    FlagEnum
)

def compute_evidence_strength_score(
    evidence_tier: EvidenceTierEnum,
    retrieval_match_score: float,  # 0 to 100
    quote_verified: bool,
    quote_partial: bool,
    number_check_result: str,  # "ok", "no_numbers", "missing_abstract", "missing_fulltext", "mismatch"
    model_certainty: str,      # "high", "medium", "low"
    is_retracted: bool = False,
    is_uncited: bool = False
) -> Tuple[float, ScoreBandEnum, ScoreBreakdown, List[FlagEnum]]:
    """
    Computes deterministic evidence strength score between 0.0 and 1.0.
    Returns (score, band, breakdown, additional_flags).
    """
    flags: List[FlagEnum] = []

    if is_retracted:
        flags.append(FlagEnum.RETRACTED_SOURCE)
        flags.append(FlagEnum.NEEDS_HUMAN_REVIEW)

    if is_uncited:
        # Uncited claims have 0 evidence score
        breakdown = ScoreBreakdown(
            tier_score=0.0,
            retrieval_score=0.0,
            quote_score=0.0,
            number_score=0.0,
            model_certainty_score=0.0,
            cap_applied=None,
            summary="Claim has no citation marker in the source text."
        )
        return 0.0, ScoreBandEnum.LOW, breakdown, [FlagEnum.NEEDS_HUMAN_REVIEW]

    # 1. Evidence Tier Sub-score (weight = 0.35)
    w_tier = 0.35
    if evidence_tier == EvidenceTierEnum.FULL_TEXT:
        s_tier = 1.0
    elif evidence_tier == EvidenceTierEnum.ABSTRACT_ONLY:
        s_tier = 0.5
        flags.append(FlagEnum.ABSTRACT_ONLY)
    elif evidence_tier == EvidenceTierEnum.METADATA_ONLY:
        s_tier = 0.2
        flags.append(FlagEnum.METADATA_ONLY)
    else:  # NOT_FOUND
        s_tier = 0.0

    # 2. Retrieval Match Sub-score (weight = 0.20)
    w_retrieval = 0.20
    s_retrieval = max(0.0, min(1.0, retrieval_match_score / 100.0))
    if s_retrieval < (settings.TITLE_SIMILARITY_THRESHOLD / 100.0) and evidence_tier != EvidenceTierEnum.NOT_FOUND:
        flags.append(FlagEnum.LOW_RETRIEVAL_MATCH)

    # 3. Quote Verification Sub-score (weight = 0.25)
    w_quote = 0.25
    if quote_verified:
        s_quote = 1.0
    elif quote_partial:
        s_quote = 0.5
    else:
        s_quote = 0.0

    # 4. Number Agreement Sub-score (weight = 0.15)
    w_numbers = 0.15
    if number_check_result in ("ok", "no_numbers"):
        s_numbers = 1.0
    elif number_check_result == "missing_abstract":
        s_numbers = 0.7
        flags.append(FlagEnum.NUMBER_NOT_FOUND)
    elif number_check_result == "missing_fulltext":
        s_numbers = 0.3
        flags.append(FlagEnum.NUMBER_NOT_FOUND)
    elif number_check_result == "mismatch":
        s_numbers = 0.0
        flags.append(FlagEnum.NUMBER_MISMATCH)
    else:
        s_numbers = 0.5

    # 5. Model Certainty Sub-score (weight = 0.05)
    w_model = 0.05
    c_lower = (model_certainty or "").lower()
    if c_lower == "high":
        s_model = 1.0
    elif c_lower == "medium":
        s_model = 0.6
    else:
        s_model = 0.2

    # Weighted calculation
    raw_score = (
        (w_tier * s_tier) +
        (w_retrieval * s_retrieval) +
        (w_quote * s_quote) +
        (w_numbers * s_numbers) +
        (w_model * s_model)
    )

    # Cap logic
    cap_applied = None
    final_score = raw_score
    if evidence_tier == EvidenceTierEnum.ABSTRACT_ONLY:
        if final_score > settings.ABSTRACT_SCORE_CAP:
            final_score = settings.ABSTRACT_SCORE_CAP
            cap_applied = f"Capped at {settings.ABSTRACT_SCORE_CAP} due to abstract-only evidence tier."
    elif evidence_tier == EvidenceTierEnum.METADATA_ONLY:
        if final_score > settings.METADATA_SCORE_CAP:
            final_score = settings.METADATA_SCORE_CAP
            cap_applied = f"Capped at {settings.METADATA_SCORE_CAP} due to metadata-only evidence tier."
    elif evidence_tier == EvidenceTierEnum.NOT_FOUND:
        final_score = 0.0
        cap_applied = "Zeroed because source reference could not be found."

    final_score = round(max(0.0, min(1.0, final_score)), 2)

    # Determine band
    if final_score >= 0.75:
        band = ScoreBandEnum.HIGH
    elif final_score >= 0.50:
        band = ScoreBandEnum.MEDIUM
    else:
        band = ScoreBandEnum.LOW
        if FlagEnum.NEEDS_HUMAN_REVIEW not in flags:
            flags.append(FlagEnum.NEEDS_HUMAN_REVIEW)

    # Build concise summary breakdown
    components = [
        f"Tier ({evidence_tier.value}): {int(s_tier * 100)}%",
        f"Retrieval: {int(s_retrieval * 100)}%",
        f"Quote: {'Verified' if quote_verified else ('Partial' if quote_partial else 'Failed')}",
        f"Numbers: {number_check_result}"
    ]
    summary_text = " • ".join(components)
    if cap_applied:
        summary_text += f" [{cap_applied}]"

    breakdown = ScoreBreakdown(
        tier_score=round(s_tier, 2),
        retrieval_score=round(s_retrieval, 2),
        quote_score=round(s_quote, 2),
        number_score=round(s_numbers, 2),
        model_certainty_score=round(s_model, 2),
        cap_applied=cap_applied,
        summary=summary_text
    )

    return final_score, band, breakdown, list(dict.fromkeys(flags))
