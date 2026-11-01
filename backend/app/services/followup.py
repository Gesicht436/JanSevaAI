"""
Follow-up Question & Information Gain Calculation
Determines which missing fields have the highest leverage to transition
Tier 2 (Needs More Info) schemes into Tier 1 (Eligible).
"""

from collections import Counter
from typing import Dict, List, Set
from ..models.match import SchemeVerdictResult

FIELD_LABELS = {
    "state_ut": "Which State or Union Territory do you currently reside in?",
    "age": "Could you confirm your age in years?",
    "gender": "What is your gender (Female / Male / Transgender)?",
    "qualification": "What is your highest educational qualification (e.g. 10th, 12th, Graduate, Postgraduate)?",
    "marital_status": "What is your marital status (Never Married, Married, Widowed)?",
    "caste_category": "Do you belong to General, OBC, SC, or ST category?",
    "residence": "Do you live in a Rural or Urban area?",
    "annual_family_income_inr": "What is your total annual household income in rupees?",
    "current_sector": "Which sector or industry do you work in (e.g. IT, Farming, Construction, Manufacturing, Crafts)?",
    "aspiring_sector": "Which sector do you want training or financial assistance for?",
    "benefit_intent": "What specific assistance are you seeking (e.g. Loan, Scholarship, Pension)?",
    "is_bpl": "Do you or your family hold a BPL or Ration Card?",
    "is_farmer": "Do you or your family cultivate agricultural land?",
    "land_holding_acres": "How many acres of agricultural land do you own or cultivate?",
    "is_differently_abled": "Are you a person with a certified benchmark disability?",
    "documents_held": "Which official documents do you currently possess (e.g. Aadhaar, Bank Passbook, Caste Certificate)?"
}


def rank_followup_fields(needs_more_info_schemes: List[SchemeVerdictResult], limit: int = 3) -> List[str]:
    """
    Ranks missing fields by frequency of occurrence across potential schemes.
    """
    counter: Counter[str] = Counter()
    for s in needs_more_info_schemes:
        for f in s.missing_fields:
            if f in FIELD_LABELS:
                counter[f] += 1

    return [item[0] for item in counter.most_common(limit)]
