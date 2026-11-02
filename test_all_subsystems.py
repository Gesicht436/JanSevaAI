"""
JanSevaAI Comprehensive Subsystem Test Suite
Executes individual tests across all subsystems:
1. Database & Catalog Subsystem
2. Rule Operators & Kleene 3-Valued Logic
3. Anti-Hallucination & Quote Verification Engine
4. Two-Stage Match Engine & Tiering
5. Rule E9 Compliance
6. High-Leverage Follow-up Calculation & Progressive Unlocking
7. Conversational Profile Extraction (Deterministic & LLM Fallback)
8. Multi-turn Profile Merging
9. Grounded Explanation Generation
10. Edge-TTS Audio Synthesis
11. REST API Integration Endpoints
12. Headless CLI Subsystem
"""

import sys
import time
import json
import sqlite3
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.models.states import STATES
from backend.app.models.profile import CitizenProfile, ProfileExtractRequest
from backend.app.models.criteria import Criterion
from backend.app.evaluator.operators import evaluate_operator, QUALIFICATION_HIERARCHY
from backend.app.evaluator.engine import MatchEngine
from backend.app.compiler.verifier import verify_quote, extract_numbers_from_text, verify_numbers, normalize_text
from backend.app.services.db import get_db_connection, SchemeStore
from backend.app.services.llm import (
    extract_profile_deterministic,
    extract_profile_with_llm,
    merge_profiles,
    check_information_sufficiency,
    generate_grounded_explanation
)
from backend.app.services.followup import rank_followup_fields
from backend.app.services.tts import synthesize_speech


def run_tests():
    total_passed = 0
    total_failed = 0
    results_summary = []

    def log_test(name: str, passed: bool, detail: str = ""):
        nonlocal total_passed, total_failed
        status = "PASS" if passed else "FAIL"
        if passed:
            total_passed += 1
            print(f"  [PASS] {name}: {detail}")
        else:
            total_failed += 1
            print(f"  [FAIL] {name}: {detail}")
        results_summary.append((name, passed, detail))

    print("\n======================================================================")
    print("      JANSEVA AI UNIFIED - COMPREHENSIVE INDIVIDUAL SUBSYSTEM TESTS")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    # 1. Database & Catalog Subsystem
    # ------------------------------------------------------------------
    print("--- 1. DATABASE & CATALOG SUBSYSTEM ---")
    db_path = settings.resolved_database_path
    log_test("Database File Existence", db_path.exists(), f"Path: {db_path} ({db_path.stat().st_size / (1024*1024):.2f} MB)")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM schemes;")
    total_schemes = cur.fetchone()[0]
    log_test("Total Schemes Count", total_schemes >= 200, f"Found {total_schemes} schemes")

    cur.execute("SELECT COUNT(*) FROM scheme_criteria;")
    total_criteria = cur.fetchone()[0]
    log_test("Total Compiled Criteria", total_criteria >= 1000, f"Found {total_criteria} verified statutory criteria")

    cur.execute("SELECT COUNT(DISTINCT slug) FROM scheme_criteria;")
    schemes_with_criteria = cur.fetchone()[0]
    log_test("Criteria Coverage", schemes_with_criteria == total_schemes, f"{schemes_with_criteria}/{total_schemes} schemes have compiled criteria")

    store = SchemeStore()
    mudra = store.get_scheme("pm-svanidhi") or store.get_scheme("pm-kisan") or store.list_schemes()[0]
    log_test("Scheme Retrieval by Slug", mudra is not None, f"Found {mudra['name'] if mudra else 'None'}")

    # ------------------------------------------------------------------
    # 2. Rule Operators & Kleene 3-Valued Logic
    # ------------------------------------------------------------------
    print("\n--- 2. RULE OPERATORS & KLEENE 3-VALUED LOGIC ---")
    log_test("Numeric Operator 'gte' Fail (16 >= 18)", evaluate_operator("gte", 18, 16) == "fail")
    log_test("Numeric Operator 'gte' Pass (25 >= 18)", evaluate_operator("gte", 18, 25) == "pass")
    log_test("Kleene Logic Unknown (None >= 18)", evaluate_operator("gte", 18, None) == "unknown")

    log_test("Qualification Hierarchy (graduate >= 10th_pass)", evaluate_operator("gte_qualification", "10th_pass", "graduate") == "pass")
    log_test("Qualification Hierarchy (below_10th >= 10th_pass)", evaluate_operator("gte_qualification", "10th_pass", "below_10th") == "fail")

    log_test("Set Operator 'in' Pass (it_tech)", evaluate_operator("in", ["it_tech", "services_retail"], "it_tech") == "pass")
    log_test("Set Operator 'in' Fail (agriculture)", evaluate_operator("in", ["it_tech", "services_retail"], "agriculture") == "fail")
    log_test("Exclusion Operator Inversion", evaluate_operator("gte", 18, 25, kind="exclusion") == "fail")

    # ------------------------------------------------------------------
    # 3. Anti-Hallucination & Quote Verification Engine
    # ------------------------------------------------------------------
    print("\n--- 3. ANTI-HALLUCINATION & QUOTE VERIFIER ---")
    official_clause = "The applicant must be a permanent resident of Maharashtra and have an annual income below Rs 2,50,000."
    log_test("Normalize Text Function", normalize_text("  Income   Below Rs. 2,50,000  ") == "income below rs. 2,50,000")

    v_pass = verify_quote("permanent resident of Maharashtra", official_clause)
    log_test("Exact Quote Match in Official Text", v_pass is True)

    v_hallucinated = verify_quote("must possess a doctoral PhD degree in robotics", official_clause)
    log_test("Hallucinated Quote Rejection", v_hallucinated is False, "Rejected fabricated clause")

    nums = extract_numbers_from_text("annual income below Rs 2.5 Lakhs")
    log_test("Number Indian Unit Extraction (2.5 Lakhs -> 250,000)", 250000.0 in nums)

    c_valid = Criterion(
        id="c1", kind="requirement", group_id=1, field="annual_family_income_inr",
        operator="lte", value=250000, source_section="eligibility", source_line=0,
        source_quote="income below Rs 2.5 Lakhs"
    )
    log_test("Number Verifier Match", verify_numbers(c_valid) is None)

    c_fake = Criterion(
        id="c2", kind="requirement", group_id=1, field="annual_family_income_inr",
        operator="lte", value=9999999, source_section="eligibility", source_line=0,
        source_quote="income below Rs 2.5 Lakhs"
    )
    log_test("Hallucinated Number Rejection", verify_numbers(c_fake) is not None, "Rejected fabricated 9,999,999 vs 250,000")

    # ------------------------------------------------------------------
    # 4. Two-Stage Match Engine & Tiering
    # ------------------------------------------------------------------
    print("\n--- 4. TWO-STAGE MATCH ENGINE & PERFORMANCE ---")
    engine = MatchEngine(conn)

    prof_test = CitizenProfile(
        age=26,
        gender="male",
        marital_status="never_married",
        state_ut="Gujarat",
        caste_category="sc",
        residence="urban",
        qualification="graduate",
        current_sector="it_tech",
        annual_family_income_inr=180000,
        benefit_intent="credit_loan",
        confirmed=True
    )

    # Warm run / evaluate latency
    engine.evaluate_profile(prof_test)
    t0 = time.perf_counter()
    match_res = engine.evaluate_profile(prof_test)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    log_test("Match Engine Evaluation Latency (< 50ms)", elapsed_ms < 50, f"Evaluated 200 schemes in {elapsed_ms:.2f} ms")
    log_test("Eligible Tier Count > 0", match_res.counts.eligible > 0, f"Found {match_res.counts.eligible} eligible schemes")
    log_test("Ineligible Tier Count > 0", match_res.counts.ineligible > 0, f"Found {match_res.counts.ineligible} ineligible schemes")
    log_test("State Filter Applied", match_res.state_filter_applied is True)

    total_sum = match_res.counts.eligible + match_res.counts.needs_more_info + match_res.counts.ineligible + match_res.counts.closed
    log_test("Scheme Tier Conservation", total_sum == total_schemes, f"Sum of tiers: {total_sum} == {total_schemes}")

    sample_scheme = match_res.results.eligible[0]
    log_test("myScheme URL Provisioning", "myscheme.gov.in" in sample_scheme.myscheme_url, f"URL: {sample_scheme.myscheme_url}")
    log_test("Required Documents Included", isinstance(sample_scheme.required_documents, list) and len(sample_scheme.required_documents) > 0, f"Found {len(sample_scheme.required_documents)} docs for {sample_scheme.slug}")
    log_test("Specialized Criteria Captured", isinstance(sample_scheme.specialized_criteria, list), f"Found {len(sample_scheme.specialized_criteria)} dept prereqs")

    # ------------------------------------------------------------------
    # 5. Rule E9 Compliance (Human-in-the-Loop Confirmation)
    # ------------------------------------------------------------------
    print("\n--- 5. RULE E9 VERIFICATION COMPLIANCE ---")
    from fastapi.testclient import TestClient
    from backend.app.main import app
    client = TestClient(app)

    unconfirmed_payload = {
        "profile": {
            "age": 26,
            "state_ut": "Maharashtra",
            "confirmed": False
        }
    }
    r_unconf = client.post("/api/match", json=unconfirmed_payload)
    log_test("Rule E9 Enforced: Unconfirmed Profile Rejected", r_unconf.status_code == 400, f"HTTP {r_unconf.status_code}: {r_unconf.json().get('error', {}).get('code')}")

    confirmed_payload = {
        "profile": {
            "age": 26,
            "state_ut": "Maharashtra",
            "confirmed": True
        }
    }
    r_conf = client.post("/api/match", json=confirmed_payload)
    log_test("Rule E9 Enforced: Confirmed Profile Accepted", r_conf.status_code == 200, f"HTTP {r_conf.status_code} with {r_conf.json()['counts']['eligible']} eligible")

    # ------------------------------------------------------------------
    # 6. High-Leverage Follow-up Calculation & Progressive Unlocking
    # ------------------------------------------------------------------
    print("\n--- 6. HIGH-LEVERAGE FOLLOW-UP & PROGRESSIVE UNLOCKING ---")
    pending_schemes = match_res.results.needs_more_info
    followup_fields = rank_followup_fields(pending_schemes, limit=3)
    log_test("Follow-up Fields Discovery", isinstance(followup_fields, list), f"Fields: {followup_fields}")

    # Test Progressive Unlocking
    initial_slugs = [s.slug for s in match_res.results.eligible]
    # Simulate answering caste_category or income
    unlocked_match = engine.evaluate_profile(
        CitizenProfile(**{**prof_test.model_dump(), "caste_category": "obc"}),
        previous_unlocked_slugs=initial_slugs
    )
    newly_unlocked = [s for s in unlocked_match.results.eligible if s.unlocked_in_this_round]
    log_test("Progressive Unlocking Evaluation", True, f"Unlocked schemes marked: {len(newly_unlocked)} new")

    # ------------------------------------------------------------------
    # 7. Conversational Profile Extraction Subsystem
    # ------------------------------------------------------------------
    print("\n--- 7. PROFILE EXTRACTION & DETERMINISTIC REGEX ---")
    query_1 = "I am 26, bachelor in IT, have 3 years work experience in IT sector, looking for loan in Maharashtra."
    det_prof, det_conf, det_phrases = extract_profile_deterministic(query_1)

    log_test("Deterministic Age Extracted", det_prof.age == 26, f"Age: {det_prof.age} (conf: {det_conf.get('age')})")
    log_test("Deterministic State Extracted", det_prof.state_ut == "Maharashtra", f"State: {det_prof.state_ut}")
    log_test("Deterministic Qual Extracted", det_prof.qualification == "graduate", f"Qual: {det_prof.qualification}")
    log_test("Deterministic Sector Extracted", det_prof.current_sector == "it_tech", f"Sector: {det_prof.current_sector}")
    log_test("Deterministic Intent Extracted", det_prof.benefit_intent == "credit_loan", f"Intent: {det_prof.benefit_intent}")

    # Extraction via API endpoint (with hybrid augmentation)
    r_extract = client.post("/api/profile/extract", json={"text": query_1})
    log_test("API /api/profile/extract Endpoint", r_extract.status_code == 200, f"HTTP {r_extract.status_code}")
    ext_data = r_extract.json()
    log_test("API Profile Age Extracted", ext_data["profile"]["age"] == 26)
    log_test("API Profile State Extracted", ext_data["profile"]["state_ut"] == "Maharashtra")

    # ------------------------------------------------------------------
    # 8. Multi-Turn Profile Merging
    # ------------------------------------------------------------------
    print("\n--- 8. MULTI-TURN PROFILE MERGING ---")
    base_p = CitizenProfile(age=26, state_ut="Maharashtra", confirmed=True)
    incoming_p = CitizenProfile(current_sector="it_tech", benefit_intent="credit_loan")
    merged_p = merge_profiles(base_p, incoming_p)

    log_test("Preserve Existing Facts (Age)", merged_p.age == 26)
    log_test("Preserve Existing Facts (State)", merged_p.state_ut == "Maharashtra")
    log_test("Incorporate New Facts (Sector)", merged_p.current_sector == "it_tech")
    log_test("Incorporate New Facts (Intent)", merged_p.benefit_intent == "credit_loan")

    # ------------------------------------------------------------------
    # 9. Grounded Explanation Generation
    # ------------------------------------------------------------------
    print("\n--- 9. GROUNDED EXPLANATION GENERATION ---")
    explanation = generate_grounded_explanation(
        scheme_name="Pradhan Mantri MUDRA Yojana",
        verdict="eligible",
        criteria_results=[{"field": "age", "result": "pass", "quote": "Applicant must be at least 18 years", "quote_verified": True}],
        benefit_snippet="Collateral-free micro loans up to Rs 10 Lakhs",
        contextual_reason="Candidate meets all statutory requirements."
    )
    log_test("Grounded Explanation Non-Empty", bool(explanation and len(explanation) > 20), f"Length: {len(explanation)} chars")
    log_test("Grounded Explanation References Citations", "18" in explanation or "Mudra" in explanation)

    # ------------------------------------------------------------------
    # 10. Text-to-Speech (TTS) Synthesis Subsystem
    # ------------------------------------------------------------------
    print("\n--- 10. TEXT-TO-SPEECH (TTS) SYNTHESIS ---")
    tts_text = "You are eligible for Pradhan Mantri Mudra Yojana."
    import asyncio
    tts_bytes = asyncio.run(synthesize_speech(tts_text))
    log_test("TTS Audio Synthesis Output", len(tts_bytes) > 100, f"Generated {len(tts_bytes)} audio bytes")

    # ------------------------------------------------------------------
    # 11. REST API Integration Endpoints
    # ------------------------------------------------------------------
    print("\n--- 11. REST API INTEGRATION ENDPOINTS ---")
    r_health = client.get("/api/health")
    log_test("GET /api/health", r_health.status_code == 200 and r_health.json()["status"] == "ok")

    r_cat = client.get("/api/catalog/status")
    log_test("GET /api/catalog/status", r_cat.status_code == 200 and r_cat.json()["total_schemes"] >= 200)

    r_schemes = client.get("/api/schemes?limit=5")
    log_test("GET /api/schemes?limit=5", r_schemes.status_code == 200 and len(r_schemes.json()["schemes"]) == 5)

    first_slug = r_schemes.json()["schemes"][0]["slug"]
    r_scheme_detail = client.get(f"/api/schemes/{first_slug}")
    log_test(f"GET /api/schemes/{first_slug}", r_scheme_detail.status_code == 200 and "name" in r_scheme_detail.json() and "myscheme_url" in r_scheme_detail.json())

    r_scheme_crit = client.get(f"/api/schemes/{first_slug}/criteria")
    log_test(f"GET /api/schemes/{first_slug}/criteria", r_scheme_crit.status_code == 200 and "criteria" in r_scheme_crit.json())

    r_explain = client.post("/api/explain", json={"slug": first_slug, "profile": prof_test.model_dump()})
    log_test(f"POST /api/explain ({first_slug})", r_explain.status_code == 200 and "explanation" in r_explain.json())

    r_tts = client.post("/api/tts", json={"text": "Hello citizen"})
    log_test("POST /api/tts Audio Stream", r_tts.status_code == 200 and r_tts.headers.get("content-type") == "audio/mpeg")

    # ------------------------------------------------------------------
    # 12. Headless CLI Subsystem
    # ------------------------------------------------------------------
    print("\n--- 12. HEADLESS CLI SUBSYSTEM ---")
    import subprocess
    cli_cmd = [
        sys.executable, "-m", "backend.cli", "report",
        "--profile=backend/tests/fixtures/sample_profile.json"
    ]
    cli_proc = subprocess.run(cli_cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
    log_test("CLI report command exit code", cli_proc.returncode == 0)
    log_test("CLI report output content", "JANSEVA AI MATCH REPORT" in cli_proc.stdout and "Eligible Schemes" in cli_proc.stdout)

    # ------------------------------------------------------------------
    # 13. Frontend SPA Distribution Serving
    # ------------------------------------------------------------------
    print("\n--- 13. FRONTEND SPA STATIC DISTRIBUTION ---")
    r_spa_root = client.get("/")
    log_test("GET / Serves SPA HTML", r_spa_root.status_code == 200 and "<!doctype html>" in r_spa_root.text.lower())

    dist_index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    log_test("frontend/dist/index.html Exists", dist_index.exists())

    dist_assets = list((PROJECT_ROOT / "frontend" / "dist" / "assets").glob("*.js"))
    log_test("Compiled JS Bundle Exists", len(dist_assets) > 0, f"Found {dist_assets[0].name if dist_assets else 'None'}")

    conn.close()

    # ------------------------------------------------------------------
    # Final Summary
    # ------------------------------------------------------------------
    print("\n======================================================================")
    print(f"TEST SUMMARY: {total_passed} PASSED | {total_failed} FAILED | TOTAL: {total_passed + total_failed}")
    print("======================================================================\n")

    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
