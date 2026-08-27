"""
src/extractors/__init__.py
──────────────────────────
Public interface for the extractors package.

Consumers (e.g. main.py) import from here:
    from src.extractors import extract_all

extract_all() orchestrates all sub-extractors and assembles the final
structured JSON-compatible dictionary.
"""

from src.extractors.email      import extract_email
from src.extractors.phone      import extract_phone
from src.extractors.links      import extract_links
from src.extractors.name       import extract_name
from src.extractors.skills     import extract_skills
from src.extractors.education  import extract_education
from src.extractors.experience import extract_experience


def extract_all(
    text: str,
    embedded_uris: list[str] | None = None,
) -> dict:
    """
    Run all extractors and return a structured result dictionary.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume file (visible layer).
    embedded_uris : list[str] | None
        Hyperlink URIs from PDF annotations or DOCX relationships.
        Passed to email and links extractors so they can find values
        that are not visible in the text layer.

    Returns
    -------
    dict with keys:
        name, email, phone, skills, education, experience, linkedin, github
    """
    if embedded_uris is None:
        embedded_uris = []

    links = extract_links(text, embedded_uris)

    return {
        "name":       extract_name(text),
        "email":      extract_email(text, embedded_uris),
        "phone":      extract_phone(text),
        "skills":     extract_skills(text),
        "education":  extract_education(text),
        "experience": extract_experience(text),
        "linkedin":   links["linkedin"],
        "github":     links["github"],
    }
