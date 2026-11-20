# 🛡️ CiteVerify — Scientific Claim & Citation Verification System

> **“Your citation integrity copilot — verify what your sources actually say.”**  
> *INNOVEDGE Hackathon 2026 · Problem Statement 03 · Domain: Research Technology & Academic Integrity*

CiteVerify is an evidence-backed verification copilot that reads academic documents (PDF or TXT), extracts verifiable claims and citations, retrieves original scholarly publications across OpenAlex, Crossref, and Open Access repositories, and verifies whether cited sources genuinely substantiate the claims made.

---

## 🌟 Key Capabilities & Architectural Highlights

1. **Evidence Before Verdict**: No verdict is displayed without an underlying verified evidence quote.
2. **Verified Quotes Only**: Displayed evidence quotes are verbatim substrings checked in code after normalizing ligatures, line-break hyphenation, whitespace, and smart quotes. Unverified quotes are dropped and routed to review.
3. **An Abstract is Not the Paper**: Absence of evidence in an abstract is not evidence of absence. Negative verdicts (`UNSUPPORTED`, `CONTRADICTORY`) are blocked on abstract-only sources unless the abstract itself explicitly contradicts the claim.
4. **Number-Aware Verification**: Normalizes numbers, percentages, and multipliers. Searches whole retrieved papers; flags `NUMBER_MISMATCH` if values diverge (e.g. 18% reported vs 45% claimed) or `NUMBER_NOT_FOUND`.
5. **Computed Evidence Strength Score**: A deterministic $0.0 - 1.0$ indicator (High, Medium, Low) computed in code from observable signals: evidence tier, retrieval similarity, quote verification, and number agreement. Never framed as an accuracy or probability.
6. **Dedicated DOI & Bibliographic Verification Engine**: Verifies DOI resolution, author match, title fuzzy match, year, publication type, peer-review status, and flags `doi_not_found`, `metadata_mismatch`, `fabricated_suspected`, `preprint_only`, or `retracted`.
7. **Atomic Claim Decomposition**: Automatically splits compound multi-assertion sentences into discrete atomic subclaims, categorized by scientific type (`statistic`, `finding`, `causal`, `comparative`, `general`) with named entity extraction.
8. **Study Methodology & Explicit Author Limitations**: Automatically classifies study design (`randomized_controlled_trial`, `prospective_cohort`, `retrospective_cohort`, `in_vitro_or_animal_model`, etc.), extracts sample sizes (e.g., $N=12$), and strictly distinguishes explicit author limitations from AI-inferred concerns.
9. **Causal Overclaim & Language Gap Detector**: Identifies linguistic causal assertions (e.g., "causes", "leads to", "proves") applied to observational or correlational designs, flagging `CAUSALITY_OVERCLAIM`.
10. **Domain-Aware Freshness Engine**: Evaluates time sensitivity against domain-specific volatility thresholds (AI: 5 yrs, LLMs: 3 yrs, clinical oncology: 10 yrs, math: 50 yrs), distinguishing foundational citations from outdated evidence.
11. **Internal Contradiction & Diversity Intelligence**: Cross-evaluates all claims within the document to detect conflicting statements and calculates publisher and author independence.
12. **Research Integrity Scorecard**: Computes a transparent Research Integrity Index (0–100), Citation Coverage %, Source Diversity, and itemized penalty deductions.
13. **Human-in-the-Loop Review & Append-Only Audit Trail**: Every finding can be accepted, rejected, marked false positive, overridden, or annotated, with single-click undo. All actions are permanently persisted to an append-only SQLite audit log.
14. **Expanded Multi-Format Export Engine**: Generates Standalone Printable HTML Reports, structured JSON dossiers, CSV audit matrices, and corrected BibTeX (`.bib`) bibliography files.
15. **Provider-Agnostic LLM Engine & 100% Offline Mode**: Runs seamlessly with Google Gemini, OpenAI, Claude, or offline pre-warmed cache (`OFFLINE_DEMO=true`).

---

## 📋 The 8 Planted Demo Cases

| Case | Planted Condition | Ground Truth / Source Behavior | Verdict Assigned | Key Flags |
|---|---|---|---|---|
| **C1** | Correct citation | Kaplan et al. (2020) Scaling Laws | `SUPPORTED` | Full Text Open Access |
| **C2** | Wrong number in claim | Claim states 45% exam pass rate; source says 18% | `PARTIALLY_SUPPORTED` | `NUMBER_MISMATCH`, `NEEDS_HUMAN_REVIEW` |
| **C3** | Overgeneralized claim | Claim asserts stress elimination across all demographics; study was pilot of 35 students | `PARTIALLY_SUPPORTED` | `SCOPE_OVERGENERALIZED` |
| **C4** | Real but unrelated paper | Claim asserts potassium channel gating; source measures lipid bilayer shear mechanics | `UNSUPPORTED` | Full Text Open Access |
| **C5** | Reference cannot be found | Non-existent quantum gradient descent paper | `UNVERIFIABLE` | Reason: `reference_not_found`, `NEEDS_HUMAN_REVIEW` |
| **C6** | Strong claim with no citation | Deep neural networks representation statement | `UNCITED` | `NEEDS_HUMAN_REVIEW` |
| **C7** | Old source for time-sensitive claim | 2007 statistical n-gram paper for modern token limits | `POSSIBLY_OUTDATED` | `NEEDS_HUMAN_REVIEW` (Recency Heuristic) |
| **C8** | Retracted publication | Vane & Doe (2018) osteogenesis scaffold study | `SUPPORTED` (Quote verified) | `RETRACTED_SOURCE`, `NEEDS_HUMAN_REVIEW` (Prominent Alert Banner) |

---

## 📊 Measured Benchmark (Section 13)

- **Dataset**: 20 hand-labeled scientific claim–source pairs (`app/demo/benchmark.py`)
- **Measured Exact Match Accuracy**: **85.0%** (17 / 20 ground-truth matches)
- Results are recorded in `BENCHMARK_RESULTS.json`.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.11+
- Node.js 18+ (for building the modern web UI)

### 2. Installation
```bash
# Clone or navigate to project directory
cd citeverify

# Install Python requirements
pip install -r requirements.txt
```

### 3. Run Pre-warm and Tests
```bash
# Verify the 8 planted demo cases and pre-warm cache
python -m app.demo.prewarm

# Run 20-sample mini-benchmark
python -m app.demo.benchmark

# Run the 54-test suite (including all 23 Advanced Integrity Scenarios A through W)
pytest -v
```

### 4. Start the CiteVerify Website
The modern React application is built into `frontend/dist/` and served directly by FastAPI at port 8000:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser to: **http://localhost:8000**

*(Optional) Alternative Streamlit viewer:*
```bash
streamlit run app/streamlit_app.py
```

---

## 📁 Repository Structure

```
citeverify/
├── .env.example              # Environment variables template
├── DECISIONS.md              # Architectural decisions, weights & formulas
├── README.md                 # Project documentation & user guide
├── BENCHMARK_RESULTS.json    # Measured 20-sample benchmark data
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
├── app/
│   ├── config.py             # App settings (Pydantic v2)
│   ├── main.py               # FastAPI backend & static server
│   ├── schemas.py            # Pydantic data models & strictly defined Enums
│   ├── streamlit_app.py      # Companion Streamlit viewer
│   ├── core/
│   │   ├── cache.py          # DiskCache (HTTP & LLM hash-keyed cache)
│   │   ├── llm_client.py     # Provider-agnostic LLM interface (Gemini/OpenAI/OfflineMock)
│   │   ├── audit.py          # SQLite append-only audit trail
│   │   └── scoring.py        # Computed Evidence Strength Score formula
│   ├── pipeline/
│   │   ├── orchestrator.py   # 10-stage verification pipeline orchestrator
│   │   ├── p1_ingest.py      # PDF & TXT parser, style detector
│   │   ├── p2_extract_claims.py # Verifiable claim extractor & verbatim verifier
│   │   ├── p3_parse_references.py # DOI regex & citation parser
│   │   ├── p4_map_markers.py # Numeric range & author-year mapper, orphan detector
│   │   ├── p5_retrieve.py    # Scholarly cascade (OpenAlex, Crossref, Unpaywall)
│   │   ├── p6_reference_checks.py # Metadata mismatch & retraction checks
│   │   ├── p7_select_evidence.py # BM25 chunk ranker with number booster
│   │   ├── p8_verify_guardrails.py # LLM judge & Section 4 code guardrails
│   │   ├── quote_verifier.py # Verbatim quote verifier (ligatures & whitespace)
│   │   └── number_checker.py # Quantitative figure normalizer & comparator
│   ├── demo/
│   │   ├── demo_doc.txt      # 2-page demo document with 8 planted cases
│   │   ├── demo_doc.pdf      # Digital PDF version
│   │   ├── prewarm.py        # Pre-warm & validation script
│   │   └── benchmark.py      # 20 hand-labeled mini-benchmark evaluator
│   └── export/
│       └── exporters.py      # JSON, CSV, and standalone printable HTML report
├── frontend/
│   ├── index.html            # Vite HTML entry
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite configuration & API proxy
│   ├── dist/                 # Production compiled frontend bundle
│   └── src/
│       ├── App.jsx           # Main React component
│       ├── main.jsx          # React DOM entry
│       └── index.css         # Styling, palette & responsive rules
└── tests/
    ├── test_api_endpoints.py # FastAPI route integration tests
    ├── test_end_to_end.py    # End-to-end demo document pipeline test
    ├── test_guardrails.py    # Guardrail enforcement unit tests
    ├── test_marker_mapping.py# Marker expansion & mapping tests
    ├── test_number_checker.py# Quantitative figure normalization tests
    ├── test_quote_verifier.py# Ligature & verbatim quote verification tests
    └── test_scoring.py       # Evidence strength score formula tests
```

---

## 🔒 Trust Principles & Guardrail Specifications

1. **Quote Enforcement**:
   - `SUPPORTED`, `PARTIALLY_SUPPORTED`, and `CONTRADICTORY` require verified quotes.
   - If verification fails in code, the quote is dropped, verdict set to `UNVERIFIABLE (evidence_unverified)`, and routed to `NEEDS_HUMAN_REVIEW`.
2. **Abstract-Only Tier Guardrail**:
   - Scores on abstract-only sources are capped at $\le 0.60$.
   - Negative verdicts (`UNSUPPORTED`, `CONTRADICTORY`) are blocked unless the abstract explicitly contradicts the claim.
3. **Number Check Guardrail**:
   - Numbers, percentages, and multipliers are extracted and searched across the entire retrieved source text.
   - Missing numbers in full text cap verdicts at `PARTIALLY_SUPPORTED` (`NUMBER_NOT_FOUND` or `NUMBER_MISMATCH`).
4. **Outdated Literature Heuristic**:
   - Sources older than 10 years on time-sensitive claims receive `POSSIBLY_OUTDATED` and are labeled as a recency heuristic.
5. **Retraction Enforcement**:
   - Retracted sources trigger a prominent banner and force `NEEDS_HUMAN_REVIEW`.
6. **Multi-Citation Aggregation**:
   - For claims citing multiple references (e.g. `[1, 2]`), evaluations are performed per pair and rolled up to the strongest support, explicitly noting split support.

---

## 📄 Licensing & Disclaimer

CiteVerify is designed as an integrity copilot to support student researchers, educators, and peer reviewers. It does not replace human academic judgment. All findings remain subject to reviewer verification.
