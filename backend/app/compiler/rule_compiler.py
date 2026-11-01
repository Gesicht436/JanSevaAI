"""
Deterministic Rule Compiler (Pass 1 Fast Engine)
Extracts typed criteria from eligibility and exclusions lines using high-precision regex.
Supports qualification tiers, career sectors, credit intents, and demographic markers.
"""

import re
from typing import Any, Dict, List, Optional
from ..models.states import STATES
from .verifier import normalize_text, verify_quote


class RuleCompiler:
    def __init__(self):
        self.states = STATES

    def compile_section_lines(
        self,
        slug: str,
        section_name: str,
        lines: List[Dict[str, Any]],
        start_counter: int = 1
    ) -> List[Dict[str, Any]]:
        criteria = []
        c_counter = start_counter
        kind = "exclusion" if section_name == "exclusions" else "requirement"

        for line_obj in lines:
            line_idx = line_obj["line_index"]
            line_text = line_obj["line_text"].strip()
            if not line_text:
                continue

            extracted = self._extract_rules_from_line(
                slug=slug,
                line_idx=line_idx,
                line_text=line_text,
                section_name=section_name,
                kind=kind,
                start_c_id=c_counter
            )
            for c in extracted:
                criteria.append(c)
                c_counter += 1

        return criteria

    def _extract_rules_from_line(
        self,
        slug: str,
        line_idx: int,
        line_text: str,
        section_name: str,
        kind: str,
        start_c_id: int
    ) -> List[Dict[str, Any]]:
        extracted = []
        lower = line_text.lower()
        c_id = f"c{start_c_id}"

        # 1. State / UT Residency
        for state in self.states:
            st_lower = state.lower()
            if st_lower in lower and any(w in lower for w in ["resident", "domicile", "living in", "citizen of", "state of", "ut of"]):
                start_p = lower.find(st_lower)
                end_p = start_p + len(st_lower)
                extracted.append(self._build_criterion(
                    c_id=c_id, kind=kind, group_id=start_c_id, field="state_ut",
                    operator="eq", value=state, section_name=section_name,
                    line_idx=line_idx, quote=line_text[start_p:end_p],
                    note=f"Must be a resident of {state}"
                ))
                return extracted

        # 2. Educational Qualification
        if re.search(r'\b(postgraduate|post-graduate|pg degree|master\'?s? degree)\b', lower):
            m = re.search(r'\b(postgraduate|post-graduate|pg degree|master\'?s? degree)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="qualification",
                operator="gte_qualification", value="postgraduate", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must have completed Postgraduate degree or higher"
            ))
            return extracted
        elif re.search(r'\b(graduate|bachelor\'?s? degree|college degree|b\.?tech|b\.?sc|b\.?com|b\.?a|bca)\b', lower):
            m = re.search(r'\b(graduate|bachelor\'?s? degree|college degree|b\.?tech|b\.?sc|b\.?com|b\.?a|bca)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="qualification",
                operator="gte_qualification", value="graduate", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must hold at least a Bachelor's degree / Graduate qualification"
            ))
            return extracted
        elif re.search(r'\b(diploma|polytechnic|iti)\b', lower):
            m = re.search(r'\b(diploma|polytechnic|iti)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="qualification",
                operator="gte_qualification", value="diploma", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must hold a technical Diploma or ITI certification"
            ))
            return extracted
        elif re.search(r'\b(12th|class 12|higher secondary|intermediate|10\+2)\b', lower):
            m = re.search(r'\b(12th|class 12|higher secondary|intermediate|10\+2)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="qualification",
                operator="gte_qualification", value="12th_pass", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must have passed Class 12th / Higher Secondary"
            ))
            return extracted
        elif re.search(r'\b(10th|class 10|matriculation|matric|sslc)\b', lower):
            m = re.search(r'\b(10th|class 10|matriculation|matric|sslc)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="qualification",
                operator="gte_qualification", value="10th_pass", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must have passed Class 10th / Matriculation"
            ))
            return extracted

        # 3. Industry / Career Sectors
        if re.search(r'\b(it sector|software|information technology|computer|telecom)\b', lower):
            m = re.search(r'\b(it sector|software|information technology|computer|telecom)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="current_sector",
                operator="sector_in", value=["it_tech"], section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Applicable to IT / Tech industry"
            ))
            return extracted
        elif re.search(r'\b(farmer|agriculture|cultivator|farming|dairy|fisheries)\b', lower):
            m = re.search(r'\b(farmer|agriculture|cultivator|farming|dairy|fisheries)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="is_farmer",
                operator="is_true", value=True, section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Requires agricultural farmer / cultivator background"
            ))
            return extracted
        elif re.search(r'\b(artisan|craftsman|handloom|weaver|potter|blacksmith)\b', lower):
            m = re.search(r'\b(artisan|craftsman|handloom|weaver|potter|blacksmith)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="current_sector",
                operator="sector_in", value=["artisan_craft"], section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Applicable to traditional artisans / craft workers"
            ))
            return extracted

        # 4. Age Constraints
        age_between = re.search(r'\b(?:between|age of)\s*(\d{1,2})\s*(?:and|to|-)\s*(\d{1,2})\s*(?:years|yrs)?\b', lower)
        if age_between:
            min_a, max_a = int(age_between.group(1)), int(age_between.group(2))
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="age",
                operator="between", value=[min_a, max_a], section_name=section_name,
                line_idx=line_idx, quote=line_text[age_between.start():age_between.end()],
                note=f"Age must be between {min_a} and {max_a} years"
            ))
            return extracted

        age_min = re.search(r'\b(?:at least|minimum|above)\s*(\d{1,2})\s*(?:years|yrs)?\s*(?:of age)?\b', lower)
        if age_min:
            min_a = int(age_min.group(1))
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="age",
                operator="gte", value=min_a, section_name=section_name,
                line_idx=line_idx, quote=line_text[age_min.start():age_min.end()],
                note=f"Age must be at least {min_a} years"
            ))
            return extracted

        age_max = re.search(r'\b(?:maximum|not exceed|below|up to)\s*(\d{1,2})\s*(?:years|yrs)?\s*(?:of age)?\b', lower)
        if age_max:
            max_a = int(age_max.group(1))
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="age",
                operator="lte", value=max_a, section_name=section_name,
                line_idx=line_idx, quote=line_text[age_max.start():age_max.end()],
                note=f"Age must not exceed {max_a} years"
            ))
            return extracted

        # 5. Gender Specifics
        if re.search(r'\b(only women|female candidates?|women only|girl student)\b', lower):
            m = re.search(r'\b(only women|female candidates?|women only|girl student)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="gender",
                operator="eq", value="female", section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Exclusively for female citizens"
            ))
            return extracted

        # 6. Caste & Minority
        if re.search(r'\b(scheduled caste|scheduled tribe|sc/st|sc and st|sc, st)\b', lower):
            m = re.search(r'\b(scheduled caste|scheduled tribe|sc/st|sc and st|sc, st)\b', lower)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="caste_category",
                operator="in", value=["sc", "st"], section_name=section_name,
                line_idx=line_idx, quote=line_text[m.start():m.end()],
                note="Must belong to SC or ST category"
            ))
            return extracted

        # 7. Income Limits
        inc_m = re.search(r'(?:income|annual income|family income)\s*(?:does not exceed|not more than|less than|up to|below|<=)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|crore)?', lower)
        if inc_m:
            raw_v = float(inc_m.group(1))
            unit = inc_m.group(2) or ""
            mult = 100000 if "la" in unit else (10000000 if "crore" in unit else 1)
            ceiling = int(raw_v * mult)
            extracted.append(self._build_criterion(
                c_id=c_id, kind=kind, group_id=start_c_id, field="annual_family_income_inr",
                operator="lte", value=ceiling, section_name=section_name,
                line_idx=line_idx, quote=line_text[inc_m.start():inc_m.end()],
                note=f"Annual family income must not exceed ₹{ceiling:,}"
            ))
            return extracted

        # 8. Fallback: Unverifiable clause with verbatim quote
        quote_text = line_text[:120].strip()
        extracted.append(self._build_criterion(
            c_id=c_id, kind=kind, group_id=start_c_id, field=None,
            operator="unverifiable", value=None, section_name=section_name,
            line_idx=line_idx, quote=quote_text,
            note=line_text[:150]
        ))
        return extracted

    def _build_criterion(
        self,
        c_id: str,
        kind: str,
        group_id: int,
        field: Optional[str],
        operator: str,
        value: Any,
        section_name: str,
        line_idx: int,
        quote: str,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "id": c_id,
            "kind": kind,
            "group_id": group_id,
            "field": field,
            "operator": operator,
            "value": value,
            "origin": "text",
            "source_section": section_name,
            "source_line": line_idx,
            "source_quote": quote,
            "quote_verified": True,
            "note": note
        }
