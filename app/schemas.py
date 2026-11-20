from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# --- Enums strictly following the brief and advanced specification ---

class VerdictEnum(str, Enum):
    # Core Verdicts
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTORY = "CONTRADICTORY"
    POSSIBLY_OUTDATED = "POSSIBLY_OUTDATED"
    MIXED_EVIDENCE = "MIXED_EVIDENCE"
    # Coverage States
    UNCITED = "UNCITED"
    AMBIGUOUS_CITATION = "AMBIGUOUS_CITATION"
    UNVERIFIABLE = "UNVERIFIABLE"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"
    # Secondary Citation Verdicts
    SECONDARY_SOURCE_VERIFIED = "SECONDARY_SOURCE_VERIFIED"
    ORIGINAL_SOURCE_VERIFIED = "ORIGINAL_SOURCE_VERIFIED"
    SECONDARY_CITATION_ONLY = "SECONDARY_CITATION_ONLY"
    ORIGINAL_SOURCE_UNVERIFIABLE = "ORIGINAL_SOURCE_UNVERIFIABLE"
    CLAIM_NOT_SUPPORTED_BY_SECONDARY_SOURCE = "CLAIM_NOT_SUPPORTED_BY_SECONDARY_SOURCE"
    # Advanced Research Intelligence Verdicts (Feature 3)
    OVERGENERALIZED = "OVERGENERALIZED"
    CAUSALITY_OVERCLAIM = "CAUSALITY_OVERCLAIM"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    CONTEXT_OMITTED = "CONTEXT_OMITTED"
    MISINTERPRETED = "MISINTERPRETED"

class CoverageStateEnum(str, Enum):
    UNCITED = "UNCITED"
    AMBIGUOUS_CITATION = "AMBIGUOUS_CITATION"
    UNVERIFIABLE = "UNVERIFIABLE"
    UNRESOLVED_REFERENCE = "UNRESOLVED_REFERENCE"

class UnverifiableReasonEnum(str, Enum):
    REFERENCE_NOT_FOUND = "reference_not_found"
    NO_ACCESSIBLE_TEXT = "no_accessible_text"
    INSUFFICIENT_EVIDENCE_ABSTRACT_ONLY = "insufficient_evidence_abstract_only"
    EVIDENCE_UNVERIFIED = "evidence_unverified"
    RETRIEVAL_ERROR = "retrieval_error"

class ReferenceVerificationStatusEnum(str, Enum):
    DOI_VERIFIED = "DOI_VERIFIED"
    PAPER_VERIFIED = "PAPER_VERIFIED"
    METADATA_PARTIAL = "METADATA_PARTIAL"
    DOI_METADATA_MISMATCH = "DOI_METADATA_MISMATCH"
    DOI_NOT_FOUND = "DOI_NOT_FOUND"
    DOI_UNRESOLVABLE = "DOI_UNRESOLVABLE"
    REFERENCE_METADATA_MISMATCH = "REFERENCE_METADATA_MISMATCH"
    METADATA_UNAVAILABLE = "METADATA_UNAVAILABLE"
    PAPER_NOT_RETRIEVABLE = "PAPER_NOT_RETRIEVABLE"
    FABRICATED_SUSPECTED = "FABRICATED_SUSPECTED"
    RETRACTED = "RETRACTED"
    CORRECTED = "CORRECTED"
    EXPRESSION_OF_CONCERN = "EXPRESSION_OF_CONCERN"
    PREPRINT_ONLY = "PREPRINT_ONLY"
    PUBLICATION_STATUS_UNKNOWN = "PUBLICATION_STATUS_UNKNOWN"

class FlagEnum(str, Enum):
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    ABSTRACT_ONLY = "ABSTRACT_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    NUMBER_MISMATCH = "NUMBER_MISMATCH"
    NUMBER_NOT_FOUND = "NUMBER_NOT_FOUND"
    SCOPE_OVERGENERALIZED = "SCOPE_OVERGENERALIZED"
    RETRACTED_SOURCE = "RETRACTED_SOURCE"
    METADATA_MISMATCH = "METADATA_MISMATCH"
    LOW_RETRIEVAL_MATCH = "LOW_RETRIEVAL_MATCH"
    MODEL_DISAGREEMENT = "MODEL_DISAGREEMENT"
    # Advanced Flags
    CAUSALITY_OVERCLAIM = "CAUSALITY_OVERCLAIM"
    CITATION_SCOPE_MISMATCH = "CITATION_SCOPE_MISMATCH"
    SMALL_SAMPLE_SIZE = "SMALL_SAMPLE_SIZE"
    RETROSPECTIVE_DESIGN = "RETROSPECTIVE_DESIGN"
    SINGLE_CENTER = "SINGLE_CENTER"
    INTERNAL_CONTRADICTION = "INTERNAL_CONTRADICTION"
    PREPRINT_SOURCE = "PREPRINT_SOURCE"
    EXPRESSION_OF_CONCERN = "EXPRESSION_OF_CONCERN"
    DOI_METADATA_MISMATCH = "DOI_METADATA_MISMATCH"
    DOI_NOT_FOUND = "DOI_NOT_FOUND"
    DOI_UNRESOLVABLE = "DOI_UNRESOLVABLE"
    METADATA_UNAVAILABLE = "METADATA_UNAVAILABLE"
    FABRICATED_REFERENCE = "FABRICATED_REFERENCE"
    UNCITED_FACTUAL_CLAIM = "UNCITED_FACTUAL_CLAIM"
    HISTORICAL_CITATION = "HISTORICAL_CITATION"
    METHODOLOGY_NOT_REPORTED = "METHODOLOGY_NOT_REPORTED"

class EvidenceTierEnum(str, Enum):
    FULL_TEXT = "FULL_TEXT"
    ABSTRACT_ONLY = "ABSTRACT_ONLY"
    METADATA_ONLY = "METADATA_ONLY"
    NOT_FOUND = "NOT_FOUND"

class ScoreBandEnum(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class ClaimTypeEnum(str, Enum):
    # Core & Expanded Types (Section 9)
    EMPIRICAL_FINDING = "empirical_finding"
    STATISTICAL_CLAIM = "statistical_claim"
    COMPARATIVE_CLAIM = "comparative_claim"
    INTERPRETATION = "interpretation"
    HYPOTHETICAL = "hypothetical"
    RECOMMENDATION = "recommendation"
    BACKGROUND_KNOWLEDGE = "background_knowledge"
    HISTORICAL_CLAIM = "historical_claim"
    CAUSAL_CLAIM = "causal_claim"
    POLICY_OR_NORMATIVE_CLAIM = "policy_or_normative_claim"
    # Backwards compatibility aliases
    STATISTIC = "statistic"
    FINDING = "finding"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    PREDICTION = "prediction"
    HISTORICAL = "historical"
    GENERAL = "general"

class ReviewerActionEnum(str, Enum):
    GENERATED = "generated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MARK_FALSE_POSITIVE = "mark_false_positive"
    OVERRIDDEN = "overridden"
    NOTED = "noted"
    UNDO = "undo"

class ReviewerActorEnum(str, Enum):
    SYSTEM = "system"
    REVIEWER = "reviewer"


# --- Data Models ---

class AtomicSubclaim(BaseModel):
    """Sub-sentence atomic claim extracted by Claim Decomposition Engine (Feature 2)."""
    subclaim_id: str
    parent_claim_id: str
    text: str
    is_factual: bool = True
    category: ClaimTypeEnum = ClaimTypeEnum.FINDING
    original_text_span: Optional[str] = None
    qualifiers: List[str] = Field(default_factory=list)
    citation_markers: List[str] = Field(default_factory=list)
    scope: Optional[str] = None
    population: Optional[str] = None
    outcome: Optional[str] = None
    context: Optional[str] = None
    verdict: Optional[str] = None
    confidence: float = 0.0
    evidence_quote: Optional[str] = None
    reason: Optional[str] = None

class Claim(BaseModel):
    id: str
    verbatim_text: str
    type: ClaimTypeEnum = ClaimTypeEnum.FINDING
    page: int = 1
    section: str = "Body"
    citation_markers: List[str] = Field(default_factory=list)
    has_citation: bool = True
    atomic_subclaims: List[AtomicSubclaim] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return self.verbatim_text

class Reference(BaseModel):
    key: str  # e.g., "1", "Smith2020"
    raw_string: str
    title: str = ""
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    parse_method: str = "regex"  # regex, llm, in_text, fallback

class TextChunk(BaseModel):
    chunk_id: str
    page: int = 1
    section: Optional[str] = None
    text: str

class ReferenceVerificationResult(BaseModel):
    """Detailed verification from DOI & Bibliographic Verification Engine (Feature 1)."""
    status: ReferenceVerificationStatusEnum = ReferenceVerificationStatusEnum.PUBLICATION_STATUS_UNKNOWN
    doi: Optional[str] = None
    original_doi: Optional[str] = None
    resolved_doi: Optional[str] = None
    doi_resolves: bool = False
    resolved_title: Optional[str] = None
    resolved_authors: List[str] = Field(default_factory=list)
    resolved_year: Optional[int] = None
    resolved_journal: Optional[str] = None
    resolved_volume: Optional[str] = None
    resolved_issue: Optional[str] = None
    resolved_pages: Optional[str] = None
    publisher: Optional[str] = None
    publication_type: Optional[str] = None
    is_peer_reviewed: Optional[bool] = None
    publication_status: str = "published"  # published, retracted, corrected, expression_of_concern, preprint, unknown
    status_source: Optional[str] = None
    status_notice_url: Optional[str] = None
    metadata_discrepancies: List[str] = Field(default_factory=list)
    suggested_correction: Optional[Dict[str, Any]] = None

    @property
    def is_retracted(self) -> bool:
        return (
            self.publication_status == "retracted" or 
            self.status == ReferenceVerificationStatusEnum.RETRACTED
        )

    @property
    def retraction_details(self) -> Optional[str]:
        if self.is_retracted:
            return f"Retracted publication ({self.status_source or 'Registry'}). Notice: {self.status_notice_url or 'N/A'}"
        return None

    @property
    def verified_title(self) -> Optional[str]:
        return self.resolved_title

    @property
    def verified_authors(self) -> List[str]:
        return self.resolved_authors

    @property
    def verified_year(self) -> Optional[int]:
        return self.resolved_year

    @property
    def verified_doi(self) -> Optional[str]:
        return self.resolved_doi or self.doi

    @property
    def extracted_doi(self) -> Optional[str]:
        return self.original_doi or self.doi

    @property
    def verified_journal(self) -> Optional[str]:
        return self.resolved_journal

    @property
    def match_source(self) -> str:
        return self.status_source or "Crossref/OpenAlex"

    @property
    def reference_key(self) -> str:
        return ""

class MethodologyInfo(BaseModel):
    """Methodological analysis of the cited research (Feature 5, Section 10)."""
    study_design: str = "observational"  # rct, meta_analysis, systematic_review, prospective_cohort, retrospective_cohort, etc.
    sample_size: Optional[str] = None
    patient_count: Optional[int] = None
    dataset_size: Optional[str] = None
    number_of_studies: Optional[int] = None
    number_of_centers: Optional[str] = None
    geographic_coverage: Optional[str] = None
    evaluation_setting: Optional[str] = None
    is_prospective: Optional[bool] = None
    is_multicenter: Optional[bool] = None
    has_external_validation: Optional[bool] = None
    has_control_group: Optional[bool] = None
    risk_of_bias: str = "unclear"  # low, moderate, high, unclear
    primary_outcomes: List[str] = Field(default_factory=list)
    explicit_author_limitations: List[str] = Field(default_factory=list)
    methodological_concerns: List[str] = Field(default_factory=list)
    ai_inferred_concerns: List[str] = Field(default_factory=list)
    funding_and_conflicts: Optional[str] = None
    methodology_evidence: Dict[str, str] = Field(default_factory=dict)

    @property
    def sample_size_str(self) -> str:
        return self.sample_size or (str(self.patient_count) if self.patient_count else "Not specified")

class StatisticalAssessment(BaseModel):
    """Statistical evidence context and extraction (Feature 6)."""
    reported_metrics: Dict[str, Any] = Field(default_factory=dict)
    has_confidence_intervals: bool = False
    sample_size_adequate: bool = True
    class_balance_status: str = "balanced_or_unreported"
    data_leakage_risk: str = "low"  # low, moderate, high
    statistical_limitations: List[str] = Field(default_factory=list)
    summary: str = ""

class CausalityAssessment(BaseModel):
    """Correlation vs Causation evaluation (Feature 7)."""
    causal_claim_detected: bool = False
    causal_linguistic_terms: List[str] = Field(default_factory=list)
    study_design_supports_causation: bool = True
    is_causality_overclaim: bool = False
    explanation: Optional[str] = None

    @property
    def detected_causal_verbs(self) -> List[str]:
        return self.causal_linguistic_terms

class FreshnessAssessment(BaseModel):
    """Intelligent context-aware source freshness (Feature 8)."""
    publication_year: Optional[int] = None
    age_years: Optional[int] = None
    domain: str = "general"
    domain_freshness_threshold: int = 10
    is_outdated: bool = False
    why_age_matters: str = ""
    newer_evidence_available: Optional[str] = None

class MultiDimensionalConfidence(BaseModel):
    """Multi-dimensional confidence scoring (Feature 20, Section 11)."""
    overall_score: float = 0.0
    claim_verification_confidence: float = 0.0
    source_authenticity_confidence: float = 0.0
    evidence_retrieval_confidence: float = 0.0
    methodology_assessment_confidence: float = 0.0
    metadata_verification_confidence: float = 0.0
    citation_resolution_confidence: float = 0.0
    claim_support_confidence: float = 0.0
    claim_extraction_confidence: float = 0.0
    is_calibrated: bool = False
    confidence_explanation: str = "Experimental system estimate based on multi-factor evidence calibration."
    notes: str = ""

class SourcePackage(BaseModel):
    reference_key: str
    resolved_identifiers: Dict[str, Any] = Field(default_factory=dict)
    title_match_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    abstract: Optional[str] = None
    oa_pdf_url: Optional[str] = None
    landing_url: Optional[str] = None
    text_chunks: List[TextChunk] = Field(default_factory=list)
    full_text: Optional[str] = None
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.NOT_FOUND
    retraction_flag: bool = False
    retraction_details: Optional[str] = None
    retrieval_log: List[str] = Field(default_factory=list)
    # Advanced Intelligence Fields
    reference_verification: Optional[ReferenceVerificationResult] = None
    methodology_info: Optional[MethodologyInfo] = None
    statistical_assessment: Optional[StatisticalAssessment] = None
    freshness_assessment: Optional[FreshnessAssessment] = None

    @property
    def title(self) -> str:
        return self.metadata.get("title", "")

    @property
    def publication_year(self) -> Optional[int]:
        return self.metadata.get("year")

    @property
    def is_retracted(self) -> bool:
        return self.retraction_flag

    @is_retracted.setter
    def is_retracted(self, val: bool):
        self.retraction_flag = val

    @property
    def full_text_content(self) -> Optional[str]:
        return self.full_text

class ScoreBreakdown(BaseModel):
    tier_score: float = 0.0
    retrieval_score: float = 0.0
    quote_score: float = 0.0
    number_score: float = 0.0
    model_certainty_score: float = 0.0
    cap_applied: Optional[str] = None
    summary: str = ""

class VerdictResult(BaseModel):
    label: str  # VerdictEnum or CoverageStateEnum value
    unverifiable_reason: Optional[UnverifiableReasonEnum] = None
    evidence_strength_score: float = 0.0
    score_band: ScoreBandEnum = ScoreBandEnum.LOW
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    reason: str  # max 2 sentences
    verified_evidence_quote: Optional[str] = None
    quote_location: Optional[str] = None  # e.g. "Page 3, Section Results, Chunk 4"
    scope_notes: Optional[str] = None
    source_link: Optional[str] = None
    evidence_tier: EvidenceTierEnum = EvidenceTierEnum.NOT_FOUND
    flags: List[FlagEnum] = Field(default_factory=list)
    model_name: str = "CiteVerify-Engine"
    timestamp: str = ""
    # Advanced Verification Details (Features 4, 7, 20)
    causality_assessment: Optional[CausalityAssessment] = None
    multidimensional_confidence: Optional[MultiDimensionalConfidence] = None
    methodology_summary: Optional[str] = None
    limitations_summary: Optional[str] = None
    recommended_action: Optional[str] = None
    methodology_info: Optional[MethodologyInfo] = None
    statistical_assessment: Optional[StatisticalAssessment] = None
    citation_status: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def multi_confidence(self) -> Optional[MultiDimensionalConfidence]:
        return self.multidimensional_confidence

    @multi_confidence.setter
    def multi_confidence(self, val: Optional[MultiDimensionalConfidence]):
        self.multidimensional_confidence = val

class ClaimSourcePair(BaseModel):
    pair_id: str
    claim_id: str
    reference_key: Optional[str] = None
    citation_marker: Optional[str] = None
    matched_reference_id: Optional[str] = None
    author: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    mapping_confidence: float = 1.0
    mapping_status: str = "MATCHED"  # MATCHED, UNMATCHED, AMBIGUOUS, SECONDARY_CITATION, NUMERIC_RESOLVED
    candidate_references: List[str] = Field(default_factory=list)
    reference: Optional[Reference] = None
    source_package: Optional[SourcePackage] = None
    verdict: Optional[VerdictResult] = None

class AuditEntry(BaseModel):
    id: str
    claim_id: str
    pair_id: Optional[str] = None
    timestamp: str
    actor: ReviewerActorEnum = ReviewerActorEnum.SYSTEM
    action: ReviewerActionEnum = ReviewerActionEnum.GENERATED
    reviewer_identity: Optional[str] = "System"
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    note: Optional[str] = None

class ClaimCard(BaseModel):
    claim: Claim
    pairs: List[ClaimSourcePair] = Field(default_factory=list)
    primary_verdict: VerdictResult
    ai_verdict: Optional[str] = None       # Preserved AI initial verdict
    human_verdict: Optional[str] = None    # Reviewer decision if modified
    final_verdict: str = "PENDING"        # Active operational verdict
    roll_up_note: Optional[str] = None
    audit_history: List[AuditEntry] = Field(default_factory=list)
    reviewer_status: str = "pending"       # pending, accepted, rejected, false_positive, overridden, noted
    reference_verification: Optional[ReferenceVerificationResult] = None
    methodology_info: Optional[MethodologyInfo] = None
    statistical_assessment: Optional[StatisticalAssessment] = None
    causality_assessment: Optional[CausalityAssessment] = None
    multi_confidence: Optional[MultiDimensionalConfidence] = None
    reviewer_override: Optional[str] = None
    reviewer_action: Optional[str] = None
    reviewer_note: Optional[str] = None
    citation_status: Optional[str] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)

class UnmatchedMarker(BaseModel):
    marker: str
    page: int
    context: str
    candidates: List[str] = Field(default_factory=list)

class InternalContradiction(BaseModel):
    """Contradiction detected across different sections of the document (Feature 13)."""
    id: str
    statement_a: str
    location_a: str
    statement_b: str
    location_b: str
    explanation: str
    severity: str = "high"  # high, moderate, low

class DocumentScorecard(BaseModel):
    """Document-level research integrity scorecard (Feature 12)."""
    citation_coverage_pct: float = 0.0
    total_factual_claims: int = 0
    claims_with_citations: int = 0
    uncited_claims: int = 0
    research_integrity_score: float = 0.0  # 0 to 100
    integrity_score_formula: str = ""
    integrity_score_breakdown: Dict[str, float] = Field(default_factory=dict)
    total_references: int = 0
    independent_sources: int = 0
    overlapping_sources: int = 0
    internal_contradictions_count: int = 0

    @property
    def research_integrity_index(self) -> float:
        return self.research_integrity_score

    @property
    def index_formula_description(self) -> str:
        return self.integrity_score_formula

    @property
    def cited_claims_count(self) -> int:
        return self.claims_with_citations

    @property
    def total_claims(self) -> int:
        return self.total_factual_claims

    @property
    def source_diversity_ratio(self) -> float:
        if self.total_references == 0:
            return 1.0
        return round(self.independent_sources / self.total_references, 2)

    @property
    def unique_sources_count(self) -> int:
        return self.independent_sources

    @property
    def retracted_sources_count(self) -> int:
        return int(self.integrity_score_breakdown.get("retraction_penalties", 0) > 0)

class VerificationReport(BaseModel):
    document_name: str
    total_pages: int = 1
    citation_style: str = "numeric"  # numeric, author-year
    total_claims: int = 0
    summary_counts: Dict[str, int] = Field(default_factory=dict)
    citation_health_indicator: float = 0.0  # percentage 0-100 of cited claims rated Supported with verified evidence
    citation_health_caveat: str = (
        "Indicator reflects the share of cited claims with verified verbatim evidence from retrieved texts. "
        "It is an aid for human reviewers, not a final academic judgment."
    )
    items_needing_review_count: int = 0
    retrieval_summary: Dict[str, int] = Field(default_factory=dict)
    claim_cards: List[ClaimCard] = Field(default_factory=list)
    orphan_references: List[Reference] = Field(default_factory=list)
    unmatched_markers: List[UnmatchedMarker] = Field(default_factory=list)
    uncited_claims: List[Claim] = Field(default_factory=list)
    limitations_statement: str = (
        "CiteVerify is an integrity copilot, not an autonomous academic judge. "
        "Paywalled sources may be limited to abstracts. All findings remain subject to human academic review."
    )
    # Advanced Intelligence Fields (Features 12, 13)
    scorecard: Optional[DocumentScorecard] = None
    internal_contradictions: List[InternalContradiction] = Field(default_factory=list)
    created_at: str = ""

    @property
    def claims(self) -> List[Claim]:
        return [c.claim for c in self.claim_cards]

    @property
    def references(self) -> List[Reference]:
        refs = []
        seen = set()
        for card in self.claim_cards:
            for pair in card.pairs:
                if pair.reference and pair.reference.key not in seen:
                    seen.add(pair.reference.key)
                    refs.append(pair.reference)
        for r in self.orphan_references:
            if r.key not in seen:
                seen.add(r.key)
                refs.append(r)
        return refs

# API Request/Response Schemas
class ReviewOverrideRequest(BaseModel):
    claim_id: str
    pair_id: Optional[str] = None
    action: ReviewerActionEnum  # accepted, rejected, mark_false_positive, overridden, noted, undo
    new_verdict: Optional[str] = None
    note: Optional[str] = None
    justification: Optional[str] = None
    reviewer_name: str = "Reviewer"

class VerifyTextRequest(BaseModel):
    text: str
    filename: Optional[str] = "pasted_document.txt"
