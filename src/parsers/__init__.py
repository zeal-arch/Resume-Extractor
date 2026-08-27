"""
src/parsers/__init__.py
───────────────────────
Public interface for the parsers package.

Consumers (e.g. main.py) import from here:
    from src.parsers import extract_text

The function returns a (text, embedded_uris) tuple so callers can pass
embedded_uris to the extraction layer for catching links hidden in
annotation/hyperlink metadata (not visible in raw text).
"""

import os
from src.parsers.pdf_parser  import extract_text_from_pdf,  extract_embedded_links_from_pdf
from src.parsers.docx_parser import extract_text_from_docx, extract_embedded_links_from_docx

# Only these extensions are accepted — anything else is rejected early.
SUPPORTED_FORMATS = {'.pdf', '.docx'}


def extract_text(file_path: str) -> tuple[str, list[str]]:
    """
    Dispatch to the correct parser based on file extension.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to a resume file.

    Returns
    -------
    text : str
        Plain text content of the resume (visible layer only).
    embedded_uris : list[str]
        Hyperlink URIs found in annotation/relationship metadata.
        These may contain emails or profile links absent from visible text.

    Raises / Fails
    --------------
    Unsupported extensions print an error and return ('', []).
    Individual parser errors are caught and printed; partial results returned.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        print(
            f"[parsers] Unsupported format '{ext}'. "
            f"Only {sorted(SUPPORTED_FORMATS)} are accepted."
        )
        return "", []

    if ext == '.pdf':
        text = extract_text_from_pdf(file_path)
        uris = extract_embedded_links_from_pdf(file_path)
    else:  # .docx
        text = extract_text_from_docx(file_path)
        uris = extract_embedded_links_from_docx(file_path)

    return text, uris
