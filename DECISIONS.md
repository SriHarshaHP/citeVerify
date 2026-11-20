# CiteVerify — Architectural and Scoring Decisions (DECISIONS.md)

This document records the design, scoring formulas, guardrail parameters, and architectural decisions for **CiteVerify**, adhering strictly to the INNOVEDGE Hackathon 2026 Problem Statement 03 Brief.

---

## 1. Trust Principles Enforcement

1. **Evidence Before Verdict**: No `SUPPORTED` or `CONTRADICTORY` verdict is rendered without a verified verbatim quote from retrieved text.
2. **Verified Quotes Only**: Displayed evidence quotes are substrings of retrieved text verified programmatically after normalizing whitespace (`\s+` -> `' '`), unicode ligatures (e.g., `fi` -> `fi`, `fl` -> `fl`), smart quotes/dashes, and case-folding. Failed quotes are dropped, resulting in `UNVERIFIABLE (evidence_unverified)` and `NEEDS_HUMAN_REVIEW`.
3. **Abstract Is Not the Paper**: When only abstract or metadata is retrieved, absence of evidence is not evidence of absence. `UNSUPPORTED` cannot be declared on abstract-only sources unless the abstract itself explicitly contradicts the claim or is plainly about a different subject. Score is capped at `0.60`.
4. **Not Found Does Not Mean Fake**: Language is strictly sanitized. We use `"reference could not be verified"`, never `"fake"`, `"fabricated"`, or `"hallucinated"`.
5. **Computed Evidence Strength Score**: The score is an observable indicator of evidence strength and uncertainty, computed in code from verifiable properties. It is never self-reported by an LLM, and never framed as a probability or accuracy.
6. **Human-in-the-Loop**: Every card provides Accept, Override, and Annotate actions with an immutable, append-only SQLite audit log.
7. **Traceability**: Every card links to the publication DOI / landing page / open-access PDF, displays chunk ID and page number, and records the audit history.
8. **No Silent Guessing**: Ambiguous citation markers, missing references, and low similarity matches are explicitly flagged.
9. **Untrusted Input**: All uploaded text and retrieved external text are treated strictly as untrusted data, enclosed in delimiters in LLM prompts, with instructions telling the LLM to ignore injected commands.

---

## 2. Evidence Strength Score Formula & Weights

The evidence strength score $S \in [0.0, 1.0]$ is computed deterministically in code based on observable signals:

$$S = w_{\text{tier}} \cdot S_{\text{tier}} + w_{\text{retrieval}} \cdot S_{\text{retrieval}} + w_{\text{quote}} \cdot S_{\text{quote}} + w_{\text{numbers}} \cdot S_{\text{numbers}} + w_{\text{model}} \cdot S_{\text{model}}$$

### Base Weights:
- **Evidence Tier Weight ($w_{\text{tier}} = 0.35$):**
  - `FULL_TEXT`: $1.0$
  - `ABSTRACT_ONLY`: $0.5$ (also caps overall score at $\le 0.60$)
  - `METADATA_ONLY`: $0.2$ (caps overall score at $\le 0.40$)
  - `NOT_FOUND`: $0.0$ (forces score $= 0.0$)
- **Retrieval Match Weight ($w_{\text{retrieval}} = 0.20$):**
  - DOI exact match: $1.0$
  - Title similarity match (rapidfuzz ratio): $\text{ratio} / 100$ (threshold $\ge 80\%$)
- **Quote Verification Weight ($w_{\text{quote}} = 0.25$):**
  - Exact verified quote: $1.0$
  - Partial/relaxed match: $0.5$
  - Failed/No quote: $0.0$
- **Number Agreement Weight ($w_{\text{numbers}} = 0.15$):**
  - All claim numbers present and matching: $1.0$
  - Claim has no numbers: $1.0$ (neutral)
  - Number not found in abstract-only: $0.7$
  - Number not found in full text: $0.3$
  - Number mismatch detected: $0.0$
- **Model Certainty Weight ($w_{\text{model}} = 0.05$):**
  - High certainty: $1.0$
  - Medium certainty: $0.6$
  - Low certainty: $0.2$

### Score Bands:
- **High**: $S \ge 0.75$
- **Medium**: $0.50 \le S < 0.75$
- **Low**: $S < 0.50$ (automatically triggers `NEEDS_HUMAN_REVIEW`)

---

## 3. Guardrails Rules

1. **Quote Enforcement**:
   - `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTORY` require verified quotes.
   - If quote fails verification: retry once with stricter prompt; if still failed, drop quote, set verdict `UNVERIFIABLE` with reason `evidence_unverified` and flag `NEEDS_HUMAN_REVIEW`.
2. **Tier Negative Verdict Enforcement**:
   - `UNSUPPORTED` and `CONTRADICTORY` are permitted only when `FULL_TEXT` is available, OR when the abstract explicitly addresses and contradicts/is completely unrelated to the claim. Otherwise set `UNVERIFIABLE` (`insufficient_evidence_abstract_only`).
3. **Number Check Enforcement**:
   - If full text is retrieved and a claim number is missing, the verdict is capped at `PARTIALLY_SUPPORTED`.
   - If a different number is found for the same measure, flag `NUMBER_MISMATCH`. If completely absent, flag `NUMBER_NOT_FOUND`.
   - If only abstract text is retrieved, flag `NUMBER_NOT_FOUND`, cap score at $0.60$, and route to review, but do not downgrade verdict on that basis alone.
4. **Outdated Heuristic**:
   - If source publication year is older than threshold (default $10$ years) and claim is classified as time-sensitive, assign `POSSIBLY_OUTDATED` and label as a recency heuristic.
5. **Retraction Enforcement**:
   - If source is flagged as retracted (via Crossref, OpenAlex, or Retraction Watch), force `RETRACTED_SOURCE` and `NEEDS_HUMAN_REVIEW` with an alert banner.
6. **Multi-Citation Aggregation**:
   - For claims with multiple citations (e.g., `[1, 2]`), generate a pair evaluation for each reference. Roll up to the strongest support for the claim summary card, while explicitly noting split support.

---

## 4. LLM Provider Independence

- CiteVerify defines an abstract `LLMClient` interface.
- Configured via `.env`:
  - `LLM_PROVIDER`: `gemini` | `openai` | `anthropic` | `offline_mock`
  - `LLM_API_KEY`: API key for selected provider
  - `LLM_MODEL_STRONG`: strong reasoning model (e.g. `gemini-1.5-pro`, `gpt-4o`, `claude-3-5-sonnet-20241022`)
  - `LLM_MODEL_FAST`: fast extraction model (e.g. `gemini-1.5-flash`, `gpt-4o-mini`, `claude-3-5-haiku-20241022`)
  - `OFFLINE_DEMO`: `true` / `false`
- Offline Demo mode loads pre-cached responses and realistic scholarly data without requiring internet or API keys.
