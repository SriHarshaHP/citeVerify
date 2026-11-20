import pytest
from app.pipeline.p4_map_markers import parse_numeric_marker_keys, match_author_year_marker
from app.schemas import Reference

def test_numeric_single_marker():
    assert parse_numeric_marker_keys("[1]") == ["1"]
    assert parse_numeric_marker_keys("1") == ["1"]

def test_numeric_list_marker():
    assert parse_numeric_marker_keys("[1, 3]") == ["1", "3"]
    assert parse_numeric_marker_keys("[1,3, 7]") == ["1", "3", "7"]

def test_numeric_range_marker():
    assert parse_numeric_marker_keys("[1-4]") == ["1", "2", "3", "4"]
    assert parse_numeric_marker_keys("[1–3]") == ["1", "2", "3"]  # en-dash

def test_numeric_composite_marker():
    assert parse_numeric_marker_keys("[1, 3-5, 8]") == ["1", "3", "4", "5", "8"]

def test_author_year_matching():
    refs = [
        Reference(key="1", raw_string="Smith, J. (2020)...", title="Paper 1", authors=["J. Smith"], year=2020),
        Reference(key="2", raw_string="Doe, A. (2021)...", title="Paper 2", authors=["A. Doe"], year=2021)
    ]
    matched, cands = match_author_year_marker("(Smith, 2020)", refs)
    assert matched == "1"
    assert cands == ["1"]

def test_author_year_ambiguous():
    refs = [
        Reference(key="1", raw_string="Smith, J. (2020a)...", title="Study A", authors=["J. Smith"], year=2020),
        Reference(key="2", raw_string="Smith, J. (2020b)...", title="Study B", authors=["J. Smith"], year=2020)
    ]
    matched, cands = match_author_year_marker("(Smith, 2020)", refs)
    assert matched is None
    assert len(cands) == 2
