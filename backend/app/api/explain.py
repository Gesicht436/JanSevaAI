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
    if not req.profile.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Rule E9: Citizen profile must be confirmed before generating explanation."
        )

    engine = MatchEngine(db)
    target_scheme = engine.evaluate_scheme(req.slug, req.profile)

    if not target_scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.slug}' not found.")

    explanation = generate_grounded_explanation(
        scheme_name=target_scheme.name,
        verdict=target_scheme.verdict,
        criteria_results=[c.model_dump() for c in target_scheme.criteria_results],
        benefit_snippet=target_scheme.benefit_snippet,
        contextual_reason=target_scheme.contextual_match_reason
    )

    citations = [c.quote for c in target_scheme.criteria_results if c.quote_verified and c.quote]

    return ExplainResponse(
        slug=target_scheme.slug,
        scheme_name=target_scheme.name,
        verdict=target_scheme.verdict,
        explanation=explanation,
        source_citations=citations[:5],
        missing_critical_rules=target_scheme.missing_fields
    )
