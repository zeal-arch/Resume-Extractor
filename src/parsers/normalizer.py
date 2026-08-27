"""
src/parsers/normalizer.py
─────────────────────────
Handles PDF-specific text cleanup:
  - Replaces common ligature characters from custom-encoded PDF fonts.
  - Applies Unicode NFC normalization.
  - Inserts spaces between merged camelCase words (e.g. 'SoftwareEngineer').
  - Collapses spaced-out characters (e.g. 'S K I L L S' → 'SKILLS').
"""

import re
import unicodedata

# Ligature → ASCII substitutions from custom PDF font encodings
_LIGATURE_MAP: dict[str, str] = {
    '\ufb00': 'ff',  '\ufb01': 'fi',  '\ufb02': 'fl',
    '\ufb03': 'ffi', '\ufb04': 'ffl', '\ufb05': 'st',
    '\u2019': "'",   '\u2018': "'",   '\u201c': '"',  '\u201d': '"',
    '\u2013': '-',   '\u2014': '-',
    '\u2022': '*',   '\u25aa': '*',   '\u25cf': '*',
    '\u25e6': '*',   '\u00b7': '*',
}

_SPACED_CHAR_RE = re.compile(r'\b\w\s')


def _fix_spaced_text(text: str) -> str:
    """
    Collapse lines where characters are separated by single spaces
    (e.g. 'S K I L L S' → 'SKILLS'). Double-spaces are preserved as
    word boundaries.
    """
    fixed = []
    for line in text.split('\n'):
        if len(re.findall(_SPACED_CHAR_RE, line)) > 5 and len(line) > 10:
            line = line.replace('  ', '\x00')
            line = line.replace(' ', '')
            line = line.replace('\x00', ' ')
        fixed.append(line)
    return '\n'.join(fixed)


def normalize_text(text: str) -> str:
    """
    Clean raw text extracted from PDFs.

    Steps
    -----
    1. Replace ligatures / special chars.
    2. Unicode NFC normalization.
    3. Split merged camelCase words ('SoftwareEngineer' → 'Software Engineer').
    4. Collapse spaced-out characters ('S k i l l s' → 'Skills').
    """
    for char, replacement in _LIGATURE_MAP.items():
        text = text.replace(char, replacement)

    text = unicodedata.normalize('NFC', text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    text = _fix_spaced_text(text)
    return text
