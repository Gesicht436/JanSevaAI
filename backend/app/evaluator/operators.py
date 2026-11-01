"""
Kleene Three-Valued Logic Operators
Pure deterministic evaluation functions (Rule L10).
Returns: "pass", "fail", or "unknown"
"""

from typing import Any, List, Optional
from ..models.profile import CitizenProfile

QUALIFICATION_HIERARCHY = {
    "below_10th": 0,
    "10th_pass": 1,
    "12th_pass": 2,
    "diploma": 3,
    "graduate": 4,
    "postgraduate": 5
}


def evaluate_operator(
    operator: str,
    target_value: Any,
    actual_value: Any,
    profile: Optional[CitizenProfile] = None,
    kind: str = "requirement"
) -> str:
    """
    Evaluates condition holding between target_value and actual_value.
    Inverts verdict if kind == 'exclusion'.
    """
    if operator == "unverifiable":
        return "unknown"

    # Missing factual input from citizen
    if actual_value is None:
        return "unknown"

    holds = False

    if operator == "eq":
        holds = (str(actual_value).strip().lower() == str(target_value).strip().lower())

    elif operator == "ne":
        holds = (str(actual_value).strip().lower() != str(target_value).strip().lower())

    elif operator == "in":
        if isinstance(target_value, list):
            norm_targets = [str(x).strip().lower() for x in target_value]
            holds = (str(actual_value).strip().lower() in norm_targets)
        else:
            holds = (str(actual_value).strip().lower() == str(target_value).strip().lower())

    elif operator == "not_in":
        if isinstance(target_value, list):
            norm_targets = [str(x).strip().lower() for x in target_value]
            holds = (str(actual_value).strip().lower() not in norm_targets)
        else:
            holds = (str(actual_value).strip().lower() != str(target_value).strip().lower())

    elif operator == "gte":
        try:
            holds = float(actual_value) >= float(target_value)
        except (ValueError, TypeError):
            return "unknown"

    elif operator == "lte":
        try:
            holds = float(actual_value) <= float(target_value)
        except (ValueError, TypeError):
            return "unknown"

    elif operator == "between":
        try:
            if isinstance(target_value, list) and len(target_value) == 2:
                holds = float(target_value[0]) <= float(actual_value) <= float(target_value[1])
            else:
                return "unknown"
        except (ValueError, TypeError):
            return "unknown"

    elif operator == "is_true":
        holds = (actual_value is True)

    elif operator == "is_false":
        holds = (actual_value is False)

    elif operator == "has_document":
        if isinstance(actual_value, list):
            holds = (target_value in actual_value or str(target_value).lower() in [str(x).lower() for x in actual_value])
        else:
            holds = False

    elif operator == "lacks_document":
        if isinstance(actual_value, list):
            holds = (target_value not in actual_value and str(target_value).lower() not in [str(x).lower() for x in actual_value])
        else:
            holds = True

    elif operator == "gte_qualification":
        act_score = QUALIFICATION_HIERARCHY.get(str(actual_value).lower(), -1)
        tgt_score = QUALIFICATION_HIERARCHY.get(str(target_value).lower(), 999)
        holds = (act_score >= tgt_score)

    elif operator == "sector_in":
        if isinstance(target_value, list):
            norm_targets = [str(x).strip().lower() for x in target_value]
            holds = (str(actual_value).strip().lower() in norm_targets)
            # Also check aspiring sector if present
            if not holds and profile and profile.aspiring_sector:
                holds = (str(profile.aspiring_sector).strip().lower() in norm_targets)
        else:
            holds = (str(actual_value).strip().lower() == str(target_value).strip().lower())

    elif operator == "intent_matches":
        holds = (str(actual_value).strip().lower() == str(target_value).strip().lower())

    else:
        return "unknown"

    # For exclusions: if condition holds (is met), citizen is excluded -> fail!
    if kind == "exclusion":
        return "fail" if holds else "pass"

    return "pass" if holds else "fail"
