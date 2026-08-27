"""
src/extractors/helpers.py
─────────────────────────
Shared constants and utilities used by all extractor modules.
"""

import re

# ── Section header vocabulary ─────────────────────────────────────────────────

EDU_HEADERS: set[str] = {
    "education", "academic background", "academic qualifications",
    "educational background", "academic credentials", "scholastic details",
    "degrees", "certifications", "academic profile",
}

EXP_HEADERS: set[str] = {
    "experience", "work experience", "employment history",
    "professional experience", "career history", "work history",
    "career highlights", "professional background", "employment",
}

SECTION_TERMINATORS: set[str] = (
    EDU_HEADERS
    | EXP_HEADERS
    | {
        "projects", "key projects", "selected projects", "personal projects",
        "skills", "technical skills", "core competencies", "areas of expertise", 
        "tools & technologies", "it skills",
        "certifications", "achievements", "awards", "honors & awards", 
        "publications", "languages", "interests", "hobbies", "references", 
        "volunteer", "volunteering",
        "summary", "professional summary", "career objective", "profile", "about me", "executive summary"
    }
)

# ── Bullet stripping ──────────────────────────────────────────────────────────

BULLET_RE = re.compile(r'^[\s\*\-\•\▪\◦\✦\·\–\—\>]+')


def clean_line(line: str) -> str:
    """Strip leading bullet characters and lowercase for header comparison."""
    return BULLET_RE.sub('', line).strip().lower()


def is_section_header(line: str, header_set: set[str]) -> bool:
    """
    Return True if the line matches a known section header.

    Tolerates common decorations and trailing suffixes
    (e.g. 'Work Experience (Recent)', '--- Education ---').
    """
    cleaned = clean_line(line)
    if cleaned in header_set:
        return True
    return any(cleaned.startswith(h) for h in header_set)
