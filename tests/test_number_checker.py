import pytest
from app.pipeline.number_checker import extract_numbers_from_text, verify_numbers_against_text

def test_extract_percentages():
    text = "The model achieved 45% accuracy, compared to 18 percent previously."
    nums = extract_numbers_from_text(text)
    assert len(nums) == 2
    assert nums[0]["value"] == 45.0
    assert nums[0]["is_percentage"] is True
    assert nums[1]["value"] == 18.0
    assert nums[1]["is_percentage"] is True

def test_extract_multipliers():
    text = "Quantum algorithms achieve a 120x acceleration or 50-fold speedup."
    nums = extract_numbers_from_text(text)
    vals = [n["value"] for n in nums]
    assert 120.0 in vals
    assert 50.0 in vals

def test_number_agreement_ok():
    claim = "The system achieved 18% improvement."
    text = "Participants in the intervention group showed an 18% improvement on test scores."
    c_nums = extract_numbers_from_text(claim)
    status, details = verify_numbers_against_text(c_nums, text)
    assert status == "ok"

def test_number_mismatch():
    claim = "The intervention yielded a 45% increase in passing rates."
    text = "Results revealed an 18% increase in passing rates among participants."
    c_nums = extract_numbers_from_text(claim)
    status, details = verify_numbers_against_text(c_nums, text)
    assert status == "mismatch"
    assert len(details) > 0

def test_number_missing():
    claim = "Total runtime was reduced by 350 seconds."
    text = "The overall runtime was slightly faster but no time measurements were logged."
    c_nums = extract_numbers_from_text(claim)
    status, details = verify_numbers_against_text(c_nums, text)
    assert status == "missing"
