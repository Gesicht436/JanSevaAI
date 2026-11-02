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
        caste_category="sc",
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


def test_three_valued_aggregation_conservative():
    """
    P0.1 Acceptance Tests:
    1. One mandatory group with one pass => eligible, provided every other mandatory group also passes.
    2. One mandatory group with all alternatives fail => ineligible.
    3. One mandatory group with unknown and no pass/fail certainty => needs-more-info/unresolved.
    4. One passing mandatory group plus a second unknown mandatory group => not eligible.
    5. field=None, operator='unverifiable' => not eligible.
    6. Unsupported operator => not eligible.
    7. quote_verified=False => criterion cannot pass or fail; it is unknown.
    8. Empty criteria for a scheme => not eligible.
    9. Exclusion criteria retain the correct inversion semantics.
    10. Mixed pass/fail/unknown alternatives are tested against the documented OR semantics.
    """
    conn = get_db_connection()
    engine = MatchEngine(conn)
    dummy_scheme = {
        "slug": "test-scheme",
        "name": "Test Scheme",
        "ministry": "Ministry of Social Justice",
        "department": None,
        "level": "Central",
        "beneficiary_states": "[]",
        "all_states": 1,
        "categories": "[]",
        "close_date": None,
        "brief_description": "Test scheme description",
        "verified_ratio": 1.0
    }

    # Case 8: Empty criteria => needs_more_info, never eligible
    profile = CitizenProfile(age=25, confirmed=True)
    res_empty = engine.evaluate_single_scheme(dummy_scheme, [], [], profile)
    assert res_empty.verdict == "needs_more_info", "Empty criteria must yield needs_more_info"

    # Case 1: One mandatory group with one pass => eligible
    crit_pass = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
        "operator": "gte", "value": 18, "source_section": "eligibility", "source_line": 0,
        "source_quote": "age 18 and above", "quote_verified": 1
    }]
    res_pass = engine.evaluate_single_scheme(dummy_scheme, crit_pass, [], profile)
    assert res_pass.verdict == "eligible"

    # Case 2: One mandatory group with all alternatives fail => ineligible
    crit_fail = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
        "operator": "gte", "value": 60, "source_section": "eligibility", "source_line": 0,
        "source_quote": "age 60 and above", "quote_verified": 1
    }]
    res_fail = engine.evaluate_single_scheme(dummy_scheme, crit_fail, [], profile)
    assert res_fail.verdict == "ineligible"

    # Case 3: One mandatory group with unknown => needs_more_info
    crit_unknown = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "annual_family_income_inr",
        "operator": "lte", "value": 200000, "source_section": "eligibility", "source_line": 0,
        "source_quote": "income below 2 lakh", "quote_verified": 1
    }]
    res_unknown = engine.evaluate_single_scheme(dummy_scheme, crit_unknown, [], profile)
    assert res_unknown.verdict == "needs_more_info"
    assert "annual_family_income_inr" in res_unknown.missing_fields

    # Case 4: One passing mandatory group + second unknown mandatory group => not eligible
    crit_pass_and_unknown = [
        {
            "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
            "operator": "gte", "value": 18, "source_section": "eligibility", "source_line": 0,
            "source_quote": "age 18 and above", "quote_verified": 1
        },
        {
            "criterion_id": "c2", "group_id": 2, "kind": "requirement", "field": "annual_family_income_inr",
            "operator": "lte", "value": 200000, "source_section": "eligibility", "source_line": 1,
            "source_quote": "income below 2 lakh", "quote_verified": 1
        }
    ]
    res_multi = engine.evaluate_single_scheme(dummy_scheme, crit_pass_and_unknown, [], profile)
    assert res_multi.verdict == "needs_more_info", "Passing group + unknown group must not be eligible"

    # Case 5: field=None, operator='unverifiable' => not eligible (needs_more_info)
    crit_unverifiable = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": None,
        "operator": "unverifiable", "value": None, "source_section": "eligibility", "source_line": 0,
        "source_quote": "Must have satisfactory character certificate", "quote_verified": 1
    }]
    res_unv = engine.evaluate_single_scheme(dummy_scheme, crit_unverifiable, [], profile)
    assert res_unv.verdict == "needs_more_info"
    assert res_unv.requires_manual_review is True

    # Case 6: Unsupported operator => not eligible
    crit_unsupported_op = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
        "operator": "some_future_op", "value": 25, "source_section": "eligibility", "source_line": 0,
        "source_quote": "age requirement", "quote_verified": 1
    }]
    res_bad_op = engine.evaluate_single_scheme(dummy_scheme, crit_unsupported_op, [], profile)
    assert res_bad_op.verdict == "needs_more_info"

    # Case 7: quote_verified=False => criterion cannot pass or fail; it is unknown
    crit_unverified_quote = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
        "operator": "gte", "value": 18, "source_section": "eligibility", "source_line": 0,
        "source_quote": "age 18", "quote_verified": 0
    }]
    res_unver_q = engine.evaluate_single_scheme(dummy_scheme, crit_unverified_quote, [], profile)
    assert res_unver_q.verdict == "needs_more_info"
    assert res_unver_q.criteria_results[0].result == "unknown"

    # Case 10: Mixed pass/fail/unknown alternatives in OR group
    # Subcase A: [fail, pass] => pass
    crit_or_pass = [
        {"criterion_id": "c1a", "group_id": 1, "kind": "requirement", "field": "age", "operator": "gte", "value": 60, "source_section": "eligibility", "source_line": 0, "source_quote": "q1", "quote_verified": 1},
        {"criterion_id": "c1b", "group_id": 1, "kind": "requirement", "field": "age", "operator": "gte", "value": 18, "source_section": "eligibility", "source_line": 0, "source_quote": "q2", "quote_verified": 1}
    ]
    res_or_pass = engine.evaluate_single_scheme(dummy_scheme, crit_or_pass, [], profile)
    assert res_or_pass.verdict == "eligible"

    # Subcase B: [fail, unknown] => unknown (needs_more_info)
    crit_or_unknown = [
        {"criterion_id": "c1a", "group_id": 1, "kind": "requirement", "field": "age", "operator": "gte", "value": 60, "source_section": "eligibility", "source_line": 0, "source_quote": "q1", "quote_verified": 1},
        {"criterion_id": "c1b", "group_id": 1, "kind": "requirement", "field": "annual_family_income_inr", "operator": "lte", "value": 200000, "source_section": "eligibility", "source_line": 0, "source_quote": "q2", "quote_verified": 1}
    ]
    res_or_unknown = engine.evaluate_single_scheme(dummy_scheme, crit_or_unknown, [], profile)
    assert res_or_unknown.verdict == "needs_more_info"

    conn.close()


def test_state_candidacy_acceptance_cases():
    """
    P0.2 Acceptance Tests:
    - All-India + missing state => state check passes.
    - State-restricted + missing state => needs_more_info, state_ut missing.
    - State-restricted + invalid state => same as missing.
    - State-restricted + matching state => state check passes.
    - State-restricted + nonmatching known state => ineligible only when restriction is grounded in source metadata.
    - No generated state explanation may have quote_verified=True.
    """
    conn = get_db_connection()
    engine = MatchEngine(conn)

    crit_always_pass = [{
        "criterion_id": "c1", "group_id": 1, "kind": "requirement", "field": "age",
        "operator": "gte", "value": 18, "source_section": "eligibility", "source_line": 0,
        "source_quote": "age 18", "quote_verified": 1
    }]

    all_india_scheme = {
        "slug": "all-india-scheme",
        "name": "All India Scheme",
        "ministry": "Ministry of Rural Development",
        "department": None,
        "level": "Central",
        "beneficiary_states": "[]",
        "all_states": 1,
        "categories": "[]",
        "close_date": None,
        "brief_description": "Available across India",
        "verified_ratio": 1.0
    }

    state_restricted_scheme = {
        "slug": "gujarat-scheme",
        "name": "Gujarat Scheme",
        "ministry": "Government of Gujarat",
        "department": None,
        "level": "State",
        "beneficiary_states": '["Gujarat"]',
        "all_states": 0,
        "categories": "[]",
        "close_date": None,
        "brief_description": "Only for Gujarat residents",
        "verified_ratio": 1.0
    }

    # 1. All-India + missing state => passes
    p_no_state = CitizenProfile(age=25, state_ut=None, confirmed=True)
    res1 = engine.evaluate_single_scheme(all_india_scheme, crit_always_pass, [], p_no_state)
    assert res1.verdict == "eligible"
    assert "state_ut" not in res1.missing_fields

    # 2. State-restricted + missing state => needs_more_info, state_ut missing
    res2 = engine.evaluate_single_scheme(state_restricted_scheme, crit_always_pass, [], p_no_state)
    assert res2.verdict == "needs_more_info"
    assert "state_ut" in res2.missing_fields

    # 3. State-restricted + invalid state => needs_more_info, state_ut missing
    # Note: profile model normalizes invalid state to None
    p_invalid_state = CitizenProfile.model_construct(age=25, state_ut="InvalidStateXYZ", confirmed=True)
    res3 = engine.evaluate_single_scheme(state_restricted_scheme, crit_always_pass, [], p_invalid_state)
    assert res3.verdict == "needs_more_info"
    assert "state_ut" in res3.missing_fields

    # 4. State-restricted + matching state => passes
    p_gujarat = CitizenProfile(age=25, state_ut="Gujarat", confirmed=True)
    res4 = engine.evaluate_single_scheme(state_restricted_scheme, crit_always_pass, [], p_gujarat)
    assert res4.verdict == "eligible"

    # 5. State-restricted + nonmatching known state => ineligible
    p_maharashtra = CitizenProfile(age=25, state_ut="Maharashtra", confirmed=True)
    res5 = engine.evaluate_single_scheme(state_restricted_scheme, crit_always_pass, [], p_maharashtra)
    assert res5.verdict == "ineligible"

    # 6. Verify that NO generated state explanation has quote_verified=True
    for r in [res1, res2, res3, res4, res5]:
        for cr in r.criteria_results:
            if cr.criterion_id == "state_scope":
                assert cr.quote_verified is False, "Generated state explanation must never have quote_verified=True"

    conn.close()


def test_document_normalization_and_checklist():
    from backend.app.models.documents import normalize_document_text, RequiredDocumentItem

    # 1. Alias normalization
    assert normalize_document_text("Applicant Aadhaar Card copy") == "aadhaar"
    assert normalize_document_text("Valid Ration card or BPL card") == "ration_card"
    assert normalize_document_text("Income certificate issued by Tehsildar") == "income_certificate"
    assert normalize_document_text("Community / Caste Certificate") == "caste_certificate"
    assert normalize_document_text("Domicile or Residential Certificate") == "domicile_certificate"
    assert normalize_document_text("Bank passbook copy with IFSC") == "bank_passbook"
    assert normalize_document_text("Land revenue records (Patta / 7-12 extract)") == "land_records"
    assert normalize_document_text("UDID or disability certificate") == "disability_certificate"
    assert normalize_document_text("Special engineering accreditation letter") is None

    # 2. Typed document model
    doc_item = RequiredDocumentItem(type=normalize_document_text("Aadhaar Card"), text="Aadhaar Card", source_line=0)
    assert doc_item.type == "aadhaar"
    assert doc_item.text == "Aadhaar Card"
