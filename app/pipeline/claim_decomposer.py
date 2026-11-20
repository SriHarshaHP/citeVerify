import re
from typing import List, Dict, Any, Tuple
from app.schemas import Claim, AtomicSubclaim, ClaimTypeEnum

# Linguistic indicators
OPINION_MARKERS = [
    "we believe", "in our view", "arguably", "should be considered", 
    "ought to", "it is hoped", "in the authors' opinion", "might represent"
]

CAUSAL_VERBS = [
    "causes", "caused", "leads to", "led to", "results in", "resulted in",
    "produces", "produced", "prevents", "prevented", "improves", "improved",
    "reduces", "reduced", "eliminates", "eliminated", "increases", "increased",
    "accelerates", "accelerated", "triggers", "triggered"
]

COMPARATIVE_TERMS = [
    "outperformed", "outperforms", "exceeding", "exceeded", "comparable to",
    "higher than", "lower than", "superior to", "inferior to", "faster than",
    "more accurate than", "better than", "worse than"
]

PREDICTION_TERMS = [
    "will", "is expected to", "are expected to", "is projected to",
    "are projected to", "will likely", "anticipate that"
]

RECOMMENDATION_TERMS = [
    "should", "must", "requires", "recommend", "recommended",
    "guidelines suggest", "ought to"
]

def classify_subclaim_category(text: str) -> Tuple[bool, ClaimTypeEnum]:
    """Determines if subclaim is factual and classifies its category."""
    lower = text.lower()

    # Factual vs Non-empirical / Non-factual
    if "hypothetical" in lower or "for example, suppose" in lower or "assume a scenario" in lower:
        return False, ClaimTypeEnum.HYPOTHETICAL
    elif any(rec in lower for rec in ["future investigations should", "future research should", "we recommend", "should prioritize", "guidelines suggest"]):
        return False, ClaimTypeEnum.RECOMMENDATION
    elif any(op in lower for op in OPINION_MARKERS) or any(intp in lower for intp in ["cannot establish", "should not automatically be interpreted", "cannot alone establish"]):
        return False, ClaimTypeEnum.INTERPRETATION

    is_factual = not any(op in lower for op in OPINION_MARKERS)

    # Category classification
    if any(re.search(r'\b\d+(\.\d+)?%|\b\d+x\b|\bp\s*[<>=]\s*0\.\d+|\bCI\b|\bAUC\b', lower, re.I) for _ in [1]):
        category = ClaimTypeEnum.STATISTIC
    elif any(term in lower for term in COMPARATIVE_TERMS):
        category = ClaimTypeEnum.COMPARATIVE
    elif any(term in lower for term in CAUSAL_VERBS):
        category = ClaimTypeEnum.CAUSAL
    elif any(term in lower for term in PREDICTION_TERMS):
        category = ClaimTypeEnum.PREDICTION
    elif any(term in lower for term in RECOMMENDATION_TERMS):
        category = ClaimTypeEnum.RECOMMENDATION
    elif any(yr in lower for yr in ["in 200", "in 199", "historically", "earlier research"]):
        category = ClaimTypeEnum.HISTORICAL
    else:
        category = ClaimTypeEnum.FINDING

    return is_factual, category

def extract_scope_and_entities(text: str) -> Dict[str, Any]:
    """Identifies scope, population, outcome, and context where present."""
    lower = text.lower()

    # Population heuristics
    population = None
    pop_matches = re.findall(
        r'\b(?:across|in|among)\s+(?:all\s+)?([a-z\s]+?(?:cohorts?|students?|patients?|adults?|demographics?|models?|specialties|cases))\b',
        lower
    )
    if pop_matches:
        population = pop_matches[0].strip()

    # Scope heuristics (e.g. under selected conditions, universal, retrospective)
    scope = None
    if "across all" in lower or "universally" in lower or "consistently across" in lower:
        scope = "Universal / Broad Extrapolation"
    elif "under selected" in lower or "in pilot" in lower or "in a single" in lower:
        scope = "Restricted / Selected Context"
    elif "retrospective" in lower:
        scope = "Retrospective Dataset"

    # Outcome heuristics
    outcome = None
    out_matches = re.findall(
        r'\b(?:improve|improving|reduces?|reducing|increases?|increasing|eliminate|eliminating|outperform|outperforming)\s+([a-z\s]+?)(?:across|in|under|by|\.|\,|$)',
        lower
    )
    if out_matches:
        outcome = out_matches[0].strip()

    return {
        "scope": scope,
        "population": population,
        "outcome": outcome,
        "context": None
    }

def split_outside_brackets(s: str, delimiter: str = ';') -> List[str]:
    """Splits a string by delimiter only when not enclosed in parentheses or brackets."""
    parts = []
    current = []
    depth_paren = 0
    depth_bracket = 0
    for char in s:
        if char == '(':
            depth_paren += 1
            current.append(char)
        elif char == ')':
            depth_paren = max(0, depth_paren - 1)
            current.append(char)
        elif char == '[':
            depth_bracket += 1
            current.append(char)
        elif char == ']':
            depth_bracket = max(0, depth_bracket - 1)
            current.append(char)
        elif char == delimiter and depth_paren == 0 and depth_bracket == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(char)
    last = "".join(current).strip()
    if last:
        parts.append(last)
    return parts

def is_citation_fragment(text: str) -> bool:
    """Checks whether text appears to be an orphaned citation or citation fragment."""
    t = text.strip()
    if t.count(')') > t.count('(') or t.count(']') > t.count('['):
        return True
    clean = re.sub(r'[.,;()\s]', '', t)
    if re.match(r'^(?:[A-Z][a-zA-Z]+|\d+|et|al)+$', clean) and len(t.split()) <= 6:
        if re.search(r'\b(?:19|20)\d{2}\b', t):
            return True
    if len(t.split()) < 2:
        return True
    return False

def decompose_compound_sentence(sentence: str) -> List[str]:
    """
    Decomposes a compound sentence into atomic statements.
    Never splits inside parenthetical citations or creates citation fragments.
    """
    s = sentence.strip().rstrip('.')

    # 1. Check for semicolons strictly outside parentheses and brackets
    semi_parts = split_outside_brackets(s, ';')
    if len(semi_parts) > 1:
        if not any(is_citation_fragment(p) for p in semi_parts) and all(len(p.split()) >= 4 for p in semi_parts):
            return [f"{p.rstrip('.')}." for p in semi_parts]

    # Clean citation markers from text before splitting to parse grammar accurately
    clean_s = re.sub(r'\[\s*(?:\d+(?:\s*[,-]\s*\d+)*)\s*\]', '', s)
    clean_s = re.sub(r'\([A-Za-z0-9\s,\.\-;&]+?\)', '', clean_s)

    # 2. Check for parallel verb phrases sharing a subject:
    # Example: "AI improves diagnostic accuracy, reduces costs, eliminates bias, and improves patient survival"
    m_verb_series = re.match(r'^([A-Z][a-zA-Z0-9\s\(\)\-]+?)\s+((?:[a-z]+(?:es|s|ed|ing))\s+.+)$', clean_s)
    if m_verb_series:
        subj = m_verb_series.group(1).strip()
        rest = m_verb_series.group(2).strip()
        parts = [p.strip() for p in re.split(r',\s*(?:and\s+)?|\s+and\s+', rest) if p.strip()]
        if len(parts) >= 2 and all(any(p.split()[0].lower().endswith(end) for end in ['s', 'es', 'ed', 'ing']) for p in parts):
            if not any(is_citation_fragment(p) for p in parts):
                return [f"{subj} {p}." for p in parts]

    # Two parallel verb phrases: "AI improves diagnostic accuracy and reduces clinical workload"
    two_vp = re.match(r'^([A-Z][a-zA-Z0-9\s\(\)\-]+?)\s+((?:[a-z]+(?:es|s|ed|ing))\s+.+?)\s+(?:and|while)\s+((?:[a-z]+(?:es|s|ed|ing))\s+.+)$', clean_s)
    if two_vp:
        subject = two_vp.group(1).strip()
        vp1 = two_vp.group(2).strip()
        vp2 = two_vp.group(3).strip()
        first_word_vp2 = vp2.split()[0].lower()
        if any(first_word_vp2.endswith(end) for end in ['s', 'es', 'ed', 'ing']):
            if not is_citation_fragment(vp1) and not is_citation_fragment(vp2):
                return [
                    f"{subject} {vp1}.",
                    f"{subject} {vp2}."
                ]

    # Independent clauses separated by comma + conjunction: "X demonstrated Y, but A showed B"
    conj_match = re.split(r',\s+(?:whereas|while|but)\s+', s)
    if len(conj_match) > 1 and all(len(c.strip()) > 20 and not is_citation_fragment(c) for c in conj_match):
        return [f"{c.strip().rstrip('.')}." for c in conj_match]

    # If sentence cannot be split cleanly into independent atomic claims, treat as single atomic claim
    return [f"{s}."]

from typing import List, Dict, Any, Tuple, Union

def decompose_claim(claim: Union[Claim, str], claim_id: str = "C1") -> List[AtomicSubclaim]:
    """
    Decomposes a document claim into atomic subclaims (Feature 2).
    Maps all atomic subclaims back to the original claim sentence.
    Accepts either a Claim instance or a claim text string.
    """
    if isinstance(claim, Claim):
        text = claim.verbatim_text
        c_id = claim.id
    else:
        text = str(claim)
        c_id = claim_id

    raw_subclaims = decompose_compound_sentence(text)
    atomic_claims = []

    for idx, sub_text in enumerate(raw_subclaims):
        sub_id = f"{c_id}.{idx + 1}"
        is_factual, category = classify_subclaim_category(sub_text)
        entities = extract_scope_and_entities(sub_text)

        atomic_claims.append(AtomicSubclaim(
            subclaim_id=sub_id,
            parent_claim_id=c_id,
            text=sub_text,
            is_factual=is_factual,
            category=category,
            scope=entities["scope"],
            population=entities["population"],
            outcome=entities["outcome"],
            context=entities["context"]
        ))

    return atomic_claims
