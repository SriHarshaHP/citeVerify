import re
import unicodedata
from typing import Tuple, Optional

LIGATURES = {
    'ﬁ': 'fi',
    'ﬂ': 'fl',
    'ﬀ': 'ff',
    'ﬃ': 'ffi',
    'ﬄ': 'ffl',
    'æ': 'ae',
    'œ': 'oe',
}

def normalize_text_for_matching(text: str) -> str:
    """
    Normalizes text by removing ligatures, smart quotes, soft hyphens,
    line-break hyphens, and collapsing all whitespace.
    """
    if not text:
        return ""
    
    # 1. Unicode decomposition
    text = unicodedata.normalize("NFKD", text)

    # 2. Ligatures
    for lig, rep in LIGATURES.items():
        text = text.replace(lig, rep)

    # 3. Quotes and dashes
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    text = text.replace('—', '-').replace('–', '-')

    # 4. Remove soft hyphens and de-hyphenate linebreaks (e.g. "com-\npute" -> "compute")
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)

    # 5. Collapse all whitespace to a single space and remove spaces before punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)

    return text.strip()

def verify_quote_in_text(quote: str, source_text: str) -> Tuple[bool, bool, Optional[str]]:
    """
    Checks if `quote` is a verbatim substring of `source_text`.
    Returns:
      (verified: bool, is_partial: bool, matched_text: Optional[str])
    """
    if not quote or not source_text:
        return False, False, None

    norm_quote = normalize_text_for_matching(quote)
    norm_source = normalize_text_for_matching(source_text)

    if not norm_quote:
        return False, False, None

    # 1. Exact case-sensitive substring match
    if norm_quote in norm_source:
        return True, False, norm_quote

    # 2. Case-insensitive substring match
    lower_quote = norm_quote.lower()
    lower_source = norm_source.lower()
    idx = lower_source.find(lower_quote)
    if idx != -1:
        # Extract matched segment
        matched = norm_source[idx:idx + len(norm_quote)]
        return True, False, matched

    # 3. Punctuation-stripped match
    clean_quote = re.sub(r'[^\w\s]', '', lower_quote)
    clean_source = re.sub(r'[^\w\s]', '', lower_source)
    if clean_quote and clean_quote in clean_source:
        return True, False, norm_quote

    # 4. Partial overlap match (at least 75% consecutive tokens matched)
    quote_tokens = norm_quote.split()
    if len(quote_tokens) >= 6:
        # Check window
        window_size = int(len(quote_tokens) * 0.75)
        for i in range(len(quote_tokens) - window_size + 1):
            sub_phrase = " ".join(quote_tokens[i:i + window_size]).lower()
            if sub_phrase in lower_source:
                return False, True, norm_quote

    return False, False, None
