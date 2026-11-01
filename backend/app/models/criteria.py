"""
Criteria Models & Schemas
"""

from typing import Any, List, Literal, Optional
from pydantic import BaseModel, Field

CriterionKind = Literal["requirement", "exclusion"]
CriterionOperator = Literal[
    "eq", "ne", "in", "not_in", "gte", "lte", "between",
    "is_true", "is_false", "has_document", "lacks_document",
    "gte_qualification", "sector_in", "intent_matches", "unverifiable"
]


class Criterion(BaseModel):
    id: str
    kind: CriterionKind
    group_id: int
    field: Optional[str]
    operator: CriterionOperator
    value: Any = None
    origin: str = "text"
    source_section: str
    source_line: int
    source_quote: str
    quote_verified: bool = False
    note: Optional[str] = None


class RequiredDocument(BaseModel):
    type: Optional[str]
    text: str
    source_line: int


class CriteriaPayload(BaseModel):
    criteria: List[Criterion]
    required_documents: List[RequiredDocument] = []


class EvaluationResult(BaseModel):
    verdict: str
    criteria_results: List[dict]
    unknown_count: int
    missing_fields: List[str]
    unverifiable_count: int = 0
    verification_warning: bool = False
