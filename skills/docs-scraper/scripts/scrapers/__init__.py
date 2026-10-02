"""Documentation scraper plugins for various technical documentation sources."""

from .base import DocumentationScraper
from .book import (
    BookScraper,
    clean_pdftotext,
    detect_format,
    extract_text,
    slice_document_by_headings,
)
from .cuda_api import APIScraper
from .lsp import LSPScraper
from .ptx import PTXScraper
from .rust import RustScraper, detect_rust_project
from .site import SiteScraper, parse_llms_txt, parse_sitemap_xml
from .skillsh import SkillsScraper, parse_skillsh_input

__all__ = [
    "DocumentationScraper",
    "APIScraper",
    "PTXScraper",
    "LSPScraper",
    "BookScraper",
    "RustScraper",
    "SiteScraper",
    "SkillsScraper",
    "detect_rust_project",
    "parse_llms_txt",
    "parse_sitemap_xml",
    "parse_skillsh_input",
    "clean_pdftotext",
    "detect_format",
    "extract_text",
    "slice_document_by_headings",
]
