"""
Grounded Explanation API
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from ..evaluator.engine import MatchEngine
from ..models.match import ExplainRequest, ExplainResponse
from ..services.db import get_db
from ..services.llm import generate_grounded_explanation

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain_scheme(req: ExplainRequest, db: sqlite3.Connection = Depends(get_db)):
    engine = MatchEngine(db)
    res = engine.evaluate_profile(req.profile)

    target_scheme = None
    for group in (res.results.eligible, res.results.needs_more_info, res.results.ineligible, res.results.closed):
        for s in group:
            if s.slug == req.slug:
                target_scheme = s
                break
        if target_scheme:
            break

    if not target_scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.slug}' not found.")

    explanation = generate_grounded_explanation(
        scheme_name=target_scheme.name,
        verdict=target_scheme.verdict,
        criteria_results=[c.model_dump() for c in target_scheme.criteria_results],
        benefit_snippet=target_scheme.benefit_snippet,
        contextual_reason=target_scheme.contextual_match_reason
    )

    citations = [c.quote for c in target_scheme.criteria_results if c.quote_verified]

    return ExplainResponse(
        slug=target_scheme.slug,
        scheme_name=target_scheme.name,
        verdict=target_scheme.verdict,
        explanation=explanation,
        source_citations=citations[:5],
        missing_critical_rules=target_scheme.missing_fields
    )
