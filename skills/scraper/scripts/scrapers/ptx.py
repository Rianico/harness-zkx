"""PTX ISA documentation scraper."""

import re
from pathlib import Path

from bs4 import Tag

from .base import DocumentationScraper


class PTXScraper(DocumentationScraper):
    """Scraper for PTX ISA single-page documentation.

    Caching:
    - Default: Uses cached HTML if available (with warning)
    - --force: Clears cache and re-fetches
    - Cache location: .cache/ptx/index.html
    """

    name = "ptx"
    description = """
PTX ISA (Parallel Thread Execution) documentation scraper.

Scrapes NVIDIA PTX ISA documentation and converts to markdown.
Creates a directory structure organized by chapters.

The scraper:
  - Splits documentation by chapter/section hierarchy
  - Preserves code examples and tables
  - Caches raw HTML to .cache/ptx/ (re-use by default)

Caching:
  - By default, uses cached HTML response if available
  - Use --force to clear cache and re-fetch
  - Delete .cache/ directory to clear all caches

Examples:
  scrape.py ptx                           # Use cache if available
  scrape.py ptx --force                   # Re-fetch from network
  scrape.py ptx --output-dir ./ptx-docs   # Custom output location
"""

    def __init__(self, output_dir: Path, force: bool = False):
        super().__init__(
            base_url="https://docs.nvidia.com/cuda/parallel-thread-execution/",
            output_dir=output_dir,
            force=force,
        )

    def run(self) -> None:
        """Execute PTX scraping workflow."""
        print("=" * 70)
        print("PTX ISA Documentation Scraper")
        print("=" * 70)

        soup = self.fetch_page(f"{self.base_url}index.html", cache_file="index.html")
        if not soup:
            print("Failed to fetch documentation")
            return

        print("\nExtracting sections...")
        sections = self._extract_sections(soup)
        print(f"Found {len(sections)} sections")

        # Organize by chapters
        current_chapter_dir = self.output_dir
        for section in sections:
            if "notice" in section["title"].lower() and section["level"] == 0:
                continue

            if section["level"] == 0:
                chapter_name = self.sanitize_filename(
                    section["title"], section["section_num"]
                )
                current_chapter_dir = self.output_dir / chapter_name
                current_chapter_dir.mkdir(parents=True, exist_ok=True)
                print(f"\nChapter: {section['title']}")

            self._save_section(section, current_chapter_dir)

        print(f"\n✓ Complete! Documentation saved to: {self.output_dir}")

    def _extract_sections(self, soup):
        """Extract sections from single-page documentation."""
        content = None
        for selector in [
            {"role": "main"},
            {"class": "document"},
            {"class": "body"},
            {"itemprop": "articleBody"},
        ]:
            content = soup.find("div", selector) or soup.find("section", selector)
            if content:
                break

        if not content:
            return []

        sections = []
        headings = content.find_all(["h1", "h2", "h3", "h4"])

        for heading in headings:
            heading_text = heading.get_text(strip=True)
            if not heading_text:
                continue

            # Extract section number
            section_match = re.match(r"^(\d+(?:\.\d+)*)\.\s*(.+)$", heading_text)
            section_num = section_match.group(1) if section_match else ""
            title = section_match.group(2) if section_match else heading_text

            anchor_id = heading.get("id", "") or (
                heading.find("a").get("id", "") if heading.find("a") else ""
            )
            level = int(heading.name[1]) - 1

            # Collect content
            content_elements = []
            current = heading.next_sibling
            while current:
                if isinstance(current, Tag) and current.name in [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                ]:
                    current_level = int(current.name[1]) - 1
                    if current_level <= level:
                        break
                if isinstance(current, Tag):
                    content_elements.append(current)
                current = current.next_sibling

            sections.append(
                {
                    "title": title,
                    "section_num": section_num,
                    "level": level,
                    "anchor": anchor_id,
                    "content": content_elements,
                }
            )

        return sections

    def _save_section(self, section: dict, parent_dir: Path) -> None:
        """Save section as markdown file."""
        filename = self.sanitize_filename(section["title"], section["section_num"])
        markdown_parts = []

        # Add heading
        level_prefix = "#" * (section["level"] + 1)
        title_with_num = (
            f"{section['section_num']}. {section['title']}"
            if section["section_num"]
            else section["title"]
        )
        markdown_parts.append(f"{level_prefix} {title_with_num}\n")

        # Add content
        for element in section["content"]:
            for class_name in ["headerlink", "viewcode-link", "navigation", "related"]:
                for unwanted in element.find_all(class_=class_name):
                    unwanted.decompose()

            md = self.h2t.handle(str(element))
            # Fix image URLs
            md = re.sub(
                r"!\[(.*?)\]\(_images/(.*?)\)",
                r"![\1](https://docs.nvidia.com/cuda/parallel-thread-execution/_images/\2)",
                md,
            )
            if md:
                markdown_parts.append(md)

        markdown = "\n\n".join(markdown_parts)
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

        # Write file
        output_file = parent_dir / f"{filename}.md"
        output_file.write_text(markdown, encoding="utf-8")
        print(f"  Saved: {output_file.name}")
