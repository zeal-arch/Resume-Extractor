"""
src/extractors/experience.py
────────────────────────────
Extracts work experience entries from resume text using section-aware
heuristic parsing.

What counts as an experience line
──────────────────────────────────
Inside the Experience section, we keep a line only if it matches at least
one of these signals:
  - Contains a 4-digit year (e.g. '2019', '2023')
  - Contains a common separator pattern (' - ', ' | ', ' at ')
  - Contains a common job-title keyword (engineer, developer, analyst, etc.)

This filters out pure bullet-point descriptions ('- Led a team of 5…')
while retaining role/company/date header lines.

Limitations
───────────
- Deeply nested bullets that still contain years may be captured.
- Non-English job title keywords will be missed.
- Capped at 8 entries to avoid returning the entire section body.
"""

import re
from src.extractors.helpers import (
    EXP_HEADERS, SECTION_TERMINATORS, clean_line, is_section_header, BULLET_RE,
)

_EXIT_HEADERS = SECTION_TERMINATORS - EXP_HEADERS

# A line looks like a role/company/date if it has any of these signals
_ROLE_SIGNAL = re.compile(
    r'(\d{4})'                                                   # 4-digit year
    r'|( - | \| | at )'                                          # common separators
    r'|(intern|engineer|developer|analyst|manager|designer'
    r'|lead|architect|consultant|specialist|officer|director)',  # job-title words
    re.IGNORECASE,
)

_MAX_ENTRIES = 8


def extract_experience(text: str) -> list[str]:
    """
    Return a list of work experience entry lines found in the resume.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume.

    Returns
    -------
    list[str] — up to _MAX_ENTRIES non-empty experience entry strings.
    """
    lines = text.split('\n')
    experience: list[str] = []
    in_section = False

    for line in lines:
        line_clean = clean_line(line)

        if is_section_header(line, EXP_HEADERS):
            in_section = True
            continue

        if in_section and is_section_header(line, _EXIT_HEADERS):
            in_section = False
            continue

        if in_section and line_clean:
            stripped = line.strip()

            # Skip stray single-character or very short lines
            if len(stripped) < 5:
                continue

            # Skip long bullet-description lines
            # (starts with a bullet char AND is longer than 80 chars)
            if BULLET_RE.match(line) and len(stripped) > 80:
                continue

            # Keep only lines that look like a role/company/date header
            if _ROLE_SIGNAL.search(stripped):
                experience.append(stripped)

    return experience[:_MAX_ENTRIES]
