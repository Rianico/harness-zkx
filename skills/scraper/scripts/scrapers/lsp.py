"""LSP (Language Server Protocol) specification scraper."""

import re
from pathlib import Path

from bs4 import Tag

from .base import DocumentationScraper


class LSPScraper(DocumentationScraper):
    """Scraper for LSP 3.17 specification.

    Follows cuda-driver-docs pattern:
    - Flat structure (all files in one directory)
    - Split only at h4 level (include h4 content within h3 files)
    - Convert internal anchor links to local markdown file references

    Caching:
    - Default: Uses cached HTML if available (with warning)
    - --force: Clears cache and re-fetches
    - Cache location: .cache/lsp/spec.html
    """

    # Pattern to match emoji anchor suffixes (e.g., "--arrow_right_hook" or "-leftwards_arrow_with_hook")
    EMOJI_ANCHOR_PATTERN = re.compile(r"-{1,2}(arrow_|leftwards_|rightwards_)[\w_]+$")

    name = "lsp"
    description = """
LSP 3.17 (Language Server Protocol) specification scraper.

Scrapes Microsoft LSP 3.17 specification and converts to markdown.
Creates numbered files (0001-xxx.md) for each section.

The scraper:
  - Splits at h4 level for granular, LLM-friendly files
  - Keeps Change Log as a single file (no version splitting)
  - Converts internal anchor links to local file references
  - Caches raw HTML to .cache/lsp/ (re-use by default)

Caching:
  - By default, uses cached HTML response if available
  - Use --force to clear cache and re-fetch
  - Delete .cache/ directory to clear all caches

Examples:
  scrape.py lsp                           # Use cache if available
  scrape.py lsp --force                   # Re-fetch from network
  scrape.py lsp --output-dir ./lsp-docs   # Custom output location
"""

    def __init__(self, output_dir: Path, force: bool = False):
        super().__init__(
            base_url="https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/",
            output_dir=output_dir,
            force=force,
        )
        self.sections: list[dict] = []  # Store for link resolution

    def _clean_anchor(self, anchor: str) -> str:
        """Remove emoji anchor suffix from anchor ID.

        LSP spec anchors have emoji suffixes like:
        - "inline-value-refresh-request--arrow_right_hook"
        This strips the "--<emoji_name>" suffix.
        """
        if not anchor:
            return anchor
        return self.EMOJI_ANCHOR_PATTERN.sub("", anchor)

    def run(self) -> None:
        """Execute LSP spec scraping workflow."""
        print("=" * 70)
        print("LSP 3.17 Specification Scraper")
        print("=" * 70)

        soup = self.fetch_page(self.base_url, cache_file="spec.html")
        if not soup:
            print("Failed to fetch documentation")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print("\nExtracting sections (split at h4 level)...")
        self.sections = self._extract_sections(soup)
        print(f"Found {len(self.sections)} sections")

        # Build anchor-to-file mapping for link resolution
        self.anchor_map = self._build_anchor_map()

        print("\nSaving sections...")
        for i, section in enumerate(self.sections, 1):
            self._save_section(section, i)

        # Create index
        print("\nCreating index...")
        self._create_index()

        print(f"\n✓ Complete! Documentation saved to: {self.output_dir}")

    def _extract_sections(self, soup) -> list[dict]:
        """Extract sections from LSP spec page, splitting at h4 level.

        h1 sections are TOC/index pages - skipped.
        h2-h4 sections are the actual content units (API definitions, requests, etc).

        Exception: Change Log section is kept as a single file (no h4 splitting).
        """
        content = None
        for selector in [
            {"class": "md-content"},
            {"role": "main"},
            {"class": "document"},
            {"class": "body"},
        ]:
            content = soup.find("div", selector) or soup.find("main", selector)
            if content:
                break

        if not content:
            content = soup.find("body")

        if not content:
            return []

        sections = []
        # Only process h2, h3, h4 - skip h1 (TOC pages)
        headings = content.find_all(["h2", "h3", "h4"])

        # Track if we're inside Change Log section
        in_change_log = False

        for heading in headings:
            # Remove emoji img tags from heading before extracting text
            heading_copy = heading.__copy__()
            for img in heading_copy.find_all("img", class_="emoji"):
                img.decompose()

            heading_text = heading_copy.get_text(strip=True)
            # Clean up empty parentheses left by removed emoji (e.g., "Title ()" -> "Title")
            heading_text = re.sub(r"\s*\(\s*\)", "", heading_text).strip()
            if not heading_text:
                continue

            # Check if entering/exiting Change Log section (h2 or h3)
            if heading.name in ["h2", "h3"]:
                if "change log" in heading_text.lower():
                    in_change_log = True
                elif in_change_log:
                    in_change_log = False

            # Skip h4 headings inside Change Log (they become content, not sections)
            if in_change_log and heading.name == "h4":
                continue

            # Extract section number (LSP uses formats like "3.17", "3.17.1")
            section_match = re.match(r"^(\d+(?:\.\d+)*)\.?\s*(.+)$", heading_text)
            section_num = section_match.group(1) if section_match else ""
            title = section_match.group(2) if section_match else heading_text

            # Skip very short or navigation-like titles
            if len(title) < 2 or title.lower() in ["next", "previous", "contents"]:
                continue

            anchor_id = heading.get("id", "") or (
                heading.find("a").get("id", "") if heading.find("a") else ""
            )
            # Clean emoji suffix from anchor (e.g., "--arrow_right_hook")
            anchor_id = self._clean_anchor(anchor_id)
            level = int(heading.name[1]) - 1  # h2 -> 1, h3 -> 2, h4 -> 3

            # Collect content until next heading
            # In Change Log: stop at next h2/h3 only (include h4 content)
            # Otherwise: stop at next h2/h3/h4
            content_elements = []
            current = heading.next_sibling
            while current:
                if isinstance(current, Tag) and current.name in ["h1", "h2", "h3", "h4"]:
                    if in_change_log and current.name == "h4":
                        # Include h4 as content within Change Log
                        content_elements.append(current)
                        current = current.next_sibling
                        continue
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

    def _build_anchor_map(self) -> dict[str, str]:
        """Build mapping from anchor IDs to local markdown file paths.

        Uses case-insensitive matching since HTML anchors may have different
        casing than the actual id attributes.
        """
        anchor_map = {}
        for i, section in enumerate(self.sections, 1):
            if section["anchor"]:
                filename = self._make_filename(section, i)
                # Store lowercase key for case-insensitive matching
                anchor_map[section["anchor"].lower()] = filename
        return anchor_map

    def _make_filename(self, section: dict, index: int) -> str:
        """Generate filename with numeric prefix."""
        base_name = self.sanitize_filename(section["title"], section["section_num"])
        return f"{index:04d}-{base_name}.md"

    def _save_section(self, section: dict, index: int) -> None:
        """Save section as markdown file with local link resolution."""
        filename = self._make_filename(section, index)
        markdown_parts = []

        # Add heading
        level_prefix = "#" * (section["level"] + 1)
        title_with_num = (
            f"{section['section_num']}. {section['title']}"
            if section["section_num"]
            else section["title"]
        )
        markdown_parts.append(f"{level_prefix} {title_with_num}\n")

        # Add source link
        source_anchor = section["anchor"] or section["title"].lower().replace(" ", "-")
        source_url = f"{self.base_url}#{source_anchor}"
        markdown_parts.append(f"\n**Source:** {source_url}\n")

        # Add content
        for element in section["content"]:
            # Remove navigation and headerlink elements
            for class_name in [
                "headerlink",
                "viewcode-link",
                "navigation",
                "related",
                "md-nav",
            ]:
                for unwanted in element.find_all(class_=class_name):
                    unwanted.decompose()

            # Remove emoji images from content headings
            for img in element.find_all("img", class_="emoji"):
                img.decompose()

            # Convert anchor links to local file references
            for link in element.find_all("a", href=True):
                href = link.get("href", "")
                if href.startswith("#"):
                    # Clean emoji suffix and lowercase for matching
                    anchor = self._clean_anchor(href[1:]).lower()
                    if anchor in self.anchor_map:
                        link["href"] = self.anchor_map[anchor]
                    # else: keep the original anchor link

            # Remove empty anchor links (anchors with no text content)
            for link in element.find_all("a"):
                if not link.get_text(strip=True) and not link.find("img"):
                    link.decompose()

            md = self.h2t.handle(str(element))
            if md.strip():
                markdown_parts.append(md)

        markdown = "\n\n".join(markdown_parts)
        markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

        # Clean up common artifacts
        markdown = re.sub(r"\[Edit this page\]\([^)]+\)", "", markdown)
        markdown = re.sub(r"\[Previous\]\([^)]+\)", "", markdown)
        markdown = re.sub(r"\[Next\]\([^)]+\)", "", markdown)

        # Write file
        output_file = self.output_dir / filename
        output_file.write_text(markdown.strip(), encoding="utf-8")
        print(f"  Saved: {output_file.name}")

    def _create_index(self) -> None:
        """Create INDEX.md file."""
        files = sorted(self.output_dir.glob("*.md"))
        # Count only content files (exclude INDEX.md)
        content_files = [f for f in files if f.name != "INDEX.md"]

        content = "# LSP 3.17 Specification Index\n\n"
        content += f"**Total sections:** {len(content_files)}\n\n"

        content += "## Sections\n\n"
        for md_file in files:
            if md_file.name == "INDEX.md":
                continue
            # Extract title from filename (strip numeric prefix)
            title = md_file.stem
            title = re.sub(r"^\d{4}-", "", title).replace("-", " ").title()
            content += f"- [{title}]({md_file.name})\n"

        index_path = self.output_dir / "INDEX.md"
        index_path.write_text(content, encoding="utf-8")
        print(f"  ✓ Created: {index_path}")
