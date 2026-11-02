"""
Matching Response Models
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from .profile import CitizenProfile
from .documents import RequiredDocumentItem


class CriterionResult(BaseModel):
    criterion_id: str
    kind: str
    group_id: int
    field: Optional[str]
    result: str                 # "pass", "fail", "unknown"
    quote: str
    quote_verified: bool
    source_line: int
    source_section: Optional[str] = "eligibility"
    note: Optional[str] = None
    is_specialized: bool = False


class SchemeVerdictResult(BaseModel):
    slug: str
    name: str
    ministry_or_department: str
    level: str
    beneficiary_states: List[str]
    categories: List[str]
    close_date: Optional[str]
    verdict: str                # "eligible", "needs_more_info", "ineligible", "closed"
    benefit_snippet: str
    description: Optional[str] = None
    myscheme_url: str = ""
    required_documents: List[Union[RequiredDocumentItem, str]] = Field(default_factory=list)
    specialized_criteria: List[str] = Field(default_factory=list)
    verified_ratio: float
    contextual_match_reason: Optional[str] = None
    missing_fields: List[str]
    criteria_results: List[CriterionResult]
    unlocked_in_this_round: bool = False
    requires_manual_review: bool = False


class MatchCounts(BaseModel):
    eligible: int = 0
    needs_more_info: int = 0
    ineligible: int = 0
    closed: int = 0
    excluded_by_state: int = 0


class MatchResultsGrouped(BaseModel):
    eligible: List[SchemeVerdictResult] = []
    needs_more_info: List[SchemeVerdictResult] = []
    ineligible: List[SchemeVerdictResult] = []
    closed: List[SchemeVerdictResult] = []


class MatchResponse(BaseModel):
    state_filter_applied: bool
    counts: MatchCounts
    followup_fields: List[str]
    unlock_summary: Optional[str] = None
    results: MatchResultsGrouped


class MatchRequest(BaseModel):
    profile: CitizenProfile
    previous_unlocked_slugs: Optional[List[str]] = None


class ExplainRequest(BaseModel):
    slug: str
    profile: CitizenProfile


class ExplainResponse(BaseModel):
    slug: str
    scheme_name: str
    verdict: str
    explanation: str
    source_citations: List[str]
    missing_critical_rules: List[str] = []
