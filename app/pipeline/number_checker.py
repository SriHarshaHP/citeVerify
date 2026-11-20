import re
from typing import List, Dict, Any, Tuple

NUMBER_WORDS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
    'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
    'ten': 10, 'twelve': 12, 'twenty': 20, 'thirty': 30,
    'forty': 40, 'fifty': 50, 'hundred': 100, 'thousand': 1000
}

def extract_numbers_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extracts numbers, percentages, multipliers, and quantities from text.
    Returns list of dicts with:
      raw: str, value: float, is_percentage: bool, is_multiplier: bool
    """
    results = []

    # 1. Percentages (e.g. 45%, 45 percent, 18.5 %)
    pct_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:%|percent|percentage)', text, re.IGNORECASE)
    for m in pct_matches:
        results.append({
            "raw": m.group(0),
            "value": float(m.group(1)),
            "is_percentage": True,
            "is_multiplier": False
        })

    # 2. Multipliers (e.g. 120x, 120-fold, 120 times)
    mult_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:x|-fold|times)', text, re.IGNORECASE)
    for m in mult_matches:
        results.append({
            "raw": m.group(0),
            "value": float(m.group(1)),
            "is_percentage": False,
            "is_multiplier": True
        })

    # 3. Standard numbers (e.g. 1,000, 35, 0.42)
    # Ignore numbers that were already captured as percentages or multipliers
    num_matches = re.finditer(r'\b(?<!\.)\d{1,3}(?:,\d{3})*(?:\.\d+)?(?!\w)', text)
    for m in num_matches:
        val_str = m.group(0).replace(',', '')
        try:
            val = float(val_str)
            start, end = m.span()
            # Avoid page numbers (e.g., Page 1, p. 12, --- Page 1 ---)
            if re.search(r'(?:page|p\.)\s*$', text[:start], re.IGNORECASE):
                continue
            # Avoid duplicate if part of percentage or multiplier
            snippet = text[max(0, start - 2):min(len(text), end + 15)].lower()
            if any(s in snippet for s in ['%', 'percent', 'x', '-fold', 'times']):
                continue
            # Avoid single digit citation markers [1] if adjacent to brackets
            if (start > 0 and text[start-1] in '[]()') or (end < len(text) and text[end] in '[]()'):
                continue
            # Avoid years (1900 - 2099)
            if 1900 <= val <= 2099 and float(int(val)) == val:
                continue
            results.append({
                "raw": m.group(0),
                "value": val,
                "is_percentage": False,
                "is_multiplier": False
            })
        except ValueError:
            pass

    return results

def verify_numbers_against_text(claim_numbers: List[Dict[str, Any]], retrieved_full_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Checks whether numbers in the claim are present in the retrieved text.
    Returns:
      (status, mismatches)
      status in: "ok", "no_numbers", "mismatch", "missing"
    """
    if not claim_numbers:
        return "no_numbers", []

    text_numbers = extract_numbers_from_text(retrieved_full_text)
    text_values = [n["value"] for n in text_numbers]

    missing = []
    mismatched = []

    for cn in claim_numbers:
        c_val = cn["value"]
        # Check direct value match with small tolerance for rounding
        matched = False
        for tn in text_numbers:
            t_val = tn["value"]
            if abs(c_val - t_val) < 0.01:
                matched = True
                break
            elif tn["is_percentage"] and cn["is_percentage"] and abs(c_val - t_val) <= 0.5:
                matched = True
                break

        if not matched:
            # Check if there is another percentage/number in text serving as an alternative metric
            if cn["is_percentage"]:
                other_pcts = [t for t in text_numbers if t["is_percentage"]]
                if other_pcts:
                    mismatched.append({"claim_number": cn, "found_numbers": other_pcts})
                else:
                    missing.append(cn)
            else:
                missing.append(cn)

    if mismatched:
        return "mismatch", mismatched
    elif missing:
        return "missing", missing
    else:
        return "ok", []
