"""
Canonical Indian States and Union Territories (Rule L11)
Defines the 36 official states/UTs, abbreviations, normalization, and candidacy matching.
"""

import re
import unicodedata
from typing import List, Optional

STATES = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal"
]

STATE_ABBREVIATIONS = {
    "ap": "Andhra Pradesh",
    "ar": "Arunachal Pradesh",
    "as": "Assam",
    "br": "Bihar",
    "cg": "Chhattisgarh",
    "ch": "Chandigarh",
    "dd": "Dadra and Nagar Haveli and Daman and Diu",
    "dl": "Delhi",
    "ga": "Goa",
    "gj": "Gujarat",
    "hp": "Himachal Pradesh",
    "hr": "Haryana",
    "jh": "Jharkhand",
    "jk": "Jammu and Kashmir",
    "ka": "Karnataka",
    "kl": "Kerala",
    "la": "Ladakh",
    "ld": "Lakshadweep",
    "mh": "Maharashtra",
    "ml": "Meghalaya",
    "mn": "Manipur",
    "mp": "Madhya Pradesh",
    "mz": "Mizoram",
    "nl": "Nagaland",
    "od": "Odisha",
    "pb": "Punjab",
    "py": "Puducherry",
    "rj": "Rajasthan",
    "sk": "Sikkim",
    "tn": "Tamil Nadu",
    "ts": "Telangana",
    "tr": "Tripura",
    "up": "Uttar Pradesh",
    "uk": "Uttarakhand",
    "wb": "West Bengal",
}

_CANONICAL_MAP = {re.sub(r"[^a-z0-9]", "", s.casefold()): s for s in STATES}
_CANONICAL_MAP.update({
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "uttaranchal": "Uttarakhand",
    "nctofdelhi": "Delhi",
    "delhincr": "Delhi",
    "damananddiu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadraandnagarhaveli": "Dadra and Nagar Haveli and Daman and Diu"
})


def normalize_state(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    val = value.strip().casefold()
    if val in STATE_ABBREVIATIONS:
        return STATE_ABBREVIATIONS[val]
    cleaned = re.sub(r"[^a-z0-9]", "", val)
    return _CANONICAL_MAP.get(cleaned)


def is_all_india(scheme_states: List[str], all_states: bool) -> bool:
    if all_states:
        return True
    if not scheme_states:
        return False
    lower_states = [s.strip().casefold() for s in scheme_states if s]
    return any(tok in lower_states for tok in ["all", "all india", "pan india", "pan-india", "all states"])


def check_state_scope(citizen_state: Optional[str], scheme_states: List[str], all_states: bool) -> str:
    """
    Evaluates citizen state against scheme geographic boundary.
    Returns:
      'pass' - scheme is All-India, or citizen's normalized state is in scheme_states.
      'missing_state' - scheme is state-restricted, but citizen state is missing or unrecognized.
      'fail' - scheme is state-restricted, and citizen has a valid normalized state outside the restriction.
      'ambiguous' - all_states is false and scheme_states is empty (unspecified restriction).
    """
    if is_all_india(scheme_states, all_states):
        return "pass"

    if not scheme_states:
        # Ambiguous scope: not declared all-India, but no states listed
        return "ambiguous"

    norm_cit = normalize_state(citizen_state)
    if not norm_cit:
        # Missing or invalid citizen state on a state-restricted scheme
        return "missing_state"

    for s in scheme_states:
        norm_s = normalize_state(s)
        if norm_s and norm_s == norm_cit:
            return "pass"

    return "fail"


def state_matches(citizen_state: Optional[str], scheme_states: List[str], all_states: bool) -> bool:
    return check_state_scope(citizen_state, scheme_states, all_states) == "pass"
