"""CUDA Runtime and Driver API documentation scraper."""

import re
import shutil
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import DocumentationScraper


class APIScraper(DocumentationScraper):
    """Scraper for CUDA Runtime and Driver API documentation.

    Caching:
    - Default: Uses cached HTML pages if available (with warning)
    - --force: Clears cache and re-fetches
    - Cache location: .cache/cuda-driver/ or .cache/cuda-runtime/
    """

    name = "cuda-api"
    description = """
CUDA Runtime or Driver API documentation scraper.

Scrapes NVIDIA CUDA documentation and converts to searchable markdown format.
Produces two output directories:
  - modules/       Function modules and API groups
  - data-structures/  Struct and type definitions

The scraper:
  - Fetches multiple HTML pages (modules + data structures)
  - Caches raw HTML to .cache/cuda-<driver|runtime>/ (re-use by default)
  - Cleans and processes cached files on each run

Caching:
  - By default, uses cached HTML responses if available
  - Use --force to clear cache and re-fetch
  - Delete .cache/ directory to clear all caches

Examples:
  scrape.py driver                    # Use cache if available
  scrape.py driver --force            # Re-fetch from network
  scrape.py runtime --output-dir ./docs  # Custom output location
"""

    def __init__(
        self,
        api_type: str,
        output_dir: Path,
        force: bool = False,
    ):
        base_urls = {
            "runtime": "https://docs.nvidia.com/cuda/cuda-runtime-api/",
            "driver": "https://docs.nvidia.com/cuda/cuda-driver-api/",
        }
        self.api_type = api_type
        # Override name for cache directory
        self._scraper_name = f"cuda-{api_type}"
        super().__init__(
            base_urls[api_type],
            output_dir,
            force=force,
        )
        # Override cache_dir to use api_type specific name
        self.cache_dir = self.cache_base / self._scraper_name
        self._cached_pages_dir = self.cache_dir / "pages"

    def _fetch_with_cache(self, url: str, cache_filename: str) -> BeautifulSoup | None:
        """Fetch page with unified caching."""
        cache_path = self._cached_pages_dir / cache_filename

        # Use cache if available and not forcing refresh
        if cache_path.exists() and not self.force:
            try:
                content = cache_path.read_text(encoding="utf-8")
                return BeautifulSoup(content, "html.parser")
            except Exception as e:
                print(f"Warning: Failed to read cache: {e}")

        # Fetch from network
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Save to cache
            self._cached_pages_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(response.text, encoding="utf-8")

            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _discover_modules(self) -> list[dict[str, str]]:
        """Discover all module pages."""
        soup = self._fetch_with_cache(
            urljoin(self.base_url, "modules.html"),
            "modules.html"
        )
        if not soup:
            return []

        pattern = (
            r"group__CUDA__.*\.html"
            if self.api_type == "driver"
            else r"group__CUDART.*\.html"
        )
        modules = []
        seen = set()

        for link in soup.find_all("a", href=re.compile(pattern)):
            href = link.get("href")
            title = link.get_text(strip=True)
            if href and title and href not in seen:
                seen.add(href)
                modules.append(
                    {
                        "url": urljoin(self.base_url, href),
                        "filename": href,
                        "title": title,
                    }
                )

        print(f"Discovered {len(modules)} module pages")
        return modules

    def _discover_structures(self) -> list[dict[str, str]]:
        """Discover all data structure pages."""
        soup = self._fetch_with_cache(
            urljoin(self.base_url, "annotated.html"),
            "annotated.html"
        )
        if not soup:
            return []

        pattern = (
            r"structCU.*\.html"
            if self.api_type == "driver"
            else r"(struct|union).*\.html"
        )
        structures = []
        seen = set()

        for link in soup.find_all("a", href=re.compile(pattern)):
            href = link.get("href")
            title = link.get_text(strip=True)
            if href and title and href not in seen:
                seen.add(href)
                structures.append(
                    {
                        "url": urljoin(self.base_url, href),
                        "filename": href,
                        "title": title,
                    }
                )

        print(f"Discovered {len(structures)} data structure pages")
        return structures

    def scrape_page(self, page_info: dict[str, str], output_path: Path) -> bool:
        """Scrape and save a single page."""
        # Use sanitized filename for cache
        cache_filename = self.sanitize_filename(page_info["filename"]) + ".html"
        soup = self._fetch_with_cache(page_info["url"], cache_filename)
        if not soup:
            return False

        markdown = self.convert_to_markdown(soup, page_info["url"])
        header = f"# {page_info['title']}\n\n"
        header += f"**Source:** [{page_info['filename']}]({page_info['url']})\n\n"
        header += "---\n\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(header + markdown, encoding="utf-8")

        print(f"  ✓ Saved: {output_path.name} ({len(header + markdown)} bytes)")
        return True

    def clean_markdown_file(self, file_path: Path) -> tuple[str, int, int]:
        """Clean a markdown file, returning (content, original_size, new_size)."""
        content = file_path.read_text(encoding="utf-8")
        original_size = len(content)

        # Remove duplicate function TOC
        content = self._remove_toc(content)

        # Remove duplicate headers
        content = re.sub(r"(### Functions\s*\n){2,}", "### Functions\n\n", content)

        # Remove footer
        footer_markers = [
            "![](https://docs.nvidia.com/cuda/common/formatting/NVIDIA-LogoBlack.svg)",
            "[Privacy Policy]",
            "Copyright ©",
        ]
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if any(marker in line for marker in footer_markers):
                content = "\n".join(lines[:i])
                break

        # Remove formatting artifacts
        content = content.replace("\n---\n", "\n")
        content = content.replace("​", "")  # Zero-width spaces
        content = re.sub(r" \[inherited\]", "", content)

        # Remove anchor links
        content = re.sub(r"\[([^\]]+)\]\(#[^\)]+\)", r"\1", content)

        # Remove "See also:" sections
        content = self._remove_see_also(content)

        # Remove boilerplate notes
        boilerplate = [
            "Note that this function may also return error codes from previous, asynchronous launches.\n\n",
            "Note that this function may also return error codes from previous, asynchronous launches.",
        ]
        for text in boilerplate:
            content = content.replace(text, "")

        # Remove URLs from links (keep text only)
        content = re.sub(r"\[([^\]]+)\]\(https://[^)]+\)", r"\1", content)
        content = re.sub(r"\[\]\(https://[^)]+\)", "", content)

        # Clean up empty notes and trailing commas
        content = re.sub(r"\nNote:\n\n", "\n", content)
        content = re.sub(r",(\s*)$", r"\1", content, flags=re.MULTILINE)

        # Clean up whitespace
        content = re.sub(r"\n{4,}", "\n\n\n", content)
        content = "\n".join(line.rstrip() for line in content.split("\n"))

        return content, original_size, len(content)

    def _remove_toc(self, content: str) -> str:
        """Remove duplicate function TOC from content."""
        lines = content.split("\n")
        cleaned_lines = []
        in_toc = False
        seen_functions_header = False

        for line in lines:
            # Detect TOC lines (Driver API pattern)
            if (
                ") [" in line
                and "](#" in line
                and any(x in line for x in ["](https://", "CUresult", "CUdeviceptr"])
            ):
                in_toc = True
                continue

            # End of TOC
            if line.strip() == "### Functions":
                if seen_functions_header:
                    in_toc = False
                else:
                    seen_functions_header = True

            if not in_toc:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _remove_see_also(self, content: str) -> str:
        """Remove 'See also:' sections."""
        lines = content.split("\n")
        cleaned_lines = []
        in_see_also = False

        for line in lines:
            if line.strip() == "**See also:**":
                in_see_also = True
                continue

            if in_see_also:
                if (
                    line.startswith("#")
                    or line.startswith("[CUresult]")
                    or line.startswith("[void]")
                ):
                    in_see_also = False
                    cleaned_lines.append(line)
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def run(self) -> None:
        """Execute the scraping workflow."""
        print("=" * 70)
        print(f"CUDA {self.api_type.title()} API Documentation Scraper")
        print("=" * 70)

        # Handle force mode: clear cache
        if self.force and self.cache_dir.exists():
            print(f"\n🗑️  Clearing cache: {self.cache_dir}")
            shutil.rmtree(self.cache_dir)

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check if using cache
        pages_cache = self._cached_pages_dir
        if pages_cache.exists() and not self.force:
            cached_count = len(list(pages_cache.glob("*.html")))
            if cached_count > 0:
                print(f"\n⚡ Using cached HTML responses ({cached_count} files)")
                print(f"   Cache: {self.cache_dir.relative_to(self.output_dir.parent)}")
                print(f"   (Use --force to re-fetch, or delete .cache/ directory)")

        print("\n1. Discovering pages...")
        modules = self._discover_modules()
        structures = self._discover_structures()

        print(
            f"\nTotal pages: {len(modules) + len(structures)} "
            f"(modules: {len(modules)}, structures: {len(structures)})"
        )

        # Scrape to cache
        cache_modules_dir = self.cache_dir / "modules"
        cache_structures_dir = self.cache_dir / "data-structures"
        cache_modules_dir.mkdir(exist_ok=True)
        cache_structures_dir.mkdir(exist_ok=True)

        # Scrape modules
        print("\n2. Scraping module pages...")
        for i, module in enumerate(modules, 1):
            print(f"\n[{i}/{len(modules)}] {module['title']}")
            filename = self.sanitize_filename(module["filename"]) + ".md"
            self.scrape_page(module, cache_modules_dir / filename)

        # Scrape structures
        print("\n3. Scraping data structure pages...")
        for i, struct in enumerate(structures, 1):
            print(f"\n[{i}/{len(structures)}] {struct['title']}")
            filename = self.sanitize_filename(struct["filename"]) + ".md"
            self.scrape_page(struct, cache_structures_dir / filename)

        # Cleanup phase
        print("\n4. Cleaning and processing files...")
        out_modules_dir = self.output_dir / "modules"
        out_structures_dir = self.output_dir / "data-structures"
        out_modules_dir.mkdir(exist_ok=True)
        out_structures_dir.mkdir(exist_ok=True)

        total_original = 0
        total_new = 0
        files_cleaned = 0

        for md_file in sorted(cache_modules_dir.glob("*.md")):
            content, orig_size, new_size = self.clean_markdown_file(md_file)
            (out_modules_dir / md_file.name).write_text(content, encoding="utf-8")
            total_original += orig_size
            total_new += new_size
            files_cleaned += 1

        for md_file in sorted(cache_structures_dir.glob("*.md")):
            content, orig_size, new_size = self.clean_markdown_file(md_file)
            (out_structures_dir / md_file.name).write_text(content, encoding="utf-8")
            total_original += orig_size
            total_new += new_size
            files_cleaned += 1

        reduction = (
            (total_original - total_new) / total_original * 100
            if total_original > 0
            else 0
        )
        print(
            f"  Cleaned {files_cleaned} files: "
            f"{total_original:,} → {total_new:,} bytes ({reduction:.1f}% reduction)"
        )

        # Create index
        print("\n5. Creating index...")
        self._create_index(out_modules_dir, out_structures_dir)

        print("\n" + "=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(f"Output: {self.output_dir} ({total_new/1024/1024:.1f} MB)")

    def _create_index(self, modules_dir: Path, structures_dir: Path) -> None:
        """Create INDEX.md file."""
        modules = sorted(
            [
                {"title": f.stem.replace("-", " ").title(), "filename": f.stem}
                for f in modules_dir.glob("*.md")
            ],
            key=lambda x: x["title"],
        )
        structures = sorted(
            [
                {"title": f.stem.replace("-", " ").title(), "filename": f.stem}
                for f in structures_dir.glob("*.md")
            ],
            key=lambda x: x["title"],
        )

        content = f"# CUDA {self.api_type.title()} API Documentation Index\n\n"
        content += f"**Total modules:** {len(modules)}  \n"
        content += f"**Total data structures:** {len(structures)}  \n\n"

        content += "## Modules\n\n"
        for module in modules:
            filename = self.sanitize_filename(module["filename"]) + ".md"
            content += f"- [{module['title']}](modules/{filename})\n"

        content += "\n## Data Structures\n\n"
        for struct in structures:
            filename = self.sanitize_filename(struct["filename"]) + ".md"
            content += f"- [{struct['title']}](data-structures/{filename})\n"

        index_path = self.output_dir / "INDEX.md"
        index_path.write_text(content, encoding="utf-8")
        print(f"  ✓ Created: {index_path}")
