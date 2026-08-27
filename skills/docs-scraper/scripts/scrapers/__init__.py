"""Documentation scraper plugins for various technical documentation sources."""

from .base import DocumentationScraper
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
    "RustScraper",
    "SiteScraper",
    "SkillsScraper",
    "detect_rust_project",
    "parse_llms_txt",
    "parse_sitemap_xml",
    "parse_skillsh_input",
]
