"""
src/extractors/education.py
───────────────────────────
Extracts education records from resume text using rule-based parsing.

Strategy
────────
1. Locate the Education section using known header keywords.
2. Within that section, group lines into degree + institution pairs by
   pattern-matching (degree keywords, institution keywords).
3. Look for optional year and score (CGPA/percentage) on nearby lines.
4. If no section is found, fall back to a full-document scan.
5. For degrees missing an institution, attempt recovery from
   orphaned institution lines elsewhere in the document.
"""

import re
from src.extractors.helpers import EDU_HEADERS, SECTION_TERMINATORS, is_section_header

# ── Patterns ──────────────────────────────────────────────────────────────────

_DEGREE_REGEX = re.compile(
    r'\b('
    r'b\.?\s*tech|m\.?\s*tech|'
    r'b\.?\s*e\.?|m\.?\s*e\.?|'
    r'b\.?\s*c\.?\s*a|m\.?\s*c\.?\s*a|'
    r'b\.?\s*sc|m\.?\s*sc|b\.?\s*s\b|m\.?\s*s\b|'
    r'b\.?\s*com|m\.?\s*com|'
    r'b\.?\s*b\.?\s*a|m\.?\s*b\.?\s*a|'
    r'ph\.?\s*d|doctorate|'
    r"bachelor(?:[''`]s)?(?:\s+of\s+[A-Za-z\s]+)?|"
    r"master(?:[''`]s)?(?:\s+of\s+[A-Za-z\s]+)?|"
    r'diploma(?:\s+in\s+[A-Za-z\s]+)?|'
    r"associate(?:[''`]s)?(?:\s+degree)?|"
    r'higher\s+secondary|senior\s+secondary|secondary\s+school|'
    r'12th|10th|sslc|cbse|icse|hsc'
    r')\b',
    re.IGNORECASE
)

_INSTITUTION_KEYWORDS = [
    "university", "institute", "college", "school", "academy",
    "polytechnic", "vidyalaya", "campus"
]

_INSTITUTION_KNOWN = [
    "mit", "iit", "nit", "iiit", "bits", "iim",
    "stanford", "harvard", "berkeley", "oxford", "cambridge"
]

# Lines that look like institutions but are really certifications / jobs
_CERT_JOB_CLUES = re.compile(
    r'\b(certified|developer|engineer|manager|lead|architect|intern|analyst|scientist|consultant)\b'
    r'|\s[-–—]\s+[A-Z]'    # dash followed by subject (e.g. "MICE – C & C++")
    r'|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',  # month names = certification/job date
    re.IGNORECASE
)

_YEAR_REGEX = re.compile(
    r'\b((?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|present|expected(?:\s+(?:19|20)\d{2})?)|'
    r'(?:19|20)\d{2})\b',
    re.IGNORECASE
)

_SCORE_REGEX = re.compile(
    r'(?:(?:cgpa|sgpa|gpa|percentage|marks|aggregate|score)\s*[:=-]?\s*(\d{1,2}(?:\.\d{1,2})?(?:\s*/\s*(?:10|4|100))?)|'
    r'(\d{1,2}(?:\.\d{1,2})?\s*(?:%|/\s*(?:10|4|100))))',
    re.IGNORECASE
)

_MONTH_NAMES = re.compile(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b', re.IGNORECASE)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_degree(line: str) -> bool:
    """Return True if the line contains a degree keyword."""
    # 'to be' phrase contains 'b.e' as a false match
    if re.search(r'\bto\s+be\b', line, re.IGNORECASE):
        line = re.sub(r'\bto\s+be\b', '', line, flags=re.IGNORECASE)
    return bool(_DEGREE_REGEX.search(line))


def _is_institution(line: str) -> bool:
    """Return True if the line looks like a university / college name."""
    ll = line.lower()
    if any(kw in ll for kw in _INSTITUTION_KEYWORDS):
        return True
    words = [w.strip("(),.") for w in ll.split()]
    return any(w in _INSTITUTION_KNOWN for w in words)


def _is_cert_or_job(line: str) -> bool:
    """Return True if the line is better classified as a certification or job title."""
    return bool(_CERT_JOB_CLUES.search(line))


# ── Core logic ─────────────────────────────────────────────────────────────────

def _parse_entries(section_lines: list[str]) -> list[dict]:
    """Parse a list of lines from the education section into structured entries."""
    education: list[dict] = []
    curr: dict = {}

    for line in section_lines:
        has_deg = _is_degree(line)
        has_inst = _is_institution(line) and not _is_cert_or_job(line)

        if has_deg and has_inst:
            # Line contains both — try to split at a comma
            if curr:
                education.append(curr)
            curr = {}
            if ',' in line:
                left, right = line.split(',', 1)
                if _is_degree(left) and _is_institution(right):
                    curr["degree"] = left.strip()
                    curr["institution"] = right.strip()
                elif _is_institution(left) and _is_degree(right):
                    curr["institution"] = left.strip()
                    curr["degree"] = right.strip()
                else:
                    curr["degree"] = line
            else:
                curr["degree"] = line

        elif has_deg:
            if curr.get("degree"):
                education.append(curr)
                curr = {}
            curr["degree"] = line

        elif has_inst:
            if curr.get("institution"):
                # Already have one — start a new entry or append
                if not curr.get("degree"):
                    curr["institution"] += f", {line}"
                else:
                    education.append(curr)
                    curr = {"institution": line}
            else:
                curr["institution"] = line

        else:
            # May contain a score or year attached to the current entry
            if curr:
                score_m = _SCORE_REGEX.search(line)
                if score_m and not _MONTH_NAMES.search(line):
                    # score_m has two groups due to OR condition in regex, take whichever matched
                    score_val = score_m.group(1) or score_m.group(2)
                    if score_val:
                        curr.setdefault("score", score_val.strip())
                year_m = _YEAR_REGEX.search(line)
                if year_m:
                    curr.setdefault("year", year_m.group(0).strip())

    if curr:
        education.append(curr)

    return education


def extract_education(text: str) -> list[dict]:
    """
    Return a list of education records found in the resume.

    Each record is a dict with keys: degree, institution (optional),
    year (optional), score (optional).
    """
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # ── Pass 1: section-aware ────────────────────────────────────────────────
    section_lines: list[str] = []
    in_edu = False

    for line in lines:
        if is_section_header(line, EDU_HEADERS):
            in_edu = True
            continue
        if in_edu and is_section_header(line, SECTION_TERMINATORS - EDU_HEADERS):
            in_edu = False
            continue
        if in_edu:
            section_lines.append(line)

    education = _parse_entries(section_lines if section_lines else lines)

    # ── Recovery: fill missing institutions from elsewhere in document ────────
    used = {e.get("institution") for e in education} | {e.get("degree") for e in education}
    orphans = [
        l for l in lines
        if _is_institution(l)
        and l not in used
        and not _is_cert_or_job(l)
        and not is_section_header(l, SECTION_TERMINATORS)
    ]

    for entry in education:
        if "degree" in entry and "institution" not in entry and orphans:
            entry["institution"] = orphans.pop(0)

    return education
