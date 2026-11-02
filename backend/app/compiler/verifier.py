"""
Formal Verifier Module (Rule L8, L9)
Validates that criteria quotes are verbatim substrings of source text lines,
verifies numeric values against Indian currency/number representations,
and enforces line coverage.
"""

from dataclasses import dataclass
import html
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Union
from ..models.criteria import Criterion

try:
    from Crawler.flattener import clean_line_text
except ImportError:
    def clean_line_text(text: str) -> str:
        """Collapses whitespace and strips leading/trailing space."""
        if not text:
            return ""
        text = html.unescape(text)
        return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class Problem:
    line: int
    code: str
    message: str


def normalize_text(text: str) -> str:
    """Normalize whitespace and unicode for strict substring checking."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", clean_line_text(text))
    return (
        normalized.replace("“", '"').replace("”", '"')
        .replace("‘", "'").replace("’", "'")
        .replace("–", "-").replace("—", "-")
        .casefold()
    )


def verify_quote(quote_or_criterion: Union[str, Criterion], line_text_or_lines: Union[str, List[str]]) -> Union[bool, Optional[Problem]]:
    """
    Overloaded verifier supporting both string checks and Criterion object checks.
    """
    if isinstance(quote_or_criterion, str) and isinstance(line_text_or_lines, str):
        if not quote_or_criterion or not line_text_or_lines:
            return False
        return normalize_text(quote_or_criterion) in normalize_text(line_text_or_lines)

    # Criterion object validation
    criterion = quote_or_criterion
    lines = line_text_or_lines
    if criterion.source_line >= len(lines):
        return Problem(criterion.source_line, "line_out_of_range", "Source line index is out of range.")
    if len(criterion.source_quote) > 300 or not criterion.source_quote.strip():
        return Problem(criterion.source_line, "invalid_quote", "Quote must be non-empty and at most 300 characters.")
    if normalize_text(criterion.source_quote) not in normalize_text(lines[criterion.source_line]):
        return Problem(criterion.source_line, "quote_not_found", "Quote is not a verbatim fragment of the source line.")
    return None


def extract_numbers_from_text(value: str) -> set[float]:
    """Extracts numeric values including Indian denominations (crore, lakh, lac)."""
    text = value.casefold().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "")
    output: set[float] = set()
    pattern = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s*(?P<unit>crore|crores|cr|lakh|lakhs|lacs|lac|k)?\b")
    for match in pattern.finditer(text):
        number = float(match.group("number"))
        unit = match.group("unit")
        if unit and (unit.startswith("crore") or unit == "cr"):
            number *= 10_000_000
        elif unit and (unit.startswith("lakh") or unit.startswith("lac")):
            number *= 100_000
        elif unit == "k":
            number *= 1_000
        output.add(number)
    return output


def verify_numbers(criterion: Criterion) -> Optional[Problem]:
    """Ensures numbers assigned to criteria actually exist in the source quote."""
    if criterion.operator == "unverifiable" or criterion.value is None:
        return None
    quote_numbers = extract_numbers_from_text(criterion.source_quote)
    values = criterion.value if isinstance(criterion.value, list) else [criterion.value]
    for val in values:
        if isinstance(val, (int, float)) and not isinstance(val, bool) and float(val) not in quote_numbers:
            return Problem(
                criterion.source_line,
                "number_not_in_quote",
                f"Numeric value {val} does not appear in the source quote."
            )
    return None


def verify_coverage(criteria: List[Criterion], eligibility: List[str], exclusions: List[str]) -> List[Problem]:
    covered = {(c.source_section, c.source_line) for c in criteria}
    problems = []
    for section, lines in (("eligibility", eligibility), ("exclusions", exclusions)):
        for idx in range(len(lines)):
            if (section, idx) not in covered:
                problems.append(Problem(idx, "line_not_covered", f"{section} line {idx} has no criterion."))
    return problems


def verify_criteria(criteria: List[Criterion], eligibility: List[str], exclusions: List[str]) -> List[Problem]:
    problems: List[Problem] = []
    source_by_section = {"eligibility": eligibility, "exclusions": exclusions}
    group_kinds: Dict[int, str] = {}

    for c in criteria:
        lines = source_by_section.get(c.source_section, [])
        q_prob = verify_quote(c, lines)
        if q_prob:
            problems.append(q_prob)
            continue
        n_prob = verify_numbers(c)
        if n_prob:
            problems.append(n_prob)
        prior_kind = group_kinds.setdefault(c.group_id, c.kind)
        if prior_kind != c.kind:
            problems.append(Problem(c.source_line, "mixed_group_kind", "An OR group cannot mix requirements and exclusions."))

    problems.extend(verify_coverage(criteria, eligibility, exclusions))
    return problems


def verify_scheme_criteria(criteria: List[Dict[str, Any]], source_lines: List[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
    """Helper for dictionary-based batch verification enforcing exact section + line and numeric validity."""
    if not criteria:
        return False, 0.0, ["No criteria generated"]

    line_map = {
        (item.get("section_name", "eligibility"), item["line_index"]): item["line_text"]
        for item in source_lines
    }

    issues = []
    verified_count = 0

    for c in criteria:
        sec = c.get("source_section", "eligibility")
        line_idx = c.get("source_line", 0)
        quote = c.get("source_quote", "")
        actual_line = line_map.get((sec, line_idx))

        # P0.3: No cross-section fallback! Must match exact (section, line)
        if actual_line is None:
            c["quote_verified"] = False
            issues.append(f"Criterion {c.get('id')}: line ({sec}, #{line_idx}) missing or out of range")
            continue

        if not verify_quote(quote, actual_line):
            c["quote_verified"] = False
            issues.append(f"Criterion {c.get('id')}: quote is not verbatim in ({sec}, #{line_idx})")
            continue

        # Check numeric consistency if applicable
        if c.get("operator") != "unverifiable" and c.get("value") is not None:
            quote_numbers = extract_numbers_from_text(quote)
            raw_vals = c["value"] if isinstance(c["value"], list) else [c["value"]]
            num_mismatch = False
            for val in raw_vals:
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    if float(val) not in quote_numbers:
                        num_mismatch = True
                        issues.append(f"Criterion {c.get('id')}: numeric value {val} not found in quote")
                        break
            if num_mismatch:
                c["quote_verified"] = False
                continue

        c["quote_verified"] = True
        verified_count += 1

    # Enforce source line coverage
    covered_lines = {(c.get("source_section", "eligibility"), c.get("source_line", 0)) for c in criteria}
    for k in line_map.keys():
        if k not in covered_lines:
            issues.append(f"Line ({k[0]}, #{k[1]}) has no compiled criterion")

    all_covered = all(k in covered_lines for k in line_map.keys())
    ratio = round(verified_count / len(criteria), 4) if criteria else 0.0
    return (verified_count == len(criteria)) and (len(issues) == 0) and all_covered, ratio, issues
