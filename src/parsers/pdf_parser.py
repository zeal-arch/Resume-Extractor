"""
src/parsers/pdf_parser.py
─────────────────────────
Extracts text and embedded hyperlink URIs from PDF files.

Primary engine: PyMuPDF (layout-aware, preserves column reading order).
Fallback engine: pypdf (linear stream extraction).
"""

import pypdf
from src.parsers.layout_extractor import LayoutAwarePDFExtractor, HAS_PYMUPDF
from src.parsers.normalizer import normalize_text


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all visible text from a PDF, preserving columnar layout order.

    Uses PyMuPDF's bounding-box block extraction when available, falling
    back to pypdf's linear stream extraction otherwise. Output is passed
    through normalize_text() to fix ligatures and CamelCase merges.
    """
    if HAS_PYMUPDF:
        try:
            text, _ = LayoutAwarePDFExtractor(pdf_path).extract()
            if text.strip():
                return normalize_text(text)
        except Exception as exc:
            print(f"[pdf_parser] Layout extraction failed, falling back to pypdf: {exc}")

    raw_text = ""
    try:
        with open(pdf_path, 'rb') as fh:
            reader = pypdf.PdfReader(fh)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
    except Exception as exc:
        print(f"[pdf_parser] Error reading '{pdf_path}': {exc}")

    return normalize_text(raw_text)


def extract_embedded_links_from_pdf(pdf_path: str) -> list[str]:
    """
    Extract hyperlink URIs from the PDF annotation layer.

    Uses PyMuPDF's page.get_links() when available, falling back to
    manually iterating pypdf's /Annots dictionary entries.
    """
    if HAS_PYMUPDF:
        try:
            _, uris = LayoutAwarePDFExtractor(pdf_path).extract()
            if uris:
                return uris
        except Exception:
            pass

    uris: list[str] = []
    try:
        with open(pdf_path, 'rb') as fh:
            reader = pypdf.PdfReader(fh)
            for page in reader.pages:
                if '/Annots' not in page:
                    continue
                for annot_ref in page['/Annots']:
                    annot = annot_ref.get_object()
                    if annot.get('/Subtype') != '/Link':
                        continue
                    action = annot.get('/A')
                    if action:
                        if hasattr(action, 'get_object'):
                            action = action.get_object()
                        uri = action.get('/URI')
                        if uri:
                            uris.append(uri)
    except Exception as exc:
        print(f"[pdf_parser] Warning: could not read annotations from '{pdf_path}': {exc}")

    return uris
