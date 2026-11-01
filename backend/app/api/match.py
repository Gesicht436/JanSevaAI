"""
Two-Stage Scheme Matching API
"""

import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from ..evaluator.engine import MatchEngine
from ..models.match import MatchRequest, MatchResponse
from ..services.db import get_db

router = APIRouter()


@router.post("/match", response_model=MatchResponse)
def match_schemes(req: MatchRequest, db: sqlite3.Connection = Depends(get_db)):
    # Rule E9: Citizen must explicitly confirm the extracted facts
    if not req.profile.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Rule E9 violation: Profile must be confirmed by the citizen before running scheme match."
        )

    engine = MatchEngine(db)
    response = engine.evaluate_profile(
        profile=req.profile,
        previous_unlocked_slugs=req.previous_unlocked_slugs
    )

    unlocked_count = sum(1 for s in response.results.eligible if s.unlocked_in_this_round)
    if unlocked_count > 0:
        response.unlock_summary = f"🎉 {unlocked_count} new scheme{'s' if unlocked_count > 1 else ''} unlocked based on your updated details!"

    return response
