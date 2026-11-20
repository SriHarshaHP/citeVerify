from typing import Dict, Any, Tuple

EVIDENCE_HIERARCHY_LEVELS = {
    "systematic_review_and_meta_analysis": {"level": "Level 1 (Highest)", "rank": 5, "desc": "Systematic synthesis of multi-trial evidence"},
    "randomized_controlled_trial": {"level": "Level 2 (High)", "rank": 4, "desc": "Interventional trial with prospective randomization"},
    "prospective_cohort": {"level": "Level 3 (Moderate)", "rank": 3, "desc": "Prospective longitudinal tracking of cohorts"},
    "retrospective_cohort": {"level": "Level 4 (Lower)", "rank": 2, "desc": "Retrospective historical dataset evaluation"},
    "in_vitro_or_animal_model": {"level": "Level 4 (Preclinical)", "rank": 2, "desc": "Preclinical laboratory or animal model"},
    "observational_study": {"level": "Level 4 (Observational)", "rank": 2, "desc": "Uncontrolled observational or cross-sectional data"},
    "computational_simulation": {"level": "Level 4 (Computational)", "rank": 2, "desc": "Algorithmic simulation and benchmark evaluation"},
    "preprint": {"level": "Unreviewed (Preprint)", "rank": 1, "desc": "Preprint publication without formal peer-review certification"}
}

def evaluate_evidence_hierarchy(
    study_design: str,
    is_peer_reviewed: bool = True,
    has_external_validation: bool = False
) -> Dict[str, Any]:
    """
    Assesses source credibility and methodological evidence tier (Feature 10).
    Evaluated independently from claim support status.
    """
    base = EVIDENCE_HIERARCHY_LEVELS.get(
        study_design,
        {"level": "Level 4 (Observational)", "rank": 2, "desc": "Standard research publication"}
    )

    rank = base["rank"]
    level_str = base["level"]
    rationale = base["desc"]

    if not is_peer_reviewed:
        level_str = "Preprint / Non-Peer-Reviewed"
        rationale += " (Caution: Evidence has not undergone formal academic peer review)."
    elif has_external_validation and rank < 5:
        level_str += " + External Validation"
        rationale += "; strengthens generalizability through multi-site validation."

    return {
        "study_type": study_design,
        "evidence_hierarchy_level": level_str,
        "hierarchy_rank": rank,
        "credibility_rationale": rationale,
        "is_peer_reviewed": is_peer_reviewed
    }
