"""Tests for book.py — monolithic document scraper helpers."""

import sys
from pathlib import Path

_scraper_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts" / "scrapers"
).resolve()
if str(_scraper_path) not in sys.path:
    sys.path.insert(0, str(_scraper_path))

_scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "docs-scraper" / "scripts"
).resolve()
if str(_scripts_path) not in sys.path:
    sys.path.insert(0, str(_scripts_path))

import pytest
from scrapers.book import (  # type: ignore[import-not-found]  # noqa: E402
    BookScraper,
    clean_pdftotext,
    detect_format,
    extract_line_range,
    extract_text,
    slice_document_by_headings,
)


class TestDetectFormat:
    """Format routing from file extensions."""

    def test_pdf(self):
        assert detect_format("doc.pdf") == "pdf"

    def test_epub(self):
        assert detect_format("book.epub") == "epub"

    def test_docx(self):
        assert detect_format("report.docx") == "docx"

    def test_markdown(self):
        assert detect_format("notes.md") == "markdown"
        assert detect_format("notes.markdown") == "markdown"

    def test_text(self):
        assert detect_format("notes.txt") == "text"

    def test_case_insensitive(self):
        assert detect_format("DOC.PDF") == "pdf"

    def test_unknown(self):
        assert detect_format("file.xyz") == "unknown"

    def test_path_object(self):
        assert detect_format(Path("a/b/file.docx")) == "docx"


class TestCleanPdftotext:
    """Deterministic layout cleanup for raw pdftotext output."""

    def test_single_page_dehyphenates(self):
        text = "The quick brown fox-\njumps over the lazy dog."
        assert clean_pdftotext(text) == "The quick brown foxjumps over the lazy dog."

    def test_no_form_feed_is_noop(self):
        text = "plain text without form feeds"
        assert clean_pdftotext(text) == text

    def test_strips_arabic_page_numbers(self):
        text = "\fPage one content\n1\n\fPage two content\n2\n"
        cleaned = clean_pdftotext(text)
        assert "1" not in cleaned.split("\n")
        assert "2" not in cleaned.split("\n")
        assert "Page one content" in cleaned
        assert "Page two content" in cleaned

    def test_strips_roman_page_numbers(self):
        text = "\fcontent a\niv\n\fcontent b\nv\n"
        cleaned = clean_pdftotext(text)
        assert "iv" not in cleaned
        assert "v" not in cleaned

    def test_strips_repeated_headers(self):
        header = "Documentation Manual"
        text = f"{header}\n\nBody one\n\f{header}\n\nBody two\n\f{header}\n\nBody three\n"
        cleaned = clean_pdftotext(text)
        assert "Documentation Manual" not in cleaned
        assert "Body one" in cleaned
        assert "Body two" in cleaned
        assert "Body three" in cleaned

    def test_keeps_non_repeated_lines(self):
        text = "\fHeader once\nBody one\n\fBody two\n\fBody three\n"
        cleaned = clean_pdftotext(text)
        assert "Header once" in cleaned
        assert "Body one" in cleaned

    def test_threshold_requires_majority(self):
        # H appears on exactly 2 of 4 pages (50%), not >50% → kept.
        text = "H\nA\n\fA\nX\n\fB\nY\n\fH\nB\n"
        cleaned = clean_pdftotext(text)
        assert "H" in cleaned


class TestSliceDocumentByHeadings:
    """Heading-anchored chunking."""

    def test_splits_at_headings(self):
        text = "# One\ncontent one\n# Two\ncontent two\n"
        chunks = slice_document_by_headings(text)
        assert len(chunks) == 2
        assert "# One" in chunks[0]
        assert "# Two" in chunks[1]

    def test_no_headings_single_chunk(self):
        text = "plain prose without headings"
        chunks = slice_document_by_headings(text)
        assert chunks == ["plain prose without headings"]

    def test_oversized_chunk_split_at_paragraphs(self):
        # max_tokens=1 → max_chars=4, forces paragraph-level splitting.
        text = "aaaa\n\nbbbb\n\ncccc"
        chunks = slice_document_by_headings(text, max_tokens=1)
        assert all(len(c) <= 4 for c in chunks)
        assert "".join(chunks).replace("\n", "") == "aaaabbbbcccc"

    def test_empty_text(self):
        assert slice_document_by_headings("") == []


class TestExtractLineRange:
    """1-indexed inclusive line slicing."""

    def test_full_range(self):
        text = "a\nb\nc\nd"
        assert extract_line_range(text, 1, 2) == "a\nb"

    def test_open_ended(self):
        text = "a\nb\nc\nd"
        assert extract_line_range(text, 3) == "c\nd"

    def test_start_clamped_to_one(self):
        text = "a\nb"
        assert extract_line_range(text, 0, 1) == "a"

    def test_single_line(self):
        text = "a\nb\nc"
        assert extract_line_range(text, 2, 2) == "b"


class TestExtractText:
    """Text extraction from non-PDF formats (no external deps needed)."""

    def test_extract_markdown(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nBody text", encoding="utf-8")
        text, method = extract_text(f)
        assert text == "# Title\n\nBody text"
        assert method == "markdown"

    def test_extract_text(self, tmp_path):
        f = tmp_path / "doc.txt"
        f.write_text("hello\nworld", encoding="utf-8")
        text, method = extract_text(f)
        assert text == "hello\nworld"
        assert method == "text"

    def test_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "doc.xyz"
        f.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported format"):
            _ = extract_text(f)


class TestBookScraper:
    """BookScraper instantiation and markdown ingestion."""

    def test_run_writes_markdown(self, tmp_path):
        src = tmp_path / "book.md"
        src.write_text("# Heading\n\nSome body text.", encoding="utf-8")
        out = tmp_path / "out"
        scraper = BookScraper(path=str(src), output_dir=out)
        scraper.run()
        assert (out / "book.md").exists()
        content = (out / "book.md").read_text(encoding="utf-8")
        assert "# Heading" in content
        assert "Some body text." in content

    def test_run_slices_multiple_headings(self, tmp_path):
        src = tmp_path / "book.md"
        src.write_text("# A\naaa\n# B\nbbb\n", encoding="utf-8")
        out = tmp_path / "out"
        scraper = BookScraper(path=str(src), output_dir=out)
        scraper.run()
        parts_dir = out / "parts"
        assert parts_dir.exists()
        part_files = sorted(parts_dir.glob("*.md"))
        assert len(part_files) == 2

    def test_missing_file_raises(self, tmp_path):
        out = tmp_path / "out"
        scraper = BookScraper(path=str(tmp_path / "nope.md"), output_dir=out)
        with pytest.raises(FileNotFoundError):
            scraper.run()
