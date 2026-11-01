"""
Two-Stage Hybrid Match Engine (Rules L10, L11, L14, L19)
Stage 1: Deterministic Hard-Gate Pruning (< 15ms)
Stage 2: Contextual Nuance Evaluation, Progressive Unlocking & Follow-up Ranking
"""

from collections import defaultdict
import datetime
import json
import sqlite3
from typing import Any, Dict, List, Optional, Set, Tuple
from zoneinfo import ZoneInfo

from ..config import settings
from ..models.profile import CitizenProfile
from ..models.match import (
    CriterionResult,
    MatchCounts,
    MatchResponse,
    MatchResultsGrouped,
    SchemeVerdictResult
)
from ..models.states import state_matches
from ..services.followup import rank_followup_fields
from .operators import evaluate_operator

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")


def is_scheme_closed(close_date_str: Optional[str]) -> bool:
    """Checks if scheme close_date has passed in Asia/Kolkata timezone."""
    if not close_date_str:
        return False
    try:
        today = datetime.datetime.now(KOLKATA_TZ).date()
        close_dt = datetime.date.fromisoformat(close_date_str[:10])
        return close_dt < today
    except Exception:
        return False


class MatchEngine:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn

    def evaluate_profile(
        self,
        profile: CitizenProfile,
        previous_unlocked_slugs: Optional[List[str]] = None
    ) -> MatchResponse:
        cursor = self.conn.cursor()

        # 1. Fetch all schemes in catalog (1 single query)
        cursor.execute("""
            SELECT 
                s.slug, s.name, s.short_title, s.ministry, s.department, s.level,
                s.beneficiary_states, s.all_states, s.categories, s.close_date,
                s.brief_description, t.verified_ratio
            FROM schemes s
            LEFT JOIN scheme_compilation_trace t ON s.slug = t.slug
            ORDER BY s.name ASC
        """)
        scheme_rows = cursor.fetchall()

        # 2. Bulk pre-fetch all compiled criteria across the catalog (1 single query)
        cursor.execute("""
            SELECT 
                slug, criterion_id, group_id, kind, field, operator, value,
                source_section, source_line, source_quote, quote_verified, note
            FROM scheme_criteria
            ORDER BY slug ASC, group_id ASC, criterion_id ASC
        """)
        criteria_rows = cursor.fetchall()
        criteria_by_slug = defaultdict(list)
        for row in criteria_rows:
            criteria_by_slug[row["slug"]].append(dict(row))

        # 3. Bulk pre-fetch all required documents across the catalog (1 single query)
        cursor.execute("""
            SELECT slug, line_index, document_text
            FROM scheme_documents
            ORDER BY slug ASC, line_index ASC
        """)
        documents_by_slug = defaultdict(list)
        for d in cursor.fetchall():
            documents_by_slug[d["slug"]].append(d["document_text"])

        base_myscheme = settings.MYSCHEME_BASE_URL.rstrip('/')
        counts = MatchCounts()
        grouped_results = MatchResultsGrouped()
        prev_slugs_set = set(previous_unlocked_slugs or [])
        state_filter_applied = bool(profile.state_ut)

        for s in scheme_rows:
            slug = s["slug"]
            name = s["name"]
            level = s["level"]
            min_dept = s["ministry"] or s["department"] or ""
            b_states = json.loads(s["beneficiary_states"]) if s["beneficiary_states"] else []
            categories = json.loads(s["categories"]) if s["categories"] else []
            all_states = bool(s["all_states"])
            close_date = s["close_date"]
            brief = s["brief_description"] or ""
            v_ratio = s["verified_ratio"] if s["verified_ratio"] is not None else 1.0

            myscheme_url = f"{base_myscheme}/schemes/{slug}"
            req_docs = documents_by_slug.get(slug, [])

            # Extract criteria and specialized / department prerequisite rules
            criteria = criteria_by_slug.get(slug, [])
            scheme_specialized_criteria = [
                c["source_quote"] for c in criteria
                if (c["operator"] == "unverifiable" or c["field"] is None) and c.get("source_quote")
            ]
            specialized_list = list(dict.fromkeys(scheme_specialized_criteria))

            # -------------------------------------------------------------
            # STAGE 1: Deterministic Hard-Gate Pruning (< 15ms)
            # -------------------------------------------------------------
            # A. Check deadline
            if is_scheme_closed(close_date):
                counts.closed += 1
                grouped_results.closed.append(SchemeVerdictResult(
                    slug=slug, name=name, ministry_or_department=min_dept, level=level,
                    beneficiary_states=b_states, categories=categories, close_date=close_date,
                    verdict="closed", benefit_snippet=brief, description=brief,
                    myscheme_url=myscheme_url, required_documents=req_docs,
                    specialized_criteria=specialized_list, verified_ratio=v_ratio,
                    missing_fields=[], criteria_results=[]
                ))
                continue

            # B. Check State Candidacy (Rule L11)
            if not state_matches(profile.state_ut, b_states, all_states):
                counts.excluded_by_state += 1
                counts.ineligible += 1
                grouped_results.ineligible.append(SchemeVerdictResult(
                    slug=slug, name=name, ministry_or_department=min_dept, level=level,
                    beneficiary_states=b_states, categories=categories, close_date=close_date,
                    verdict="ineligible", benefit_snippet=brief, description=brief,
                    myscheme_url=myscheme_url, required_documents=req_docs,
                    specialized_criteria=specialized_list, verified_ratio=v_ratio,
                    missing_fields=[],
                    criteria_results=[
                        CriterionResult(
                            criterion_id="state_scope", kind="requirement", group_id=0,
                            field="state_ut", result="fail",
                            quote=f"Scheme available only in: {', '.join(b_states)}",
                            quote_verified=True, source_line=0,
                            note=f"Resident of {profile.state_ut} is outside scheme boundary",
                            is_specialized=False
                        )
                    ]
                ))
                continue

            # -------------------------------------------------------------
            # STAGE 2: Contextual Nuance Evaluation (Kleene 3-Valued Logic)
            # -------------------------------------------------------------
            group_map = defaultdict(list)
            for c in criteria:
                group_map[c["group_id"]].append(c)

            scheme_criteria_results: List[CriterionResult] = []
            group_verdicts = {}
            scheme_missing_fields: Set[str] = set()

            for g_id, c_list in group_map.items():
                g_c_results = []
                for c in c_list:
                    c_field = c["field"]
                    c_op = c["operator"]
                    c_val = json.loads(c["value"]) if c["value"] is not None else None
                    c_kind = c["kind"]
                    is_spec = bool(c_op == "unverifiable" or c_field is None)

                    actual_fact = getattr(profile, c_field, None) if c_field else None
                    res = evaluate_operator(
                        operator=c_op, target_value=c_val, actual_value=actual_fact,
                        profile=profile, kind=c_kind
                    )

                    if res == "unknown" and c_field and actual_fact is None:
                        scheme_missing_fields.add(c_field)

                    scheme_criteria_results.append(CriterionResult(
                        criterion_id=c["criterion_id"], kind=c_kind, group_id=g_id,
                        field=c_field, result=res, quote=c["source_quote"],
                        quote_verified=bool(c["quote_verified"]), source_line=c["source_line"],
                        note=c.get("note"), is_specialized=is_spec
                    ))
                    g_c_results.append(res)

                # Disjunctive OR rule evaluation for group
                if "pass" in g_c_results:
                    group_verdicts[g_id] = "pass"
                elif all(r == "fail" for r in g_c_results):
                    group_verdicts[g_id] = "fail"
                else:
                    group_verdicts[g_id] = "unknown"

            # Aggregate Scheme Verdict
            if any(v == "fail" for v in group_verdicts.values()):
                verdict = "ineligible"
                counts.ineligible += 1
            elif len(scheme_missing_fields) > 0:
                verdict = "needs_more_info"
                counts.needs_more_info += 1
            else:
                verdict = "eligible"
                counts.eligible += 1

            # Check if newly unlocked in this interactive turn
            unlocked_now = bool(verdict == "eligible" and len(prev_slugs_set) > 0 and slug not in prev_slugs_set)

            verdict_obj = SchemeVerdictResult(
                slug=slug, name=name, ministry_or_department=min_dept, level=level,
                beneficiary_states=b_states, categories=categories, close_date=close_date,
                verdict=verdict, benefit_snippet=brief, description=brief,
                myscheme_url=myscheme_url, required_documents=req_docs,
                specialized_criteria=specialized_list, verified_ratio=v_ratio,
                missing_fields=sorted(list(scheme_missing_fields)),
                criteria_results=scheme_criteria_results,
                unlocked_in_this_round=unlocked_now
            )

            if verdict == "eligible":
                grouped_results.eligible.append(verdict_obj)
            elif verdict == "needs_more_info":
                grouped_results.needs_more_info.append(verdict_obj)
            else:
                grouped_results.ineligible.append(verdict_obj)

        # 3. Deterministic Verified Ranking
        grouped_results.eligible.sort(key=lambda x: (-x.verified_ratio, x.name))
        grouped_results.needs_more_info.sort(key=lambda x: (len(x.missing_fields), -x.verified_ratio, x.name))
        grouped_results.ineligible.sort(key=lambda x: x.name)

        # 4. High-Leverage Follow-Up Questions (Top 3 unlock fields)
        followup_fields = rank_followup_fields(grouped_results.needs_more_info, limit=3)

        return MatchResponse(
            state_filter_applied=state_filter_applied,
            counts=counts,
            followup_fields=followup_fields,
            results=grouped_results
        )
