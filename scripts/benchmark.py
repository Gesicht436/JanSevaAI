"""
JanSevaAI Performance Benchmark Script
Measures:
1. Database file size
2. Cold DB-open time
3. Warm /api/match latency at current catalog size
4. Warm /api/match latency at synthetic scaled dataset (1,000 schemes)
5. Single-scheme /api/explain latency
6. Peak memory allocation during match evaluation
"""

import json
import sqlite3
import tempfile
import time
import tracemalloc
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config import settings
from backend.app.models.profile import CitizenProfile
from backend.app.evaluator.engine import MatchEngine
from backend.app.services.db import open_readonly_connection, get_db_connection


def benchmark_suite():
    print("\n================ JANSEVA AI PERFORMANCE BENCHMARK ================")
    db_path = settings.resolved_database_path
    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"1. Database File Size:        {db_size_mb:.2f} MB ({db_path.stat().st_size:,} bytes)")

    # 2. Cold DB-open time
    cold_times = []
    for _ in range(5):
        t0 = time.perf_counter()
        conn = open_readonly_connection(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM schemes;")
        _ = cur.fetchone()[0]
        cold_times.append((time.perf_counter() - t0) * 1000)
        conn.close()
    avg_cold_ms = sum(cold_times) / len(cold_times)
    print(f"2. Cold DB-Open + Query Time: {avg_cold_ms:.2f} ms (avg of 5 runs)")

    # Warm cached connection
    conn = get_db_connection()
    engine = MatchEngine(conn)
    profile = CitizenProfile(
        state_ut="Gujarat",
        age=26,
        gender="male",
        caste_category="sc",
        qualification="graduate",
        current_sector="it_tech",
        annual_family_income_inr=180000,
        confirmed=True
    )

    # 3. Peak memory during match evaluation
    tracemalloc.start()
    _ = engine.evaluate_profile(profile)
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"3. Peak Memory During /match:  {peak_mem / (1024 * 1024):.2f} MB (Current: {current_mem / (1024 * 1024):.2f} MB)")

    # 4. Warm /api/match latency (200 schemes)
    latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        res = engine.evaluate_profile(profile)
        latencies.append((time.perf_counter() - t0) * 1000)
    avg_match_ms = sum(latencies) / len(latencies)
    min_match_ms = min(latencies)
    max_match_ms = max(latencies)
    print(f"4. Warm /api/match Latency:    {avg_match_ms:.2f} ms (min: {min_match_ms:.2f} ms, max: {max_match_ms:.2f} ms) [200 schemes]")
    print(f"   Breakdown: Eligible={res.counts.eligible}, NeedsMoreInfo={res.counts.needs_more_info}, Ineligible={res.counts.ineligible}, Closed={res.counts.closed}")

    # 5. /api/explain single-scheme latency
    explain_latencies = []
    for _ in range(20):
        t0 = time.perf_counter()
        scheme_res = engine.evaluate_scheme("aspfts12ps", profile)
        explain_latencies.append((time.perf_counter() - t0) * 1000)
    avg_explain_ms = sum(explain_latencies) / len(explain_latencies)
    print(f"5. Single-Scheme Explain Eval: {avg_explain_ms:.2f} ms (avg of 20 runs)")

    # 6. Scaled benchmark with synthetic 1,000 schemes
    print("\nCreating synthetic scaled database with 1,000 schemes...")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        scaled_db_path = Path(tmp.name)

    try:
        # Copy schema from canonical
        src_conn = sqlite3.connect(db_path)
        dst_conn = sqlite3.connect(scaled_db_path)
        src_conn.backup(dst_conn)
        src_conn.close()

        # Multiply schemes 5x to 1,000
        dst_cur = dst_conn.cursor()
        for i in range(1, 5):
            dst_cur.execute(f"""
                INSERT INTO schemes (
                    slug, name, short_title, ministry, department, level,
                    beneficiary_states, all_states, categories, sub_categories,
                    scheme_type, benefit_type, tags, brief_description,
                    close_date, open_date, sections, application_process,
                    source_links, content_hash, fetched_at, list_fetched_at, fetch_strategy
                )
                SELECT 
                    slug || '-scale-{i}', name || ' Scaled {i}', short_title, ministry, department, level,
                    beneficiary_states, all_states, categories, sub_categories,
                    scheme_type, benefit_type, tags, brief_description,
                    close_date, open_date, sections, application_process,
                    source_links, content_hash, fetched_at, list_fetched_at, fetch_strategy
                FROM schemes WHERE slug NOT LIKE '%-scale-%';
            """)
            dst_cur.execute(f"""
                INSERT INTO scheme_criteria (
                    slug, criterion_id, group_id, kind, field, operator, value,
                    source_section, source_line, source_quote, quote_verified, note
                )
                SELECT 
                    slug || '-scale-{i}', criterion_id, group_id, kind, field, operator, value,
                    source_section, source_line, source_quote, quote_verified, note
                FROM scheme_criteria WHERE slug NOT LIKE '%-scale-%';
            """)
        dst_conn.commit()
        dst_cur.execute("SELECT COUNT(*) FROM schemes;")
        total_scaled = dst_cur.fetchone()[0]
        dst_conn.close()

        scaled_ro_conn = open_readonly_connection(scaled_db_path)
        scaled_engine = MatchEngine(scaled_ro_conn)

        scaled_latencies = []
        for _ in range(10):
            t0 = time.perf_counter()
            _ = scaled_engine.evaluate_profile(profile)
            scaled_latencies.append((time.perf_counter() - t0) * 1000)
        avg_scaled_ms = sum(scaled_latencies) / len(scaled_latencies)
        print(f"6. Warm /api/match (1,000 schemes): {avg_scaled_ms:.2f} ms (avg of 10 runs)")
        scaled_ro_conn.close()
    finally:
        scaled_db_path.unlink(missing_ok=True)

    print("===================================================================\n")


if __name__ == "__main__":
    benchmark_suite()
