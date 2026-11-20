import pytest
from app.pipeline.quote_verifier import verify_quote_in_text, normalize_text_for_matching

def test_exact_quote_match():
    text = "We observe that neural language models scale predictably across compute orders."
    quote = "neural language models scale predictably"
    verified, partial, matched = verify_quote_in_text(quote, text)
    assert verified is True
    assert matched == "neural language models scale predictably"

def test_quote_with_ligatures():
    # Source text contains typographic ligature 'ﬁ'
    text = "The classiﬁcation of high-dimensional manifold structures requires robust representations."
    quote = "classification of high-dimensional"
    verified, partial, matched = verify_quote_in_text(quote, text)
    assert verified is True

def test_quote_with_hyphenated_linebreak():
    text = "The trans-\nformer architecture outperforms recurrent baselines on machine translation."
    quote = "transformer architecture outperforms"
    verified, partial, matched = verify_quote_in_text(quote, text)
    assert verified is True

def test_quote_with_whitespace_and_smart_quotes():
    text = '“Deep   residual  learning   enables   hundred-layer networks.”'
    quote = '"Deep residual learning enables hundred-layer networks."'
    verified, partial, matched = verify_quote_in_text(quote, text)
    assert verified is True

def test_failed_invented_quote():
    text = "Our study demonstrated an 18% improvement in final examination pass rates."
    quote = "Our study demonstrated a massive 95% surge in test scores nationwide."
    verified, partial, matched = verify_quote_in_text(quote, text)
    assert verified is False
    assert matched is None
