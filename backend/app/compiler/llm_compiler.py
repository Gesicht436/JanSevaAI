"""
LLM Structured Criteria Compiler
Compiles arbitrary natural language eligibility text into typed criteria with strict schema.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from ..models.criteria import CriteriaPayload

PROMPT_VERSION = "criteria-v2"

_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "criteria": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "id": {"type": "STRING"},
                    "kind": {"type": "STRING", "enum": ["requirement", "exclusion"]},
                    "group_id": {"type": "INTEGER"},
                    "field": {
                        "type": "STRING",
                        "nullable": True,
                        "enum": [
                            "state_ut", "age", "gender", "caste_category", "residence",
                            "qualification", "marital_status", "employment_status",
                            "has_work_experience", "years_of_experience", "current_sector",
                            "aspiring_sector", "benefit_intent", "is_farmer", "land_holding_acres",
                            "is_student", "is_bpl", "is_minority", "is_differently_abled",
                            "disability_percentage", "is_govt_employee", "annual_family_income_inr",
                            "documents_held"
                        ]
                    },
                    "operator": {
                        "type": "STRING",
                        "enum": [
                            "eq", "ne", "in", "not_in", "gte", "lte", "between",
                            "is_true", "is_false", "has_document", "lacks_document",
                            "gte_qualification", "sector_in", "intent_matches", "unverifiable"
                        ]
                    },
                    "value": {
                        "anyOf": [
                            {"type": "STRING"}, {"type": "NUMBER"}, {"type": "BOOLEAN"},
                            {"type": "ARRAY", "items": {"type": "STRING"}}, {"type": "NULL"}
                        ]
                    },
                    "origin": {"type": "STRING", "enum": ["text"]},
                    "source_section": {"type": "STRING", "enum": ["eligibility", "exclusions"]},
                    "source_line": {"type": "INTEGER"},
                    "source_quote": {"type": "STRING"},
                    "quote_verified": {"type": "BOOLEAN"},
                    "note": {"type": "STRING", "nullable": True}
                },
                "required": [
                    "id", "kind", "group_id", "field", "operator", "value", "origin",
                    "source_section", "source_line", "source_quote"
                ]
            }
        },
        "required_documents": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "type": {"type": "STRING", "nullable": True},
                    "text": {"type": "STRING"},
                    "source_line": {"type": "INTEGER"}
                },
                "required": ["type", "text", "source_line"]
            }
        }
    },
    "required": ["criteria", "required_documents"]
}


def compile_prompt(
    scheme_name: str,
    eligibility: List[str],
    exclusions: List[str],
    documents: List[str],
    previous_problems: Optional[List[Dict[str, Any]]] = None
) -> Tuple[str, str]:
    system = (
        "You convert government welfare scheme source lines into typed citizen criteria. "
        "Create at least one criterion for every line. Use exact source_line indices and verbatim source_quote fragments. "
        "Do not invent facts or convert units. Alternatives joined by 'or' share group_id. "
        "Use operator='unverifiable' with a concise note when the rule cannot be represented by profile fields."
    )
    sections = {
        "scheme_name": scheme_name,
        "eligibility": eligibility,
        "exclusions": exclusions,
        "documents_required": documents
    }
    user_payload = {"sections": sections}
    if previous_problems:
        user_payload["verification_problems_to_fix"] = previous_problems

    return system, json.dumps(user_payload, ensure_ascii=False)


def compile_once(
    llm_client: Any,
    scheme_name: str,
    eligibility: List[str],
    exclusions: List[str],
    documents: List[str],
    previous_problems: Optional[List[Dict[str, Any]]] = None
) -> CriteriaPayload:
    system, user = compile_prompt(scheme_name, eligibility, exclusions, documents, previous_problems)
    data = llm_client.generate_json(system, user, _SCHEMA)
    return CriteriaPayload.model_validate(data)


class LLMCompilerClient:
    """Wrapper adapting repository LLM providers for offline structured criteria compilation."""
    def __init__(self, model: Optional[str] = None):
        from ..config import settings
        self.model = model or settings.GEMINI_MODEL

    def generate_json(self, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        from ..services.llm import call_llm
        output = call_llm(system, user, response_schema=schema, temperature=0.0)
        if not output:
            raise RuntimeError("LLM compiler unavailable: API returned empty response or credentials unconfigured.")
        cleaned = re.sub(r"^```(?:json)?", "", output.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)

