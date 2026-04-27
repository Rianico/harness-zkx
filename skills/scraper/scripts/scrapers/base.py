#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "html2text",
#   "requests",
# ]
# ///
"""Base scraper class for documentation extraction."""

import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urljoin

import html2text
import requests
from bs4 import BeautifulSoup, Tag


class DocumentationScraper(ABC):
    """Base class for documentation scrapers with unified caching.

    Caching behavior:
      - Default: Use cached response if available (with warning)
      - --force: Clear cache and re-fetch
      - Cache location: .cache/<scraper-name>/

    Users can manually delete the .cache directory to clear all caches.
    """

    name: str = "base"
    description: str = "Base documentation scraper"

    def __init__(
        self,
        base_url: str,
        output_dir: Path,
        force: bool = False,
        cache_base: Path | None = None,
    ):
        self.base_url = base_url
        self.output_dir = output_dir
        self.force = force

        # Unified cache directory: .cache/<scraper-name>/
        self.cache_base = cache_base or (output_dir.parent / ".cache")
        self.cache_dir = self.cache_base / self.name

        # HTTP session with headers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # html2text configuration
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.skip_internal_links = False
        self.h2t.unicode_snob = True
        self.h2t.decode_errors = "ignore"

    def fetch_page(self, url: str, cache_file: str = "page.html") -> BeautifulSoup | None:
        """Fetch and parse a webpage with caching.

        Args:
            url: URL to fetch
            cache_file: Filename for cache storage (relative to cache_dir)

        Returns:
            BeautifulSoup object or None on error
        """
        cache_path = self.cache_dir / cache_file

        # Use cache if available and not forcing refresh
        if cache_path.exists() and not self.force:
            print(f"⚡ Using cached response: {cache_path.relative_to(self.cache_base.parent)}")
            print(f"   (Use --force to re-fetch, or delete .cache/ directory)")
            try:
                content = cache_path.read_text(encoding="utf-8")
                return BeautifulSoup(content, "html.parser")
            except Exception as e:
                print(f"Warning: Failed to read cache: {e}")
                print("Falling back to network request...")

        # Force mode: clear cache
        if self.force and self.cache_dir.exists():
            print(f"🗑️  Clearing cache: {self.cache_dir}")
            shutil.rmtree(self.cache_dir)

        # Fetch from network
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save to cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(response.text, encoding="utf-8")
            print(f"   Cached to: {cache_path.relative_to(self.cache_base.parent)}")

            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def sanitize_filename(self, name: str, section_num: str = "") -> str:
        """Convert title to safe filename."""
        # Remove section number from title if present
        name = re.sub(r"^\d+(\.\d+)*\.?\s*", "", name)
        name = re.sub(r"#.*$", "", name)  # Remove anchors
        name = re.sub(r"\.html?$", "", name)  # Remove extensions
        name = re.sub(r"[^\w\s\-_.]", "", name)  # Remove special chars
        name = re.sub(r"\s+", "-", name)  # Spaces to hyphens
        name = name.lower().strip("-")

        # Add section number prefix if provided
        if section_num:
            name = f"{section_num}-{name}"

        return name if name else "index"

    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract main documentation content from page."""
        content = soup.find("div", class_="contents")
        if not content:
            content = soup.find("div", id="doc-content") or soup.find("body")
        if not content:
            raise ValueError("Could not find main content")

        # Remove navigation elements
        for nav in content.find_all(
            ["div", "ul"],
            class_=["header", "headertitle", "navigate", "breadcrumb"],
        ):
            nav.decompose()

        for elem in content.find_all(
            ["div"],
            id=["top", "titlearea", "projectlogo", "projectname", "projectbrief"],
        ):
            elem.decompose()

        # Remove large navigation lists
        for textblock in content.find_all("div", class_="textblock"):
            links = textblock.find_all("a", href=True)
            if len(links) > 10:
                html_links = [
                    link for link in links if link.get("href", "").endswith(".html")
                ]
                if len(html_links) > 10:
                    textblock.decompose()

        return content

    def convert_to_markdown(self, soup: BeautifulSoup, page_url: str) -> str:
        """Convert HTML to markdown."""
        content = self.extract_main_content(soup)

        # Make image URLs absolute
        for img in content.find_all("img"):
            src = img.get("src")
            if src and not src.startswith(("http://", "https://")):
                img["src"] = urljoin(page_url, src)

        # Make link URLs absolute
        for link in content.find_all("a"):
            href = link.get("href")
            if href and not href.startswith(("http://", "https://", "#", "mailto:")):
                link["href"] = urljoin(page_url, href)

        markdown = self.h2t.handle(str(content))
        markdown = self._clean_navigation_markdown(markdown)
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)
        return markdown.strip()

    def _clean_navigation_markdown(self, markdown: str) -> str:
        """Remove navigation cruft from markdown."""
        lines = markdown.split("\n")
        cleaned_lines = []
        in_nav = False
        found_header = False

        for line in lines:
            if (
                "NVIDIA" in line
                and "Toolkit Documentation" in line
                and not found_header
            ):
                in_nav = True
                continue

            if line.startswith("###") or (
                line.startswith("##") and "Public Members" in line
            ):
                in_nav = False
                found_header = True

            if not in_nav:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    @abstractmethod
    def run(self) -> None:
        """Execute the scraping workflow."""
        pass

    @classmethod
    def get_help(cls) -> str:
        """Return help text for this scraper."""
        return cls.description
