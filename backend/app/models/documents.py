"""
Canonical Documents and Normalization (Rule L8, Rule E9)
Defines the canonical DocumentType set, alias mappings, and document models.
"""

import re
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel

DocumentType = Literal[
    "aadhaar", "ration_card", "income_certificate", "caste_certificate",
    "domicile_certificate", "bank_passbook", "birth_certificate",
    "disability_certificate", "land_records", "school_or_college_id",
    "marksheet", "passport_photo"
]

CANONICAL_DOCUMENTS: Dict[str, str] = {
    "aadhaar": "Aadhaar Card",
    "ration_card": "Ration Card (BPL / Antyodaya / APL)",
    "income_certificate": "Income Certificate",
    "caste_certificate": "Caste / Community Certificate",
    "domicile_certificate": "Domicile / Residence Certificate",
    "bank_passbook": "Bank Passbook / Account Details",
    "birth_certificate": "Birth Certificate / Age Proof",
    "disability_certificate": "Disability Certificate (UDID)",
    "land_records": "Land Records (RoR / 7-12 / Patta / Khasra)",
    "school_or_college_id": "School / College / Student ID",
    "marksheet": "Educational Marksheet / Degree Certificate",
    "passport_photo": "Passport Size Photograph"
}

_DOCUMENT_PATTERNS = [
    ("aadhaar", [r"\baadhaar\b", r"\badhar\b", r"\buidai\b", r"\buid card\b", r"\baadhar\b"]),
    ("ration_card", [r"\bration card\b", r"\bbpl card\b", r"\baay card\b", r"\bration\b"]),
    ("income_certificate", [r"\bincome cert", r"\bproof of income\b", r"\bsalary cert", r"\bincome proof\b"]),
    ("caste_certificate", [r"\bcaste cert", r"\bcommunity cert", r"\bsc cert", r"\bst cert", r"\bobc cert", r"\btribe cert"]),
    ("domicile_certificate", [r"\bdomicile\b", r"\bresidence cert", r"\bproof of residence\b", r"\bnativity cert", r"\bresidential proof\b"]),
    ("bank_passbook", [r"\bbank passbook\b", r"\bbank account\b", r"\bpassbook\b", r"\bcancelled cheque\b", r"\bbank statement\b"]),
    ("birth_certificate", [r"\bbirth cert", r"\bproof of date of birth\b", r"\bdob cert", r"\bage proof\b"]),
    ("disability_certificate", [r"\bdisability cert", r"\bpwd cert", r"\budid\b", r"\bhandicapped cert"]),
    ("land_records", [r"\bland record", r"\b7/12\b", r"\bpatta\b", r"\bkhasra\b", r"\bkhatauni\b", r"\bror\b", r"\bland deed\b", r"\bjamabandi\b"]),
    ("school_or_college_id", [r"\bschool id\b", r"\bcollege id\b", r"\bstudent id\b", r"\bbonafide cert"]),
    ("marksheet", [r"\bmarksheet\b", r"\bmark sheet\b", r"\bdegree cert", r"\bdiploma cert", r"\bpassing cert", r"\b10th cert", r"\b12th cert"]),
    ("passport_photo", [r"\bpassport.*photo", r"\bphotograph\b", r"\bpassport size photo", r"\brecent photo"])
]


def normalize_document_text(text: Optional[str]) -> Optional[str]:
    """
    Deterministically normalizes raw document requirement text into canonical DocumentType.
    Returns None for unclassified / specialized document requirements.
    """
    if not text:
        return None
    lower = text.casefold()
    for doc_type, patterns in _DOCUMENT_PATTERNS:
        for pat in patterns:
            if re.search(pat, lower):
                return doc_type
    return None


class RequiredDocumentItem(BaseModel):
    type: Optional[str] = None
    text: str
    source_line: Optional[int] = None
