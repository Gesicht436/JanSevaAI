"""
Unit Tests for Kleene Three-Valued Logic and Engine Performance
"""

import time
import pytest
from backend.app.models.profile import CitizenProfile
from backend.app.evaluator.operators import evaluate_operator
from backend.app.evaluator.engine import MatchEngine
from backend.app.services.db import get_db_connection


def test_operators_numeric():
    profile = CitizenProfile(age=26, annual_family_income_inr=180000)
    assert evaluate_operator("gte", 18, profile.age, profile, "requirement") == "pass"
    assert evaluate_operator("gte", 35, profile.age, profile, "requirement") == "fail"
    assert evaluate_operator("between", [20, 30], profile.age, profile, "requirement") == "pass"
    assert evaluate_operator("lte", 250000, profile.annual_family_income_inr, profile, "requirement") == "pass"


def test_operator_qualification_hierarchy():
    profile_grad = CitizenProfile(qualification="graduate")
    assert evaluate_operator("gte_qualification", "12th_pass", profile_grad.qualification, profile_grad) == "pass"
    assert evaluate_operator("gte_qualification", "graduate", profile_grad.qualification, profile_grad) == "pass"
    assert evaluate_operator("gte_qualification", "postgraduate", profile_grad.qualification, profile_grad) == "fail"


def test_operator_sectors_and_intent():
    profile_it = CitizenProfile(current_sector="it_tech", benefit_intent="credit_loan")
    assert evaluate_operator("sector_in", ["it_tech", "services_retail"], profile_it.current_sector, profile_it) == "pass"
    assert evaluate_operator("sector_in", ["agriculture"], profile_it.current_sector, profile_it) == "fail"
    assert evaluate_operator("intent_matches", "credit_loan", profile_it.benefit_intent, profile_it) == "pass"


def test_operator_exclusions_behavior():
    profile_govt = CitizenProfile(is_govt_employee=True)
    # Exclusion triggers: true -> fail!
    assert evaluate_operator("is_true", True, profile_govt.is_govt_employee, profile_govt, "exclusion") == "fail"

    profile_clean = CitizenProfile(is_govt_employee=False)
    # Exclusion does not trigger: false -> pass!
    assert evaluate_operator("is_true", True, profile_clean.is_govt_employee, profile_clean, "exclusion") == "pass"


def test_engine_performance_under_50ms():
    conn = get_db_connection()
    engine = MatchEngine(conn)
    profile = CitizenProfile(
        name="Tester",
        state_ut="Gujarat",
        age=26,
        gender="male",
        qualification="graduate",
        current_sector="it_tech",
        annual_family_income_inr=150000,
        confirmed=True
    )

    start = time.perf_counter()
    res = engine.evaluate_profile(profile)
    latency_ms = (time.perf_counter() - start) * 1000

    assert latency_ms < 50.0, f"MatchEngine took {latency_ms:.2f}ms (must be < 50ms)"
    assert res.counts.eligible + res.counts.needs_more_info + res.counts.ineligible + res.counts.closed == 200
    assert len(res.results.eligible[0].myscheme_url) > 0
    assert "myscheme.gov.in" in res.results.eligible[0].myscheme_url
    assert isinstance(res.results.eligible[0].required_documents, list)
    conn.close()
