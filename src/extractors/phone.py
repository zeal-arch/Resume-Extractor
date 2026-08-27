"""
src/extractors/phone.py
───────────────────────
Extracts a phone number from resume text using the Google libphonenumber port.

Design decisions
────────────────
- We use the `phonenumbers` library instead of regex. International formats
  vary wildly (length, spacing, prefixes). Regex produces too many false
  positives (ZIP codes, VAT IDs) and false negatives (missed extensions).
- We use `PhoneNumberMatcher` to scan the unstructured text.
- Extracted numbers are validated against global telecom rules and returned
  in standard E.164 international format when possible.
"""

import re

try:
    import phonenumbers
    from phonenumbers import PhoneNumberFormat
    _HAS_PHONENUMBERS = True
except ImportError:
    _HAS_PHONENUMBERS = False

# Fallback regex if the library is not installed
_FALLBACK_RE = re.compile(r'\+?\d[\d\s\-\(\)]{7,15}\d')


def extract_phone(text: str) -> str | None:
    """
    Return the first valid phone number found in the resume.

    If phonenumbers is installed, the returned number is formatted to
    international standard (E.164) if possible.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume.

    Returns
    -------
    str  — the matched and formatted phone string.
    None — if no valid number is found.
    """
    if _HAS_PHONENUMBERS:
        # Default to US if no country code is specified, as a baseline.
        # STRICT_GROUPING prevents date ranges (e.g. 01/2012 - 04/2019) from
        # being falsely parsed as valid US phone numbers.
        for match in phonenumbers.PhoneNumberMatcher(text, "US", leniency=phonenumbers.Leniency.STRICT_GROUPING):
            if phonenumbers.is_valid_number(match.number):
                return phonenumbers.format_number(
                    match.number, PhoneNumberFormat.INTERNATIONAL
                )

    # Fallback to broad regex if the library is missing or didn't find anything
    match = _FALLBACK_RE.search(text)
    if match:
        candidate = match.group(0).strip()
        digit_count = len(re.sub(r'\D', '', candidate))
        if 7 <= digit_count <= 15:
            return candidate

    return None
