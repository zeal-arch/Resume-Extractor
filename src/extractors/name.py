"""
src/extractors/name.py
──────────────────────
Extracts the candidate's full name from resume text.

Strategy
────────
1. Heuristic scan of the first 4 non-trivial lines: a clean 2–4 word
   string of letters only (no digits, pipes, or @ symbols) that doesn't
   match known job titles, section headers, or skill keywords.
2. Fallback to spaCy PERSON entity recognition on the top 5–10 lines.

We deliberately limit scanning to the document header region since resumes
almost always open with the candidate's name, while deeper sections risk
false positives (company names, references, etc.).
"""

import re

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except (ImportError, OSError):
    _nlp = None

_HAS_DIGIT = re.compile(r'\d')

_JOB_TITLE_WORDS: set[str] = {
    "engineer", "developer", "designer", "manager", "analyst", "scientist",
    "lead", "architect", "consultant", "intern", "specialist", "officer",
    "executive", "director", "programmer", "administrator", "student",
    "candidate", "resume", "curriculum", "vitae", "profile", "portfolio",
    "contact", "finalist", "solving", "hackerrank", "webdeveloper",
    # Languages (common in language-skills sections that look like 2-word names)
    "english", "hindi", "marathi", "tamil", "telugu", "kannada", "bengali",
    "gujarati", "malayalam", "punjabi", "urdu", "french", "german", "spanish",
}

_SECTION_HEADERS: set[str] = {
    "work experience", "professional summary", "technical skills", "education",
    "certifications", "projects", "key projects", "experience", "skills", "summary",
    "licences and", "licences", "achievements", "language", "languages",
    "contact", "profile", "objective", "about me", "interests", "hobbies",
    "references", "awards", "publications", "volunteer",
}

_SKILL_WORDS: set[str] = {
    "javascript", "typescript", "python", "java", "c++", "c#", "html", "css",
    "react", "angular", "vue", "next.js", "node.js", "express", "sql", "nosql",
    "mongodb", "postgresql", "mysql", "redis", "docker", "kubernetes", "aws",
    "azure", "gcp", "git", "linux", "pandas", "numpy", "scikit-learn",
    "tensorflow",
}

_NAME_CHARS = re.compile(r"^[A-Za-z\s\-\.]+$")  # no apostrophes
_POSSESSIVE = re.compile(r"\b\w+'s\b")


def _tokenize(line: str) -> list[str]:
    return [w.lower().strip("(),.;:\"'") for w in line.split()]


def _is_valid_name(line: str) -> bool:
    """Return True if the line looks like a personal name."""
    if any(c in line for c in ('@', 'http', '+', '|', '\u2022', '\u00b7')):
        return False
    if _POSSESSIVE.search(line):          # rejects "IBM's AI Fundamentals"
        return False
    if not _NAME_CHARS.match(line):
        return False
    words = _tokenize(line)
    if not (2 <= len(words) <= 4):
        return False
    if any(len(w) > 16 for w in words):  # "Fundamentals" (13) - fine; long cert titles fail
        return False
    if not line[0].isupper():             # must start with a capital letter
        return False
    low = line.lower()
    return (
        low not in _SECTION_HEADERS
        and not any(w in _JOB_TITLE_WORDS for w in words)
        and not any(w in _SKILL_WORDS for w in words)
    )


def extract_name(text: str) -> str | None:
    """Return the candidate's full name, or None if not found."""
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

    # Pass 1: heuristic scan of the top 10 lines (covers most single-column
    # resumes and resumes where the name is in the primary/right column).
    for line in lines[:10]:
        if _is_valid_name(line):
            return line.title() if line.isupper() else line

    # Pass 2: extended heuristic scan up to line 50.
    # Handles sidebar-heavy PDFs (e.g. Mayuri's resume) where the left sidebar
    # is read first by the layout engine, pushing the name to position ~30+.
    for line in lines[10:50]:
        if _is_valid_name(line):
            return line.title() if line.isupper() else line

    # Pass 3: spaCy NER on the first 50 lines as a final fallback.
    if _nlp is not None:
        doc = _nlp(" ".join(lines[:50]))
        for ent in doc.ents:
            if ent.label_ != "PERSON":
                continue
            name = ent.text.strip()
            words = _tokenize(name)
            if (
                len(words) >= 2
                and len(name) > 3
                and not _HAS_DIGIT.search(name)
                and '|' not in name
                and not any(w in _JOB_TITLE_WORDS for w in words)
                and not any(w in _SKILL_WORDS for w in words)
            ):
                return name.title() if name.isupper() else name

    # Pass 4: single-word name fallback.
    # For resumes where only the first name appears at the top (e.g. Vishwajeet's
    # resume with Unicode icons that ate the surname), return the first valid token.
    for line in lines[:5]:
        words = _tokenize(line)
        if (
            len(words) == 1
            and len(line) > 3
            and line[0].isupper()
            and _NAME_CHARS.match(line)
            and line.lower() not in _SECTION_HEADERS
            and line.lower() not in _JOB_TITLE_WORDS
            and not _HAS_DIGIT.search(line)
        ):
            return line.title() if line.isupper() else line

    return None
