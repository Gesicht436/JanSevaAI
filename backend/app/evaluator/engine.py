"""
Two-Stage Hybrid Match Engine (Rules L10, L11, L14, L19)
Stage 1: Deterministic Hard-Gate Pruning (< 15ms)
Stage 2: Contextual Nuance Evaluation, Progressive Unlocking & Follow-up Ranking
"""

from collections import defaultdict
import datetime
import json
import sqlite3
import threading
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
from ..models.documents import normalize_document_text, RequiredDocumentItem
from ..models.states import check_state_scope, is_all_india, normalize_state
from ..services.followup import rank_followup_fields
from .operators import evaluate_operator

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")

_catalog_cache: Optional[Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], Dict[str, List[RequiredDocumentItem]]]] = None
_cache_lock = threading.Lock()


def get_preloaded_catalog(conn: sqlite3.Connection):
    """Caches decoded immutable scheme metadata and parsed criteria values at process scope."""
    global _catalog_cache
    if _catalog_cache is None:
        with _cache_lock:
            if _catalog_cache is None:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.slug, s.name, s.short_title, s.ministry, s.department, s.level,
                        s.beneficiary_states, s.all_states, s.categories, s.close_date,
                        s.brief_description, t.verified_ratio
                    FROM schemes s
                    LEFT JOIN scheme_compilation_trace t ON s.slug = t.slug
                    ORDER BY s.name ASC
                """)
                raw_schemes = cursor.fetchall()
                parsed_schemes = []
                for s in raw_schemes:
                    d = dict(s)
                    d["beneficiary_states_parsed"] = json.loads(d["beneficiary_states"]) if d.get("beneficiary_states") else []
                    d["categories_parsed"] = json.loads(d["categories"]) if d.get("categories") else []
                    parsed_schemes.append(d)

                cursor.execute("""
                    SELECT 
                        slug, criterion_id, group_id, kind, field, operator, value,
                        source_section, source_line, source_quote, quote_verified, note
                    FROM scheme_criteria
                    ORDER BY slug ASC, group_id ASC, criterion_id ASC
                """)
                criteria_by_slug = defaultdict(list)
                for r in cursor.fetchall():
                    c_dict = dict(r)
                    raw_val = c_dict.get("value")
                    if raw_val is not None and isinstance(raw_val, str):
                        try:
                            c_dict["parsed_value"] = json.loads(raw_val)
                        except Exception:
                            c_dict["parsed_value"] = raw_val
                    else:
                        c_dict["parsed_value"] = raw_val
                    criteria_by_slug[c_dict["slug"]].append(c_dict)

                cursor.execute("""
                    SELECT slug, line_index, document_text
                    FROM scheme_documents
                    ORDER BY slug ASC, line_index ASC
                """)
                docs_by_slug = defaultdict(list)
                for d in cursor.fetchall():
                    doc_text = d["document_text"]
                    docs_by_slug[d["slug"]].append(RequiredDocumentItem(
                        type=normalize_document_text(doc_text),
                        text=doc_text,
                        source_line=d["line_index"]
                    ))

                _catalog_cache = (parsed_schemes, dict(criteria_by_slug), dict(docs_by_slug))
    return _catalog_cache


def clear_catalog_cache():
    global _catalog_cache
    with _cache_lock:
        _catalog_cache = None


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

    def evaluate_single_scheme(
        self,
        scheme: Dict[str, Any],
        criteria: List[Dict[str, Any]],
        req_docs: List[Any],
        profile: CitizenProfile,
        previous_unlocked_slugs: Optional[Set[str]] = None
    ) -> SchemeVerdictResult:
        """
        Evaluates a single scheme against a citizen profile.
        Shared core evaluation logic for both full-catalog and single-scheme requests.
        """
        slug = scheme["slug"]
        name = scheme["name"]
        level = scheme["level"]
        min_dept = scheme.get("ministry") or scheme.get("department") or ""
        b_states = scheme.get("beneficiary_states_parsed") if "beneficiary_states_parsed" in scheme else (json.loads(scheme["beneficiary_states"]) if scheme.get("beneficiary_states") else [])
        categories = scheme.get("categories_parsed") if "categories_parsed" in scheme else (json.loads(scheme["categories"]) if scheme.get("categories") else [])
        all_states = bool(scheme.get("all_states"))
        close_date = scheme.get("close_date")
        brief = scheme.get("brief_description") or ""
        v_ratio = scheme["verified_ratio"] if scheme.get("verified_ratio") is not None else 1.0

        base_myscheme = settings.MYSCHEME_BASE_URL.rstrip('/')
        myscheme_url = f"{base_myscheme}/schemes/{slug}"

        # Specialized / department prerequisite rules
        scheme_specialized_criteria = [
            c["source_quote"] for c in criteria
            if (c.get("operator") == "unverifiable" or c.get("field") is None) and c.get("source_quote")
        ]
        specialized_list = list(dict.fromkeys(scheme_specialized_criteria))

        # -------------------------------------------------------------
        # STAGE 1: Deterministic Hard-Gate Pruning (< 15ms)
        # -------------------------------------------------------------
        # A. Check deadline
        if is_scheme_closed(close_date):
            return SchemeVerdictResult(
                slug=slug, name=name, ministry_or_department=min_dept, level=level,
                beneficiary_states=b_states, categories=categories, close_date=close_date,
                verdict="closed", benefit_snippet=brief, description=brief,
                myscheme_url=myscheme_url, required_documents=req_docs,
                specialized_criteria=specialized_list, verified_ratio=v_ratio,
                missing_fields=[], criteria_results=[]
            )

        scheme_criteria_results: List[CriterionResult] = []
        group_verdicts: Dict[int, str] = {}
        scheme_missing_fields: Set[str] = set()

        # B. Check State Candidacy (Rule L11 & P0.2)
        state_status = check_state_scope(profile.state_ut, b_states, all_states)

        if state_status == "fail":
            # Definitively excluded: known resident outside restriction
            scheme_criteria_results.append(CriterionResult(
                criterion_id="state_scope", kind="requirement", group_id=0,
                field="state_ut", result="fail",
                quote=f"Scheme beneficiary state restriction: {', '.join(b_states)}",
                quote_verified=False, source_line=0, source_section="metadata",
                note=f"Resident of {profile.state_ut} is outside scheme boundary",
                is_specialized=False
            ))
            return SchemeVerdictResult(
                slug=slug, name=name, ministry_or_department=min_dept, level=level,
                beneficiary_states=b_states, categories=categories, close_date=close_date,
                verdict="ineligible", benefit_snippet=brief, description=brief,
                myscheme_url=myscheme_url, required_documents=req_docs,
                specialized_criteria=specialized_list, verified_ratio=v_ratio,
                missing_fields=[],
                criteria_results=scheme_criteria_results
            )

        elif state_status == "missing_state":
            # State-restricted scheme, citizen state is missing or invalid: add state_ut follow-up
            scheme_missing_fields.add("state_ut")
            scheme_criteria_results.append(CriterionResult(
                criterion_id="state_scope", kind="requirement", group_id=0,
                field="state_ut", result="unknown",
                quote=f"Scheme restricted to specific states/UTs: {', '.join(b_states)}",
                quote_verified=False, source_line=0, source_section="metadata",
                note="Resident state/UT is required to confirm eligibility",
                is_specialized=False
            ))
            group_verdicts[0] = "unknown"

        elif state_status == "ambiguous":
            # Ambiguous state scope: not declared all-India and no states given
            scheme_criteria_results.append(CriterionResult(
                criterion_id="state_scope", kind="requirement", group_id=0,
                field=None, result="unknown",
                quote="Geographic boundary not specified in source metadata",
                quote_verified=False, source_line=0, source_section="metadata",
                note="Geographic scope requires departmental confirmation",
                is_specialized=True
            ))
            group_verdicts[0] = "unknown"

        # -------------------------------------------------------------
        # STAGE 2: Contextual Nuance Evaluation (Kleene 3-Valued Logic)
        # -------------------------------------------------------------
        group_map = defaultdict(list)
        for c in criteria:
            group_map[c["group_id"]].append(c)

        for g_id, c_list in group_map.items():
            g_c_results = []
            for c in c_list:
                c_field = c.get("field")
                c_op = c.get("operator", "unverifiable")
                if "parsed_value" in c:
                    c_val = c["parsed_value"]
                else:
                    val_raw = c.get("value")
                    if val_raw is not None and isinstance(val_raw, str):
                        try:
                            c_val = json.loads(val_raw)
                        except Exception:
                            c_val = val_raw
                    else:
                        c_val = val_raw

                c_kind = c.get("kind", "requirement")
                is_spec = bool(c_op == "unverifiable" or c_field is None)
                quote_verified = bool(c.get("quote_verified", False))

                actual_fact = getattr(profile, c_field, None) if c_field else None

                # Rule P0.1: An unverified source quote must never produce a pass/fail evaluation
                if not quote_verified:
                    res = "unknown"
                else:
                    res = evaluate_operator(
                        operator=c_op, target_value=c_val, actual_value=actual_fact,
                        profile=profile, kind=c_kind
                    )

                if res == "unknown" and c_field and actual_fact is None:
                    scheme_missing_fields.add(c_field)

                scheme_criteria_results.append(CriterionResult(
                    criterion_id=str(c.get("criterion_id", f"c_{g_id}")),
                    kind=c_kind,
                    group_id=g_id,
                    field=c_field,
                    result=res,
                    quote=c.get("source_quote", ""),
                    quote_verified=quote_verified,
                    source_line=c.get("source_line", 0),
                    source_section=c.get("source_section", "eligibility"),
                    note=c.get("note"),
                    is_specialized=is_spec
                ))
                g_c_results.append(res)

            # Disjunctive OR rule evaluation for group
            # A group is 'pass' if at least one verified alternative passes
            # A group is 'fail' only if all alternatives fail
            # Otherwise 'unknown'
            if "pass" in g_c_results:
                group_verdicts[g_id] = "pass"
            elif g_c_results and all(r == "fail" for r in g_c_results):
                group_verdicts[g_id] = "fail"
            else:
                group_verdicts[g_id] = "unknown"

        # Aggregate Scheme Verdict (P0.1)
        # 1. Any definitely failing mandatory group establishes ineligible.
        # 2. Empty criteria set must NEVER be eligible (P0.1).
        # 3. Any unknown mandatory group or missing fields means needs_more_info.
        # 4. Only all-pass mandatory groups can establish eligible.
        has_fail = any(v == "fail" for v in group_verdicts.values())
        has_unknown = any(v == "unknown" for v in group_verdicts.values())
        has_missing = len(scheme_missing_fields) > 0
        empty_criteria = len(criteria) == 0

        if has_fail:
            verdict = "ineligible"
        elif empty_criteria or has_unknown or has_missing:
            verdict = "needs_more_info"
        else:
            verdict = "eligible"

        # Check if newly unlocked in this interactive turn
        prev_set = previous_unlocked_slugs or set()
        unlocked_now = bool(verdict == "eligible" and len(prev_set) > 0 and slug not in prev_set)

        # Flag manual review when unresolved criteria exist that cannot be answered via profile fields
        requires_manual_review = any(
            cr.result == "unknown" and (cr.field is None or cr.is_specialized or not cr.quote_verified)
            for cr in scheme_criteria_results
        ) or (empty_criteria and verdict == "needs_more_info")

        return SchemeVerdictResult(
            slug=slug,
            name=name,
            ministry_or_department=min_dept,
            level=level,
            beneficiary_states=b_states,
            categories=categories,
            close_date=close_date,
            verdict=verdict,
            benefit_snippet=brief,
            description=brief,
            myscheme_url=myscheme_url,
            required_documents=req_docs,
            specialized_criteria=specialized_list,
            verified_ratio=v_ratio,
            missing_fields=sorted(list(scheme_missing_fields)),
            criteria_results=scheme_criteria_results,
            unlocked_in_this_round=unlocked_now,
            requires_manual_review=requires_manual_review
        )

    def evaluate_scheme(self, slug: str, profile: CitizenProfile) -> Optional[SchemeVerdictResult]:
        """Evaluates a single scheme by slug without full catalog evaluation."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                s.slug, s.name, s.short_title, s.ministry, s.department, s.level,
                s.beneficiary_states, s.all_states, s.categories, s.close_date,
                s.brief_description, t.verified_ratio
            FROM schemes s
            LEFT JOIN scheme_compilation_trace t ON s.slug = t.slug
            WHERE s.slug = ?
        """, (slug,))
        row = cursor.fetchone()
        if not row:
            return None

        cursor.execute("""
            SELECT 
                slug, criterion_id, group_id, kind, field, operator, value,
                source_section, source_line, source_quote, quote_verified, note
            FROM scheme_criteria
            WHERE slug = ?
            ORDER BY group_id ASC, criterion_id ASC
        """, (slug,))
        criteria = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT line_index, document_text
            FROM scheme_documents
            WHERE slug = ?
            ORDER BY line_index ASC
        """, (slug,))
        docs = [
            RequiredDocumentItem(
                type=normalize_document_text(d["document_text"]),
                text=d["document_text"],
                source_line=d["line_index"]
            )
            for d in cursor.fetchall()
        ]

        return self.evaluate_single_scheme(dict(row), criteria, docs, profile)

    def evaluate_profile(
        self,
        profile: CitizenProfile,
        previous_unlocked_slugs: Optional[List[str]] = None
    ) -> MatchResponse:
        scheme_rows, criteria_by_slug, documents_by_slug = get_preloaded_catalog(self.conn)

        counts = MatchCounts()
        grouped_results = MatchResultsGrouped()
        prev_slugs_set = set(previous_unlocked_slugs or [])
        state_filter_applied = bool(profile.state_ut)

        for s in scheme_rows:
            slug = s["slug"]
            criteria = criteria_by_slug.get(slug, [])
            req_docs = documents_by_slug.get(slug, [])

            verdict_obj = self.evaluate_single_scheme(
                scheme=dict(s),
                criteria=criteria,
                req_docs=req_docs,
                profile=profile,
                previous_unlocked_slugs=prev_slugs_set
            )

            if verdict_obj.verdict == "closed":
                counts.closed += 1
                grouped_results.closed.append(verdict_obj)
            elif verdict_obj.verdict == "ineligible":
                counts.ineligible += 1
                if any(cr.criterion_id == "state_scope" and cr.result == "fail" for cr in verdict_obj.criteria_results):
                    counts.excluded_by_state += 1
                grouped_results.ineligible.append(verdict_obj)
            elif verdict_obj.verdict == "needs_more_info":
                counts.needs_more_info += 1
                grouped_results.needs_more_info.append(verdict_obj)
            else:
                counts.eligible += 1
                grouped_results.eligible.append(verdict_obj)

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
