"""
Automated Verification & Retry Loop
Enforces multi-attempt verification feeding errors back into LLM prompt with fallback.
"""

from typing import Any, Dict, List
from .llm_compiler import PROMPT_VERSION, compile_once
from .verifier import Problem, verify_criteria, verify_quote, verify_numbers
from ..models.criteria import Criterion, CriteriaPayload


def compile_scheme(scheme: Dict[str, Any], llm_client: Any, max_attempts: int = 3) -> Dict[str, Any]:
    sections = scheme.get("sections") or {}
    eligibility = sections.get("eligibility") or []
    exclusions = sections.get("exclusions") or []
    documents = sections.get("documents_required") or []

    if not eligibility:
        return {
            "status": "failed", "criteria": [], "required_documents": [],
            "verified_ratio": 0.0, "evaluable_ratio": 0.0, "attempts": 0,
            "trace": [{"attempt": 0, "problems": [{"code": "E18", "message": "Scheme has no eligibility lines."}]}],
            "model": getattr(llm_client, "model", "default"), "prompt_version": PROMPT_VERSION
        }

    accepted: List[Criterion] = []
    trace: List[Dict[str, Any]] = []
    prior_problems: List[Dict[str, Any]] = []
    documents_out = []

    for attempt in range(1, max_attempts + 1):
        try:
            payload: CriteriaPayload = compile_once(
                llm_client, scheme.get("name", ""), eligibility, exclusions, documents, prior_problems
            )
            problems = verify_criteria(payload.criteria, eligibility, exclusions)
            trace.append({
                "attempt": attempt,
                "problems": [p.__dict__ for p in problems]
            })

            if not problems:
                accepted = [c.model_copy(update={"quote_verified": True}) for c in payload.criteria]
                documents_out = [d.model_dump() for d in payload.required_documents]
                return _build_result(accepted, documents_out, trace, getattr(llm_client, "model", "default"), "compiled")

            valid = [
                c.model_copy(update={"quote_verified": True})
                for c in payload.criteria
                if not _criterion_has_issue(c, eligibility, exclusions)
            ]
            accepted = valid
            documents_out = [d.model_dump() for d in payload.required_documents]
            prior_problems = [p.__dict__ for p in problems]
        except Exception as exc:
            trace.append({"attempt": attempt, "problems": [{"code": "compile_error", "message": str(exc)}]})
            prior_problems = [{"code": "compile_error", "message": str(exc)}]

    # Fallback: store remaining uncovered lines as unverifiable
    covered = {(c.source_section, c.source_line) for c in accepted}
    next_id = len(accepted) + 1
    for sec_name, lines in (("eligibility", eligibility), ("exclusions", exclusions)):
        kind = "requirement" if sec_name == "eligibility" else "exclusion"
        for idx, line in enumerate(lines):
            if (sec_name, idx) in covered:
                continue
            accepted.append(Criterion(
                id=f"c{next_id}",
                kind=kind,
                group_id=max((c.group_id for c in accepted), default=0) + 1,
                field=None,
                operator="unverifiable",
                value=None,
                source_section=sec_name,
                source_line=idx,
                source_quote=line[:150],
                quote_verified=True,
                note="Uncovered line fallback."
            ))
            next_id += 1

    return _build_result(accepted, documents_out, trace, getattr(llm_client, "model", "default"), "partial")


def _criterion_has_issue(criterion: Criterion, eligibility: List[str], exclusions: List[str]) -> bool:
    lines = eligibility if criterion.source_section == "eligibility" else exclusions
    if verify_quote(criterion, lines) is not None:
        return True
    if verify_numbers(criterion) is not None:
        return True
    return False


def _build_result(
    criteria: List[Criterion],
    documents: List[Dict[str, Any]],
    trace: List[Dict[str, Any]],
    model_name: str,
    status: str
) -> Dict[str, Any]:
    verified_count = sum(1 for c in criteria if c.quote_verified)
    evaluable_count = sum(1 for c in criteria if c.operator != "unverifiable")
    total = len(criteria) or 1
    return {
        "status": status,
        "criteria": [c.model_dump() for c in criteria],
        "required_documents": documents,
        "verified_ratio": round(verified_count / total, 4),
        "evaluable_ratio": round(evaluable_count / total, 4),
        "attempts": len(trace),
        "trace": trace,
        "model": model_name,
        "prompt_version": PROMPT_VERSION
    }
