"""
Unit Tests for Quote Normalization, Numeric Verification, and Coverage
"""

import pytest
from backend.app.compiler.verifier import normalize_text, verify_quote, extract_numbers_from_text, verify_numbers
from backend.app.models.criteria import Criterion


def test_normalize_text():
    raw = "   Applicant  must be an \n Indian Citizen.  "
    assert normalize_text(raw) == "applicant must be an indian citizen."


def test_verify_quote_substring():
    line = "The applicant must be between 18 and 35 years of age at the time of application."
    assert verify_quote("between 18 and 35 years", line) is True
    assert verify_quote("between 20 and 40 years", line) is False


def test_extract_numbers_indian_units():
    text = "Annual income must not exceed Rs. 2.5 Lakh or 1 Crore for special categories."
    numbers = extract_numbers_from_text(text)
    assert 250000.0 in numbers
    assert 10000000.0 in numbers


def test_verify_numbers_hallucination_detection():
    c_valid = Criterion(
        id="c1", kind="requirement", group_id=1, field="annual_family_income_inr",
        operator="lte", value=250000, source_section="eligibility", source_line=0,
        source_quote="income not to exceed Rs. 2.5 Lakh"
    )
    assert verify_numbers(c_valid) is None

    c_hallucinated = Criterion(
        id="c2", kind="requirement", group_id=1, field="annual_family_income_inr",
        operator="lte", value=500000, source_section="eligibility", source_line=0,
        source_quote="income not to exceed Rs. 2.5 Lakh"
    )
    assert verify_numbers(c_hallucinated) is not None
