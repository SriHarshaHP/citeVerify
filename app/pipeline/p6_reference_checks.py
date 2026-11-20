from typing import List
from app.schemas import (
    Reference,
    SourcePackage,
    FlagEnum,
    EvidenceTierEnum
)
from app.config import settings

def perform_reference_checks(
    reference: Reference,
    source_package: SourcePackage
) -> List[FlagEnum]:
    """
    Detects misleading references, metadata mismatches, retractions,
    and retrieval discrepancies.
    """
    flags: List[FlagEnum] = []

    # 1. Retraction Check
    if source_package.retraction_flag:
        flags.append(FlagEnum.RETRACTED_SOURCE)
        flags.append(FlagEnum.NEEDS_HUMAN_REVIEW)

    # 2. Reference Not Found / Low match
    if source_package.evidence_tier == EvidenceTierEnum.NOT_FOUND:
        flags.append(FlagEnum.NEEDS_HUMAN_REVIEW)
        return flags

    if source_package.title_match_score < settings.TITLE_SIMILARITY_THRESHOLD:
        flags.append(FlagEnum.LOW_RETRIEVAL_MATCH)

    # 3. Metadata Mismatch Check
    meta = source_package.metadata or {}
    registry_year = meta.get("publication_year") or meta.get("year")
    if reference.year and registry_year:
        if abs(reference.year - registry_year) >= 2:
            flags.append(FlagEnum.METADATA_MISMATCH)

    registry_authors = meta.get("authors") or []
    if reference.authors and registry_authors:
        # Check if any author surname matches
        ref_surnames = [a.split()[-1].lower() for a in reference.authors if a.strip()]
        reg_surnames = [str(a).split()[-1].lower() for a in registry_authors if str(a).strip()]
        
        has_overlap = any(s in reg_surnames for s in ref_surnames)
        if not has_overlap and len(ref_surnames) > 0 and len(reg_surnames) > 0:
            flags.append(FlagEnum.METADATA_MISMATCH)

    # 4. Tier Flags
    if source_package.evidence_tier == EvidenceTierEnum.ABSTRACT_ONLY:
        flags.append(FlagEnum.ABSTRACT_ONLY)
    elif source_package.evidence_tier == EvidenceTierEnum.METADATA_ONLY:
        flags.append(FlagEnum.METADATA_ONLY)

    return list(dict.fromkeys(flags))
