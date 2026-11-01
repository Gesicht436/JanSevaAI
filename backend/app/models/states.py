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


def state_matches(citizen_state: Optional[str], scheme_states: List[str], all_states: bool) -> bool:
    if all_states or "All" in scheme_states or "all" in [s.lower() for s in scheme_states]:
        return True
    if not citizen_state:
        return True
    norm_cit = normalize_state(citizen_state)
    if not norm_cit:
        return True
    for s in scheme_states:
        norm_s = normalize_state(s)
        if norm_s and norm_s == norm_cit:
            return True
    return False
