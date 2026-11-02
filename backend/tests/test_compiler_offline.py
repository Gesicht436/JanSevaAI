"""
Unit Tests for Offline LLM Compilation and Verification Retry Loop (P0.4)
Ensures offline compilation works with a mocked LLM client and zero network dependencies.
"""

import pytest
from typing import Any, Dict, List
from backend.app.compiler.retry_loop import compile_scheme
from backend.app.models.criteria import CriteriaPayload


class MockLLMClient:
    def __init__(self, responses: List[Dict[str, Any]]):
        self.responses = list(responses)
        self.call_count = 0
        self.model = "mock-llm-model"

    def generate_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        if self.call_count < len(self.responses):
            res = self.responses[self.call_count]
            self.call_count += 1
            return res
        raise RuntimeError("Mock LLM ran out of responses")


def test_offline_llm_compilation_success_on_first_try():
    scheme_input = {
        "name": "Youth Skill Scheme",
        "sections": {
            "eligibility": [
                "Applicant must be between 18 and 35 years of age.",
                "Annual family income must not exceed ₹ 2,50,000."
            ],
            "exclusions": [
                "Government employees are not eligible."
            ],
            "documents_required": [
                "Aadhaar Card"
            ]
        }
    }

    mock_response = {
        "criteria": [
            {
                "id": "c1",
                "kind": "requirement",
                "group_id": 1,
                "field": "age",
                "operator": "between",
                "value": [18, 35],
                "origin": "text",
                "source_section": "eligibility",
                "source_line": 0,
                "source_quote": "between 18 and 35 years",
                "quote_verified": False,
                "note": "Age requirement"
            },
            {
                "id": "c2",
                "kind": "requirement",
                "group_id": 2,
                "field": "annual_family_income_inr",
                "operator": "lte",
                "value": 250000,
                "origin": "text",
                "source_section": "eligibility",
                "source_line": 1,
                "source_quote": "income must not exceed ₹ 2,50,000",
                "quote_verified": False,
                "note": "Income requirement"
            },
            {
                "id": "c3",
                "kind": "exclusion",
                "group_id": 3,
                "field": "is_govt_employee",
                "operator": "is_true",
                "value": True,
                "origin": "text",
                "source_section": "exclusions",
                "source_line": 0,
                "source_quote": "Government employees are not eligible",
                "quote_verified": False,
                "note": "Exclusion for govt workers"
            }
        ],
        "required_documents": [
            {
                "type": "aadhaar",
                "text": "Aadhaar Card",
                "source_line": 0
            }
        ]
    }

    mock_client = MockLLMClient([mock_response])
    result = compile_scheme(scheme_input, llm_client=mock_client, max_attempts=3)

    assert result["status"] == "compiled"
    assert result["verified_ratio"] == 1.0
    assert result["evaluable_ratio"] == 1.0
    assert len(result["criteria"]) == 3
    assert all(c["quote_verified"] is True for c in result["criteria"])


def test_offline_llm_compilation_retry_loop_corrects_hallucination():
    scheme_input = {
        "name": "Youth Skill Scheme",
        "sections": {
            "eligibility": [
                "Applicant must be between 18 and 35 years of age."
            ],
            "exclusions": [],
            "documents_required": []
        }
    }

    # Attempt 1: Fabricated age number (e.g. 21 instead of 18)
    bad_response = {
        "criteria": [
            {
                "id": "c1", "kind": "requirement", "group_id": 1, "field": "age",
                "operator": "between", "value": [21, 35], "origin": "text",
                "source_section": "eligibility", "source_line": 0,
                "source_quote": "between 18 and 35 years", "quote_verified": False
            }
        ],
        "required_documents": []
    }

    # Attempt 2: Corrected response
    good_response = {
        "criteria": [
            {
                "id": "c1", "kind": "requirement", "group_id": 1, "field": "age",
                "operator": "between", "value": [18, 35], "origin": "text",
                "source_section": "eligibility", "source_line": 0,
                "source_quote": "between 18 and 35 years", "quote_verified": False
            }
        ],
        "required_documents": []
    }

    mock_client = MockLLMClient([bad_response, good_response])
    result = compile_scheme(scheme_input, llm_client=mock_client, max_attempts=3)

    assert mock_client.call_count == 2, "Retry loop should attempt correction"
    assert result["status"] == "compiled"
    assert result["verified_ratio"] == 1.0


def test_offline_llm_compilation_fallback_for_uncovered_clause():
    scheme_input = {
        "name": "General Scheme",
        "sections": {
            "eligibility": [
                "Must be a registered handloom weaver in district society."
            ],
            "exclusions": [],
            "documents_required": []
        }
    }

    # Model returns empty or fails to compile
    empty_response = {
        "criteria": [],
        "required_documents": []
    }

    mock_client = MockLLMClient([empty_response, empty_response, empty_response])
    result = compile_scheme(scheme_input, llm_client=mock_client, max_attempts=3)

    # Should fall back to an unverifiable source-verified criterion
    assert result["status"] == "partial"
    assert len(result["criteria"]) == 1
    fallback = result["criteria"][0]
    assert fallback["operator"] == "unverifiable"
    assert fallback["field"] is None
    assert fallback["quote_verified"] is True
    assert "handloom weaver" in fallback["source_quote"].lower()
