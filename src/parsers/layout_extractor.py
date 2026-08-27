"""
src/parsers/layout_extractor.py
───────────────────────────────
Layout-aware PDF text extraction using PyMuPDF.

Solves the "word salad" problem on multi-column resumes by:
  1. Extracting text blocks with exact bounding-box geometry (x0, y0, x1, y1).
  2. Detecting vertical column separators via horizontal whitespace gaps.
  3. Assigning blocks to columns and sorting each column top-to-bottom.
  4. Merging full-width elements (headers/banners) and columns in true
     human reading order (left column fully, then right column, etc.).
  5. Extracting embedded link annotations (/URI, mailto:) from the page.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class ExtractorConfig:
    # Blocks wider than this fraction of the page are treated as full-width
    full_width_ratio: float = 0.72
    # Minimum empty horizontal gap (fraction of page width) to split columns
    min_gap_ratio: float = 0.025
    # Minimum gap size in PDF points
    min_gap_points: float = 12.0
    # Each column must be at least this wide (fraction of page width)
    min_column_width_ratio: float = 0.12
    block_separator: str = "\n"
    page_separator: str = "\n\n"


@dataclass
class _Block:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_no: int
    block_type: int

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def center_x(self) -> float:
        return (self.x0 + self.x1) / 2


class LayoutAwarePDFExtractor:
    """
    Extracts text from a PDF in visual reading order, preserving columns.

    Returns (text: str, links: list[str]) via .extract().
    """

    _TEXT_BLOCK = 0

    def __init__(self, pdf_path: str | Path, config: Optional[ExtractorConfig] = None):
        self.pdf_path = Path(pdf_path)
        self.config = config or ExtractorConfig()
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

    # ── Public API ────────────────────────────────────────────────────────────

    def extract(self) -> Tuple[str, List[str]]:
        """Return (full_text, embedded_link_uris)."""
        pages: List[str] = []
        links: List[str] = []

        with pymupdf.open(self.pdf_path) as doc:
            for page in doc:
                for link in page.get_links():
                    uri = link.get("uri")
                    if uri:
                        links.append(uri)
                page_text = self._extract_page(page)
                if page_text.strip():
                    pages.append(page_text.strip())

        return self.config.page_separator.join(pages), links

    # ── Page extraction ───────────────────────────────────────────────────────

    def _extract_page(self, page: pymupdf.Page) -> str:
        blocks = self._get_text_blocks(page)
        if not blocks:
            return ""
        separators = self._detect_columns(blocks, page.rect.width)
        if not separators:
            ordered = sorted(blocks, key=lambda b: (round(b.y0, 1), round(b.x0, 1)))
        else:
            ordered = self._multi_column_order(blocks, separators, page.rect.width)
        return self._blocks_to_text(ordered)

    def _get_text_blocks(self, page: pymupdf.Page) -> List[_Block]:
        raw = page.get_text("blocks", sort=False)
        blocks = []
        for item in raw:
            if len(item) < 7:
                continue
            x0, y0, x1, y1, text, block_no, block_type = item[:7]
            b = _Block(float(x0), float(y0), float(x1), float(y1),
                       text, int(block_no), int(block_type))
            if b.block_type == self._TEXT_BLOCK and self._clean(b.text):
                blocks.append(b)
        return blocks

    # ── Column detection ──────────────────────────────────────────────────────

    def _detect_columns(self, blocks: List[_Block], page_width: float) -> List[float]:
        """Return X-axis separator coordinates between columns."""
        if page_width <= 0:
            return []

        useful = [b for b in blocks if b.width / page_width < self.config.full_width_ratio]
        if len(useful) < 2:
            return []

        edges = {0.0, page_width}
        for b in useful:
            edges.add(max(0.0, min(page_width, b.x0)))
            edges.add(max(0.0, min(page_width, b.x1)))

        gaps: List[Tuple[float, float]] = []
        for left, right in zip(sorted(edges), sorted(edges)[1:]):
            gap = right - left
            if gap < self.config.min_gap_points or gap / page_width < self.config.min_gap_ratio:
                continue
            mid = (left + right) / 2
            if not any(b.x0 <= mid <= b.x1 for b in useful):
                gaps.append((left, right))

        separators: List[float] = []
        for left, right in self._merge_intervals(gaps):
            sep = (left + right) / 2
            if (
                sep / page_width >= self.config.min_column_width_ratio
                and (page_width - sep) / page_width >= self.config.min_column_width_ratio
                and any(b.x1 <= sep for b in useful)
                and any(b.x0 >= sep for b in useful)
            ):
                separators.append(sep)

        return sorted(set(separators))

    # ── Multi-column ordering ─────────────────────────────────────────────────

    def _multi_column_order(self, blocks: List[_Block], separators: List[float], page_width: float) -> List[_Block]:
        regions = self._build_regions(separators, page_width)
        columns: List[List[_Block]] = [[] for _ in regions]
        full_width: List[_Block] = []

        for b in blocks:
            if b.width / page_width >= self.config.full_width_ratio:
                full_width.append(b)
                continue
            placed = False
            for i, (left, right) in enumerate(regions):
                if left <= b.center_x <= right:
                    columns[i].append(b)
                    placed = True
                    break
            if not placed:
                best = self._best_column(b, regions)
                if best is not None:
                    columns[best].append(b)
                else:
                    full_width.append(b)

        for col in columns:
            col.sort(key=lambda b: (round(b.y0, 1), round(b.x0, 1)))
        full_width.sort(key=lambda b: (round(b.y0, 1), round(b.x0, 1)))

        return self._interleave(columns, full_width)

    def _interleave(self, columns: List[List[_Block]], full_width: List[_Block]) -> List[_Block]:
        """Combine columns and full-width blocks in vertical reading order."""
        if not full_width:
            return [b for col in columns for b in col]

        result: List[_Block] = []
        consumed: set[int] = set()

        first_col_y = min((b.y0 for col in columns for b in col), default=float('inf'))
        for fw in full_width:
            if fw.y0 <= first_col_y:
                result.append(fw)
                consumed.add(id(fw))

        for col in columns:
            for b in col:
                result.append(b)
                for fw in full_width:
                    if id(fw) not in consumed and fw.y0 <= b.y1:
                        result.append(fw)
                        consumed.add(id(fw))

        result.extend(fw for fw in full_width if id(fw) not in consumed)
        return result

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _build_regions(separators: List[float], page_width: float) -> List[Tuple[float, float]]:
        coords = [0.0] + separators + [page_width]
        return [(coords[i], coords[i + 1]) for i in range(len(coords) - 1)]

    @staticmethod
    def _best_column(block: _Block, regions: List[Tuple[float, float]]) -> Optional[int]:
        best_idx, best_overlap = None, 0.0
        for i, (left, right) in enumerate(regions):
            overlap = max(0.0, min(block.x1, right) - max(block.x0, left))
            if overlap > best_overlap:
                best_overlap, best_idx = overlap, i
        return best_idx

    @staticmethod
    def _merge_intervals(intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        if not intervals:
            return []
        merged = [sorted(intervals)[0]]
        for start, end in sorted(intervals)[1:]:
            if start <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        return merged

    @staticmethod
    def _clean(text: str) -> str:
        lines = [re.sub(r'[ \t]+', ' ', ln).strip() for ln in text.splitlines() if ln.strip()]
        return '\n'.join(lines).strip()

    def _blocks_to_text(self, blocks: List[_Block]) -> str:
        chunks = [self._clean(b.text) for b in blocks if self._clean(b.text)]
        return re.sub(r'\n{3,}', '\n\n', self.config.block_separator.join(chunks)).strip()
