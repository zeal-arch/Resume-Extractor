"""
src/extractors/email.py
───────────────────────
Extracts a candidate's email address using two strategies:

1. Regex scan of the visible text layer.
   Pattern based on RFC-practical recommendations:
   - Negative lookahead prevents leading dot or consecutive dots (..),
     which are technically invalid but common in OCR noise.
   - Supports plus-addressing (user+label@domain.com).
   - Handles multi-level domains (user@mail.company.co.uk).

2. Fallback: scan embedded mailto: URIs recovered from PDF annotations
   or DOCX hyperlink relationships — catches emails that appear only as
   clickable links with custom display text (e.g. 'Contact Me').
"""

import re

# Robust email regex (pragmatic, not full RFC 5322):
# - Rejects emails starting with a dot or containing consecutive dots.
# - Allows plus-addressing (+) and apostrophes in local part.
# - Handles dotted domains like co.uk, ac.in, etc.
_EMAIL_RE = re.compile(
    r"(?<!\.)(?<!\.\w)"           # no leading dot context
    r"[a-zA-Z0-9_%+\-]+"          # local part start (no leading dot)
    r"(?:\.[a-zA-Z0-9_%+\-]+)*"   # optional dotted local part segments
    r"@"
    r"[a-zA-Z0-9][a-zA-Z0-9\-]*"  # domain (must start alphanumeric)
    r"(?:\.[a-zA-Z0-9][a-zA-Z0-9\-]*)*"  # sub-domains
    r"\.[a-zA-Z]{2,}",            # TLD (2+ letters)
    re.IGNORECASE,
)

_CONSECUTIVE_DOTS = re.compile(r'\.\.+')


def _is_clean(email: str) -> bool:
    """Quick sanity check after regex match."""
    local, _, domain = email.partition('@')
    return (
        not local.startswith('.')
        and not local.endswith('.')
        and not _CONSECUTIVE_DOTS.search(email)
        and len(local) >= 1
        and len(domain) >= 4
    )


def extract_email(text: str, embedded_uris: list[str] | None = None) -> str | None:
    """
    Return the first valid email address found in the resume.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume file.
    embedded_uris : list[str] | None
        URIs from PDF annotations / DOCX rels (may include 'mailto:…').

    Returns
    -------
    str  — the email address (e.g. 'jane@example.com')
    None — if no valid address is found.
    """
    # Strategy 1: visible text layer
    for match in _EMAIL_RE.finditer(text):
        candidate = match.group(0)
        if _is_clean(candidate):
            return candidate

    # Strategy 2: embedded mailto: URIs (hidden behind hyperlink buttons)
    if embedded_uris:
        for uri in embedded_uris:
            if uri.lower().startswith('mailto:'):
                address = uri[len('mailto:'):].split('?')[0].strip()
                if _EMAIL_RE.fullmatch(address) and _is_clean(address):
                    return address

    return None
