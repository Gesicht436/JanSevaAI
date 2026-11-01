"""
JanSeva AI - Headless Command Line Interface
Usage:
    python -m backend.cli compile [--slugs=...] [--force]
    python -m backend.cli report --profile=profile.json
"""

import argparse
from collections import Counter
import json
import sys

from backend.app.models.profile import CitizenProfile
from backend.app.evaluator.engine import MatchEngine
from backend.app.services.db import get_db_connection


def run_compile(args: argparse.Namespace) -> int:
    from backend.app.compiler.seed_criteria import compile_all_schemes
    print("Compiling criteria for all schemes in Datasets/schemes.db...")
    count = compile_all_schemes()
    print(f"Compilation complete: {count} verified criteria compiled.")
    return 0


def run_report(args: argparse.Namespace) -> int:
    with open(args.profile, "r", encoding="utf-8") as f:
        profile_data = json.load(f)
    profile = CitizenProfile(**profile_data)
    profile.confirmed = True

    conn = get_db_connection()
    engine = MatchEngine(conn)
    res = engine.evaluate_profile(profile)

    print("\n================ JANSEVA AI MATCH REPORT ================")
    print(f"Citizen: Age {profile.age}, State: {profile.state_ut}, Qual: {profile.qualification}")
    print(f"Sector: {profile.current_sector}, Intent: {profile.benefit_intent}")
    print("---------------------------------------------------------")
    print(f"Eligible Schemes:        {res.counts.eligible}")
    print(f"Needs More Information:  {res.counts.needs_more_info}")
    print(f"Ineligible Schemes:      {res.counts.ineligible}")
    print(f"Closed Schemes:          {res.counts.closed}")
    print(f"High-Leverage Fields:    {', '.join(res.followup_fields)}")

    print("\nTop 5 Eligible Schemes:")
    for s in res.results.eligible[:5]:
        print(f" - [{s.slug}] {s.name} (Verified: {s.verified_ratio:.0%})")
        print(f"   Official Portal: {s.myscheme_url}")
        print(f"   Required Docs: {len(s.required_documents)} | Dept Prereqs: {len(s.specialized_criteria)}")

    conn.close()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m backend.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    compile_cmd = subparsers.add_parser("compile", help="Compile catalog criteria")
    compile_cmd.add_argument("--force", action="store_true", help="Force recompilation")

    report_cmd = subparsers.add_parser("report", help="Evaluate profile from JSON file")
    report_cmd.add_argument("--profile", required=True, help="Path to JSON file")

    args = parser.parse_args()
    if args.command == "compile":
        sys.exit(run_compile(args))
    elif args.command == "report":
        sys.exit(run_report(args))


if __name__ == "__main__":
    main()
