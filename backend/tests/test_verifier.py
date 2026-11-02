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


def test_verify_scheme_criteria_exact_section_and_numeric():
    from backend.app.compiler.verifier import verify_scheme_criteria

    source_lines = [
        {"section_name": "eligibility", "line_index": 0, "line_text": "Applicant must be aged between 18 and 35 years."},
        {"section_name": "eligibility", "line_index": 1, "line_text": "Annual family income must not exceed ₹ 3,00,000."},
        {"section_name": "exclusions", "line_index": 0, "line_text": "Government employees are not eligible for this scheme."}
    ]

    # Valid criteria matching exact line, section, and numbers
    valid_criteria = [
        {
            "id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
            "operator": "between", "value": [18, 35], "source_section": "eligibility",
            "source_line": 0, "source_quote": "aged between 18 and 35 years"
        },
        {
            "id": "c2", "group_id": 2, "kind": "requirement", "field": "annual_family_income_inr",
            "operator": "lte", "value": 300000, "source_section": "eligibility",
            "source_line": 1, "source_quote": "income must not exceed ₹ 3,00,000"
        },
        {
            "id": "c3", "group_id": 3, "kind": "exclusion", "field": "is_govt_employee",
            "operator": "is_true", "value": True, "source_section": "exclusions",
            "source_line": 0, "source_quote": "Government employees are not eligible"
        }
    ]

    all_ok, ratio, issues = verify_scheme_criteria(valid_criteria, source_lines)
    assert all_ok is True
    assert ratio == 1.0
    assert len(issues) == 0

    # Cross-section mismatch: quote from 'exclusions' line 0 claimed under 'eligibility' line 0
    cross_section_criteria = [
        {
            "id": "c_bad", "group_id": 1, "kind": "requirement", "field": "is_govt_employee",
            "operator": "is_true", "value": True, "source_section": "eligibility",
            "source_line": 0, "source_quote": "Government employees are not eligible"
        }
    ]
    ok_cross, ratio_cross, issues_cross = verify_scheme_criteria(cross_section_criteria, source_lines)
    assert ok_cross is False
    assert ratio_cross == 0.0
    assert any("not verbatim" in iss for iss in issues_cross)

    # Line out of range
    out_of_range_criteria = [
        {
            "id": "c_oor", "group_id": 1, "kind": "requirement", "field": "age",
            "operator": "gte", "value": 18, "source_section": "eligibility",
            "source_line": 99, "source_quote": "aged between 18 and 35 years"
        }
    ]
    ok_oor, _, issues_oor = verify_scheme_criteria(out_of_range_criteria, source_lines)
    assert ok_oor is False
    assert any("missing or out of range" in iss for iss in issues_oor)

    # Numeric mismatch
    numeric_mismatch = [
        {
            "id": "c_num", "group_id": 1, "kind": "requirement", "field": "annual_family_income_inr",
            "operator": "lte", "value": 500000, "source_section": "eligibility",
            "source_line": 1, "source_quote": "income must not exceed ₹ 3,00,000"
        }
    ]
    ok_num, _, issues_num = verify_scheme_criteria(numeric_mismatch, source_lines)
    assert ok_num is False
    assert any("numeric value 500000 not found" in iss for iss in issues_num)


def test_indian_number_units_comprehensive():
    sample1 = "Subsidy of ₹ 2.50 Lakh or Rs. 1.25 Crore for units with turnover below 50k"
    nums1 = extract_numbers_from_text(sample1)
    assert 250000.0 in nums1
    assert 12500000.0 in nums1
    assert 50000.0 in nums1

    sample2 = "Minimum 40% disability and age 18 to 60 years"
    nums2 = extract_numbers_from_text(sample2)
    assert 40.0 in nums2
    assert 18.0 in nums2
    assert 60.0 in nums2
