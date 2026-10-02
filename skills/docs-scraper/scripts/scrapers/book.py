#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "beautifulsoup4",
#   "html2text",
#   "requests",
# ]
# ///
"""Book / monolithic document scraper.

Extracts deterministic, LLM-friendly markdown from PDF, EPUB, DOCX, Markdown,
and plain-text documents. Text layout is cleaned deterministically: running
headers/footers, edge page numbers, and hyphen-wrap artifacts are removed.

Extraction cascade for PDF:
  1. docling        (tables + code markdown, if installed)
  2. pdftotext      (subprocess, `-layout`)
  3. pypdf / pdfminer
"""

import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path
from typing import override

from .base import DocumentationScraper

# ── Text cleanup ─────────────────────────────────────────────────────────────

# Hyphen-wrap join: end-of-line hyphen splits a word across lines.
DEHYPHENATE_RE = re.compile(r"(\w)-\n(\w)")

# Markdown heading, used by the slicing helper.
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

ARABIC_PAGE_RE = re.compile(r"^\d+$")
ROMAN_PAGE_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)

# ~4 chars per token is a safe overestimate for most technical prose.
CHARS_PER_TOKEN = 4


def _boilerplate_key(line: str) -> str:
    """Normalize a line for header/footer repetition counting."""
    return re.sub(r"\s+", " ", line).strip().lower()


def _is_page_number(line: str) -> bool:
    """True if the line is purely an Arabic or Roman-numeral page number."""
    stripped = line.strip()
    if not stripped:
        return False
    if ARABIC_PAGE_RE.fullmatch(stripped):
        return True
    return ROMAN_PAGE_RE.fullmatch(stripped) is not None


def _dehyphenate(text: str) -> str:
    return DEHYPHENATE_RE.sub(r"\1\2", text)


def _strip_edge_lines(lines: list[str], headers: set[str], footers: set[str]) -> list[str]:
    """Remove a boilerplate header/footer or page number from page edges."""
    result = list(lines)

    first_idx = next((i for i, line in enumerate(result) if line.strip()), None)
    if first_idx is not None:
        line = result[first_idx]
        if _boilerplate_key(line) in headers or _is_page_number(line):
            result[first_idx] = ""

    last_idx = next((i for i in range(len(result) - 1, -1, -1) if result[i].strip()), None)
    if last_idx is not None:
        line = result[last_idx]
        if _boilerplate_key(line) in footers or _is_page_number(line):
            result[last_idx] = ""

    return result


def clean_pdftotext(text: str) -> str:
    """Deterministic layout cleanup for raw pdftotext/pypdf output.

    Steps:
      1. Split pages on form-feed ``\\f``.
      2. Count first/last non-blank lines across pages. Any line repeated on
         more than half the pages is a running header/footer and is removed.
      3. Remove edge page numbers (Arabic digits or Roman numerals).
      4. Join hyphen-wrapped words.
    """
    if "\f" not in text:
        return _dehyphenate(text)

    pages = text.split("\f")
    threshold = len(pages) / 2

    edge_lines: list[tuple[str, str]] = []
    for page in pages:
        nonblank = [line for line in page.split("\n") if line.strip()]
        first = nonblank[0] if nonblank else ""
        last = nonblank[-1] if nonblank else ""
        edge_lines.append((first, last))

    first_counter = Counter(_boilerplate_key(f) for f, _ in edge_lines if f)
    last_counter = Counter(_boilerplate_key(l) for _, l in edge_lines if l)
    headers = {key for key, count in first_counter.items() if count > threshold}
    footers = {key for key, count in last_counter.items() if count > threshold}

    cleaned_pages: list[str] = []
    for page in pages:
        lines = _strip_edge_lines(page.split("\n"), headers, footers)
        cleaned_pages.append("\n".join(lines).strip("\n"))

    return _dehyphenate("\n".join(cleaned_pages))


# ── Document slicing ─────────────────────────────────────────────────────────


def slice_document_by_headings(text: str, max_tokens: int = 50_000) -> list[str]:
    """Split text into heading-anchored chunks.

    Chunks start at markdown headings. Any chunk still exceeding
    ``max_tokens`` (est. 4 chars/token) is further hard-split at paragraph
    boundaries to keep monolithic files from being dumped into context.
    """
    max_chars = max_tokens * CHARS_PER_TOKEN

    lines = text.split("\n")
    chunks: list[str] = []
    current: list[str] = []
    for line in lines:
        if HEADING_RE.match(line) and current:
            chunks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current))

    # Hard-split any oversized chunk at paragraph boundaries.
    final_chunks: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
            continue
        paragraphs = re.split(r"\n\s*\n", chunk)
        bucket: list[str] = []
        bucket_len = 0
        for paragraph in paragraphs:
            if bucket and bucket_len + len(paragraph) > max_chars:
                final_chunks.append("\n\n".join(bucket))
                bucket = [paragraph]
                bucket_len = len(paragraph)
            else:
                bucket.append(paragraph)
                bucket_len += len(paragraph)
        if bucket:
            final_chunks.append("\n\n".join(bucket))

    return [c for c in final_chunks if c.strip()]


def extract_line_range(text: str, start: int = 1, end: int | None = None) -> str:
    """Return 1-indexed inclusive line range ``text[start..end]``."""
    lines = text.split("\n")
    start = max(1, start)
    if end is None:
        return "\n".join(lines[start - 1 :])
    return "\n".join(lines[start - 1 : end])


# ── Format routing ───────────────────────────────────────────────────────────

PDF_EXTS = {".pdf"}
EPUB_EXTS = {".epub"}
DOCX_EXTS = {".docx"}
MARKDOWN_EXTS = {".md", ".markdown", ".mdown"}
TEXT_EXTS = {".txt", ".text"}


def detect_format(path: Path | str) -> str:
    """Route a file path to a scraper format key."""
    suffix = Path(path).suffix.lower()
    if suffix in PDF_EXTS:
        return "pdf"
    if suffix in EPUB_EXTS:
        return "epub"
    if suffix in DOCX_EXTS:
        return "docx"
    if suffix in MARKDOWN_EXTS:
        return "markdown"
    if suffix in TEXT_EXTS:
        return "text"
    return "unknown"


# ── Format extractors ────────────────────────────────────────────────────────


def _extract_pdf_docling(path: Path) -> str | None:
    """Try docling (technical PDFs: tables + code markdown)."""
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        return None
    try:
        converter = DocumentConverter()
        result = converter.convert(str(path))
        markdown = result.document.export_to_markdown()
        return markdown if markdown and markdown.strip() else None
    except Exception:
        return None


def _extract_pdf_pdftotext(path: Path) -> str | None:
    """pdftotext -layout fallback via subprocess."""
    try:
        result = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError, subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    return result.stdout if result.stdout.strip() else None


def _extract_pdf_pdfminer(path: Path) -> str | None:
    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        return None
    try:
        text = extract_text(str(path))
        return text if text.strip() else None
    except Exception:
        return None


def _extract_pdf_pypdf(path: Path) -> str | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return _extract_pdf_pdfminer(path)
    try:
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\f".join(pages)
        return text if text.strip() else None
    except Exception:
        return _extract_pdf_pdfminer(path)


def _extract_epub(path: Path) -> str:
    from bs4 import BeautifulSoup

    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".xhtml", ".html", ".htm"))]
        chunks: list[str] = []
        for name in sorted(names):
            soup = BeautifulSoup(zf.read(name), "html.parser")
            chunks.append(soup.get_text("\n"))
        return "\n".join(chunks)


def _extract_docx(path: Path) -> str:
    ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    paragraphs: list[str] = []
    for para in root.iter(f"{{{ns}}}p"):
        texts = [t.text or "" for t in para.iter(f"{{{ns}}}t")]
        paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def _extract_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_text(path: Path | str, fmt: str | None = None) -> tuple[str, str]:
    """Extract text from a document.

    Returns ``(text, method)`` where method names the extractor used.
    """
    p = Path(path)
    fmt = fmt or detect_format(p)

    if fmt == "pdf":
        for extractor, name in (
            (_extract_pdf_docling, "docling"),
            (_extract_pdf_pdftotext, "pdftotext"),
            (_extract_pdf_pypdf, "pypdf"),
        ):
            text = extractor(p)
            if text:
                return text, name
        raise RuntimeError(f"No PDF extractor available for: {p}")

    if fmt == "epub":
        return _extract_epub(p), "epub"
    if fmt == "docx":
        return _extract_docx(p), "docx"
    if fmt == "markdown":
        return _extract_markdown(p), "markdown"
    if fmt == "text":
        return _extract_text(p), "text"
    raise ValueError(f"Unsupported format '{fmt}' for: {p}")


# ── Scraper ──────────────────────────────────────────────────────────────────


class BookScraper(DocumentationScraper):
    """Scrape monolithic documents (PDF, EPUB, DOCX, MD, TXT) to markdown."""

    name: str = "book"
    description: str = (
        "Ingest monolithic documents (PDF, EPUB, DOCX, MD, TXT) into clean, "
        "deterministic markdown. PDFs use docling → pdftotext → pypdf cascade. "
        "TRIGGER: pdf, epub, docx, book, ingest document"
    )

    path: Path
    max_tokens: int

    def __init__(
        self,
        path: str,
        output_dir: Path,
        force: bool = False,
        max_tokens: int = 50_000,
    ) -> None:
        self.path = Path(path)
        self.max_tokens = max_tokens
        super().__init__(
            base_url="",
            output_dir=output_dir,
            force=force,
        )

    def _run_extraction(self) -> tuple[str, str]:
        fmt = detect_format(self.path)
        text, method = extract_text(self.path, fmt=fmt)
        # Only raw text layouts need pdftotext-style cleanup; docling already
        # emits structured markdown.
        if fmt == "pdf" and method != "docling":
            text = clean_pdftotext(text)
        elif fmt == "text":
            text = clean_pdftotext(text)
        return text, method

    @override
    def run(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Document not found: {self.path}")

        text, method = self._run_extraction()

        try:
            from sanitize import sanitize
        except ImportError:
            import sys

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from sanitize import sanitize

        cleaned, report = sanitize(text)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write full document + sliced chunks.
        full_path = self.output_dir / f"{self.path.stem}.md"
        _ = full_path.write_text(cleaned, encoding="utf-8")

        chunks = slice_document_by_headings(cleaned, max_tokens=self.max_tokens)
        if len(chunks) > 1:
            parts_dir = self.output_dir / "parts"
            parts_dir.mkdir(exist_ok=True)
            for idx, chunk in enumerate(chunks, start=1):
                _ = (parts_dir / f"part-{idx:03d}.md").write_text(chunk, encoding="utf-8")

        print(f"Extracted via: {method}")
        print(f"Output: {full_path}")
        if len(chunks) > 1:
            print(f"Sliced into {len(chunks)} chunks under {self.output_dir / 'parts'}")
        if not report["clean"]:
            print("Warning: sanitization removed threats — see report.")
