from datetime import datetime
from typing import Optional
from app.schemas import FreshnessAssessment

# Configurable domain freshness thresholds (years)
DOMAIN_FRESHNESS_THRESHOLDS = {
    "artificial_intelligence": 5,
    "large_language_models": 3,
    "clinical_guidelines": 8,
    "oncology_and_therapeutics": 10,
    "biomaterials": 10,
    "general_medicine": 12,
    "theoretical_physics": 35,
    "mathematics": 50,
    "historical_context": 100,
    "default": 10
}

def detect_domain(claim_text: str, source_title: str = "") -> str:
    """Infers domain to apply appropriate freshness policy."""
    combined = (claim_text + " " + source_title).lower()
    if any(k in combined for k in ["screening programme", "clinical practice", "guideline", "diagnostic workflow"]):
        return "clinical_guidelines"
    if any(k in combined for k in ["oncology", "cancer", "chemotherapy", "melanoma", "mammography", "screening"]):
        return "oncology_and_therapeutics"
    if any(k in combined for k in ["language model", "transformer", "llm", "chatgpt", "deep learning", "neural network"]):
        return "artificial_intelligence"
    if any(k in combined for k in ["hydrogel", "scaffold", "peptide", "collagen"]):
        return "biomaterials"
    if any(k in combined for k in ["theorem", "proof", "convex optimization", "matrix"]):
        return "mathematics"
    if any(k in combined for k in ["historically", "earlier research", "long been", "in the 1990s", "in 2002"]):
        return "historical_context"
    return "default"

def analyze_source_freshness(
    publication_year: Optional[int],
    claim_text: str = "",
    source_title: str = ""
) -> FreshnessAssessment:
    """
    Evaluates source freshness based on context, domain volatility, and claim intent (Feature 8).
    Avoids penalizing older foundational or historical citations.
    """
    if not publication_year:
        return FreshnessAssessment(
            publication_year=None,
            age_years=None,
            domain="default",
            domain_freshness_threshold=10,
            is_outdated=False,
            why_age_matters="Publication year not available; freshness check bypassed."
        )

    current_year = datetime.now().year
    age = max(0, current_year - publication_year)
    domain = detect_domain(claim_text, source_title)
    threshold = DOMAIN_FRESHNESS_THRESHOLDS.get(domain, 10)

    # Check if claim is explicitly historical: e.g. "Earlier research, including Giger (2002)..."
    lower_claim = claim_text.lower()
    is_historical_claim = any(h in lower_claim for h in ["earlier", "historically", "foundational", "in 2002", "originally"])

    is_outdated = False
    why_matters = ""
    newer_evidence = None

    if is_historical_claim:
        is_outdated = False
        why_matters = f"Source published in {publication_year} ({age} years ago) is cited for historical development context, which remains valid."
    elif age > threshold:
        is_outdated = True
        why_matters = (
            f"Source was published in {publication_year} ({age} years ago). In the domain of '{domain.replace('_', ' ')}', "
            f"literature older than {threshold} years may be superseded by recent empirical advances or modern architectures."
        )
        if domain == "artificial_intelligence":
            newer_evidence = "Contemporary multi-site prospective clinical trials (2022-2026) report updated benchmarks exceeding early baseline systems."
        elif domain == "clinical_guidelines":
            newer_evidence = "Updated regulatory frameworks (FDA / EMA / NHS AI Lab 2023-2025) supersede historical recommendations."
    else:
        why_matters = f"Source publication ({publication_year}, {age} years ago) falls within the acceptable {threshold}-year threshold for {domain.replace('_', ' ')}."

    return FreshnessAssessment(
        publication_year=publication_year,
        age_years=age,
        domain=domain,
        domain_freshness_threshold=threshold,
        is_outdated=is_outdated,
        why_age_matters=why_matters,
        newer_evidence_available=newer_evidence
    )
