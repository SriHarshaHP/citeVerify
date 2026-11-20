from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from app.config import settings
from app.schemas import (
    Claim,
    Reference,
    ClaimSourcePair,
    ClaimCard,
    VerdictResult,
    VerdictEnum,
    CoverageStateEnum,
    FlagEnum,
    EvidenceTierEnum,
    VerificationReport,
    ReviewerActorEnum,
    ReviewerActionEnum
)
from app.pipeline.p1_ingest import ingest_document
from app.pipeline.p2_extract_claims import extract_claims
from app.pipeline.p3_parse_references import parse_references
from app.pipeline.p4_map_markers import map_claims_to_references
from app.pipeline.p5_retrieve import retriever
from app.pipeline.p8_verify_guardrails import verify_claim_reference_pair
from app.core.audit import audit_manager
from app.pipeline.claim_decomposer import decompose_claim
from app.pipeline.reference_verifier import reference_verifier
from app.pipeline.methodology_analyzer import analyze_methodology
from app.pipeline.statistical_analyzer import analyze_statistics
from app.pipeline.freshness_analyzer import analyze_source_freshness
from app.pipeline.document_intelligence import detect_internal_contradictions, compute_document_scorecard

VERDICT_HIERARCHY = {
    VerdictEnum.SUPPORTED.value: 6,
    VerdictEnum.PARTIALLY_SUPPORTED.value: 5,
    VerdictEnum.POSSIBLY_OUTDATED.value: 4,
    CoverageStateEnum.UNVERIFIABLE.value: 3,
    CoverageStateEnum.AMBIGUOUS_CITATION.value: 2,
    VerdictEnum.UNSUPPORTED.value: 1,
    VerdictEnum.CONTRADICTORY.value: 0
}

RISK_SORT_ORDER = {
    VerdictEnum.CONTRADICTORY.value: 0,
    VerdictEnum.UNSUPPORTED.value: 1,
    VerdictEnum.POSSIBLY_OUTDATED.value: 2,
    CoverageStateEnum.AMBIGUOUS_CITATION.value: 3,
    CoverageStateEnum.UNVERIFIABLE.value: 4,
    VerdictEnum.PARTIALLY_SUPPORTED.value: 5,
    CoverageStateEnum.UNCITED.value: 6,
    VerdictEnum.SUPPORTED.value: 7
}

def roll_up_verdicts(pairs: List[ClaimSourcePair]) -> Tuple[VerdictResult, Optional[str]]:
    """
    Rolls up multiple claim-reference pairs to the primary verdict
    (Guardrail 8: strongest support, noting split support).
    """
    if not pairs:
        raise ValueError("Cannot roll up empty pairs")
    
    if len(pairs) == 1:
        return pairs[0].verdict, None

    # Sort pairs by support strength
    sorted_pairs = sorted(
        pairs,
        key=lambda p: (
            VERDICT_HIERARCHY.get(p.verdict.label, 0) if p.verdict else 0,
            p.verdict.evidence_strength_score if p.verdict else 0.0
        ),
        reverse=True
    )

    primary = sorted_pairs[0].verdict
    labels = {p.verdict.label for p in pairs if p.verdict}
    
    roll_up_note = None
    if len(labels) > 1:
        verdict_list = ", ".join([f"[{p.reference_key or 'Ref'}]: {p.verdict.label}" for p in pairs if p.verdict])
        roll_up_note = f"Split support across {len(pairs)} citations ({verdict_list}). Displaying strongest evidence."

    return primary, roll_up_note

def run_verification_pipeline(
    file_bytes: bytes,
    filename: str,
    progress_callback: Optional[callable] = None
) -> VerificationReport:
    """
    End-to-end orchestration of CiteVerify pipeline.
    """
    def report_progress(stage: str, percent: int):
        if progress_callback:
            progress_callback(stage, percent)

    # Stage 1: Ingest
    report_progress("Ingesting document and detecting citation style", 10)
    ingest_res = ingest_document(file_bytes, filename)

    # Stage 2: Extract claims
    report_progress("Extracting and verifying verifiable claims", 25)
    claims = extract_claims(ingest_res.body_text, ingest_res.pages)
    for c in claims:
        c.atomic_subclaims = decompose_claim(c.verbatim_text, claim_id=c.id)

    # Stage 3: Parse references & verify bibliographic metadata
    report_progress("Parsing bibliography and resolving DOIs", 40)
    references = parse_references(ingest_res.references_text, body_text=ingest_res.body_text)
    ref_verifications = {}
    for ref in references:
        ref_ver = reference_verifier.verify_reference(ref)
        ref_verifications[ref.key] = ref_ver

    # Stage 4: Map citation markers
    report_progress("Mapping citation markers and detecting orphan references", 55)
    pairs, orphan_references, unmatched_markers = map_claims_to_references(claims, references)

    # Stage 5: Retrieve scholarly packages
    report_progress("Retrieving sources across OpenAlex, Crossref & OA repositories", 70)
    ref_packages = {}
    for ref in references:
        pkg = retriever.retrieve_source(ref)
        pkg.reference_verification = ref_verifications.get(ref.key)
        if pkg.reference_verification and pkg.reference_verification.is_retracted:
            pkg.is_retracted = True
            if not pkg.retraction_details and pkg.reference_verification.retraction_details:
                pkg.retraction_details = pkg.reference_verification.retraction_details
        
        src_text = pkg.full_text_content or pkg.abstract or ""
        pkg_title = pkg.title or ref.title or ""
        pkg_year = pkg.publication_year or ref.year
        pkg.methodology_info = analyze_methodology(src_text, title=pkg_title)
        pkg.statistical_assessment = analyze_statistics(src_text)
        pkg.freshness_assessment = analyze_source_freshness(publication_year=pkg_year, claim_text="", source_title=pkg_title)
        ref_packages[ref.key] = pkg

    # Attach retrieved source packages to pairs
    for p in pairs:
        if p.reference_key and p.reference_key in ref_packages:
            p.source_package = ref_packages[p.reference_key]

    # Stage 6 & 7 & 8: Evidence Selection, Verification, Guardrails, and Scoring
    report_progress("Comparing evidence, applying guardrails, and computing strength scores", 85)
    claim_map: Dict[str, Claim] = {c.id: c for c in claims}
    pairs_by_claim: Dict[str, List[ClaimSourcePair]] = {}

    for p in pairs:
        c = claim_map.get(p.claim_id)
        if c:
            p.verdict = verify_claim_reference_pair(
                claim=c,
                reference=p.reference,
                source_package=p.source_package,
                candidate_refs=p.candidate_references
            )
            pairs_by_claim.setdefault(p.claim_id, []).append(p)

    # Build claim cards and roll up multiple citations
    claim_cards: List[ClaimCard] = []
    uncited_claims: List[Claim] = []

    for c in claims:
        c_pairs = pairs_by_claim.get(c.id, [])
        if not c.has_citation or (c_pairs and c_pairs[0].verdict.label == CoverageStateEnum.UNCITED.value):
            uncited_claims.append(c)

        if c_pairs:
            primary_verdict, roll_note = roll_up_verdicts(c_pairs)
        else:
            # Fallback if no pair generated
            primary_verdict = verify_claim_reference_pair(c, None, None)
            roll_note = None

        # Record initial system audit entry
        audit_entry = audit_manager.record_entry(
            claim_id=c.id,
            pair_id=c_pairs[0].pair_id if c_pairs else None,
            actor=ReviewerActorEnum.SYSTEM,
            action=ReviewerActionEnum.GENERATED,
            before_value=None,
            after_value={"label": primary_verdict.label, "score": primary_verdict.evidence_strength_score},
            note="Initial automated verification result."
        )

        ref_ver = None
        methodology = None
        stats = None
        causality = None
        multi_conf = None

        if c_pairs:
            primary_pair = c_pairs[0]
            if primary_pair.source_package:
                ref_ver = primary_pair.source_package.reference_verification
                methodology = primary_verdict.methodology_info or primary_pair.source_package.methodology_info
                stats = primary_verdict.statistical_assessment or primary_pair.source_package.statistical_assessment
            causality = primary_verdict.causality_assessment
            multi_conf = primary_verdict.multi_confidence

        claim_cards.append(ClaimCard(
            claim=c,
            pairs=c_pairs,
            primary_verdict=primary_verdict,
            ai_verdict=primary_verdict.label,
            final_verdict=primary_verdict.label,
            reference_verification=ref_ver,
            methodology_info=methodology,
            statistical_assessment=stats,
            causality_assessment=causality,
            multi_confidence=multi_conf,
            roll_up_note=roll_note,
            audit_history=[audit_entry],
            reviewer_status="pending"
        ))

    # Sort claim cards by risk order (Section 9)
    def card_risk_rank(card: ClaimCard) -> Tuple[int, float]:
        v_label = card.primary_verdict.label
        rank = RISK_SORT_ORDER.get(v_label, 9)
        # Prioritize retracted source banner
        if FlagEnum.RETRACTED_SOURCE in card.primary_verdict.flags:
            rank = -1
        # Lower score = higher risk
        return (rank, card.primary_verdict.evidence_strength_score)

    claim_cards.sort(key=card_risk_rank)

    # Compute summaries
    summary_counts: Dict[str, int] = {}
    for card in claim_cards:
        v = card.primary_verdict.label
        summary_counts[v] = summary_counts.get(v, 0) + 1

    retrieval_summary: Dict[str, int] = {
        EvidenceTierEnum.FULL_TEXT.value: 0,
        EvidenceTierEnum.ABSTRACT_ONLY.value: 0,
        EvidenceTierEnum.METADATA_ONLY.value: 0,
        EvidenceTierEnum.NOT_FOUND.value: 0
    }
    for pkg in ref_packages.values():
        retrieval_summary[pkg.evidence_tier.value] = retrieval_summary.get(pkg.evidence_tier.value, 0) + 1

    # Citation Health Indicator: share of cited claims rated Supported with verified evidence
    cited_cards = [c for c in claim_cards if c.claim.has_citation and c.primary_verdict.label != CoverageStateEnum.UNCITED.value]
    supported_with_verified_evidence = [
        c for c in cited_cards 
        if c.primary_verdict.label == VerdictEnum.SUPPORTED.value and c.primary_verdict.verified_evidence_quote is not None
    ]
    if cited_cards:
        health_score = round((len(supported_with_verified_evidence) / len(cited_cards)) * 100.0, 1)
    else:
        health_score = 0.0

    # Items needing review count
    items_needing_review = sum(
        1 for card in claim_cards 
        if FlagEnum.NEEDS_HUMAN_REVIEW in card.primary_verdict.flags 
        or card.primary_verdict.evidence_strength_score < settings.SCORE_REVIEW_THRESHOLD
    )

    # Stage 9: Document Intelligence, Internal Contradictions, and Scorecard
    report_progress("Analyzing internal contradictions and computing integrity scorecard", 95)
    internal_contradictions = detect_internal_contradictions(claims, ingest_res.body_text)
    scorecard = compute_document_scorecard(claims, claim_cards, references, internal_contradictions)

    report_progress("Report ready", 100)

    now_iso = datetime.now(timezone.utc).isoformat()
    return VerificationReport(
        document_name=filename,
        total_pages=ingest_res.total_pages,
        citation_style=ingest_res.citation_style,
        total_claims=len(claims),
        summary_counts=summary_counts,
        citation_health_indicator=health_score,
        items_needing_review_count=items_needing_review,
        retrieval_summary=retrieval_summary,
        claim_cards=claim_cards,
        orphan_references=orphan_references,
        unmatched_markers=unmatched_markers,
        uncited_claims=uncited_claims,
        scorecard=scorecard,
        internal_contradictions=internal_contradictions,
        created_at=now_iso
    )
