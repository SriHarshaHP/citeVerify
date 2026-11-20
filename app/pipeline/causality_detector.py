import re
from typing import List, Tuple
from app.schemas import CausalityAssessment

CAUSAL_PATTERNS = [
    r'\bcauses\b', r'\bcaused\b', r'\bleads to\b', r'\bled to\b',
    r'\bresults in\b', r'\bresulted in\b', r'\bproduces\b', r'\bproduced\b',
    r'\bprevents\b', r'\bprevented\b', r'\beliminates\b', r'\beliminated\b',
    r'\beradicates\b', r'\btriggers\b', r'\btriggered\b'
]

CORRELATIONAL_TERMS = [
    "associated with", "correlated with", "correlation", "observational",
    "linked to", "relationship between", "co-occur", "trend toward", "survey"
]

NON_CAUSAL_STUDY_DESIGNS = [
    "observational_study", "cross_sectional_study", "retrospective_cohort",
    "computational_simulation", "survey"
]

def detect_causality_overclaim(
    claim_text: str,
    study_design: str,
    source_text: str = ""
) -> CausalityAssessment:
    """
    Detects whether an observational correlation is improperly asserted
    as direct causation in the document claim (Feature 7).
    """
    lower_claim = claim_text.lower()
    lower_source = source_text.lower()

    # 1. Detect causal linguistic terms in claim
    matched_terms: List[str] = []
    for pattern in CAUSAL_PATTERNS:
        found = re.findall(pattern, lower_claim)
        if found:
            matched_terms.extend(found)

    causal_detected = len(matched_terms) > 0

    # 2. Check if study design supports causation
    study_supports_causation = True
    if any(ncd in study_design.lower() for ncd in NON_CAUSAL_STUDY_DESIGNS):
        study_supports_causation = False
    elif any(corr in lower_source for corr in CORRELATIONAL_TERMS) and "randomized" not in lower_source:
        study_supports_causation = False

    # 3. Detect Overclaim: Causal statement in claim, but observational/correlational design in source
    is_overclaim = False
    explanation = None

    if causal_detected and not study_supports_causation:
        is_overclaim = True
        matched_str = ", ".join(list(dict.fromkeys(matched_terms)))
        explanation = (
            f"The document asserts a direct causal relationship using terms ('{matched_str}'), "
            f"whereas the cited research utilizes an observational/retrospective design ({study_design.replace('_', ' ')}) "
            "which establishes association or correlation, not definitive causation."
        )

    return CausalityAssessment(
        causal_claim_detected=causal_detected,
        causal_linguistic_terms=list(dict.fromkeys(matched_terms)),
        study_design_supports_causation=study_supports_causation,
        is_causality_overclaim=is_overclaim,
        explanation=explanation
    )
