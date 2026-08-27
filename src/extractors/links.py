"""
src/extractors/links.py
───────────────────────
Extracts LinkedIn and GitHub profile URLs from resume content.

Two-pass strategy
─────────────────
1. Regex scan of the visible text layer.
2. Fallback scan of embedded_uris (covers URLs hidden behind display text,
   e.g. a 'LinkedIn' button that links to the real profile URL).

URLs are returned stripped of the https://www. prefix for clean output.
"""

import re
from typing import TypedDict


class ProfileLinks(TypedDict):
    linkedin: str | None
    github: str | None


_LINKEDIN_RE = re.compile(
    r'https?://(?:www\.)?linkedin\.com/(?:in|profile)/[a-zA-Z0-9_%-]+',
    re.IGNORECASE,
)
_GITHUB_RE = re.compile(
    r'https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+',
    re.IGNORECASE,
)
_URL_PREFIX = re.compile(r'^https?://(?:www\.)?')


def _clean_url(url: str | None) -> str | None:
    return _URL_PREFIX.sub('', url) if url else None


def extract_links(text: str, embedded_uris: list[str] | None = None) -> ProfileLinks:
    """
    Return LinkedIn and GitHub URLs found in the resume.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume.
    embedded_uris : list[str] | None
        Hyperlink URIs from PDF annotations or DOCX relationships.

    Returns
    -------
    ProfileLinks — dict with keys 'linkedin' and 'github' (str or None).
    """
    linkedin = _LINKEDIN_RE.search(text)
    github = _GITHUB_RE.search(text)

    li_url = linkedin.group(0) if linkedin else None
    gh_url = github.group(0) if github else None

    if embedded_uris and (not li_url or not gh_url):
        for uri in embedded_uris:
            if not li_url:
                m = _LINKEDIN_RE.search(uri)
                if m:
                    li_url = m.group(0)
            if not gh_url:
                m = _GITHUB_RE.search(uri)
                if m:
                    gh_url = m.group(0)

    return {
        "linkedin": _clean_url(li_url),
        "github":   _clean_url(gh_url),
    }
