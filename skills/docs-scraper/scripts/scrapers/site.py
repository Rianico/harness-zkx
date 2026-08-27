#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "html2text",
#   "requests",
# ]
# ///
"""Site scraper for generic documentation sites.

Supports dual-mode operation:
- Discovery mode: Find URLs via llms.txt and/or sitemap.xml
- Fetch mode: Fetch specific URLs and convert to markdown
"""

import json
import re
import warnings
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .base import DocumentationScraper


def parse_sitemap_xml(content: str, base_url: str | None = None) -> list[str]:
    """Parse sitemap.xml content and extract URLs.

    Handles both regular sitemaps and sitemap indexes.

    Args:
        content: XML content of sitemap
        base_url: Base URL for resolving relative URLs

    Returns:
        List of URLs (URLs from <loc> tags, or child sitemap URLs if index)
    """
    # Try XML parser first (requires lxml), fall back to html.parser
    from bs4 import XMLParsedAsHTMLWarning

    try:
        soup = BeautifulSoup(content, "lxml-xml")
    except Exception:
        try:
            soup = BeautifulSoup(content, "xml")
        except Exception:
            # Suppress the XMLParsedAsHTMLWarning for this fallback
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            soup = BeautifulSoup(content, "html.parser")

    urls: list[str] = []

    # Check if this is a sitemap index
    sitemap_tags = soup.find_all("sitemap")
    if sitemap_tags:
        # Sitemap index - return child sitemap URLs
        for sitemap in sitemap_tags:
            loc = sitemap.find("loc")
            if loc and loc.string:
                child_url = loc.string.strip()
                if child_url:
                    urls.append(child_url)
        return urls

    # Regular sitemap - extract URL entries
    url_tags = soup.find_all("url")
    for url_tag in url_tags:
        loc = url_tag.find("loc")
        if loc and loc.string:
            url_str = loc.string.strip()
            if url_str:
                # Resolve relative URLs if base_url provided
                if base_url and not url_str.startswith(("http://", "https://")):
                    url_str = urljoin(base_url, url_str)

                # Validate URL - must be http or https with a valid host
                parsed = urlparse(url_str)
                if parsed.scheme in ("http", "https") and parsed.netloc:
                    urls.append(url_str)
                # Skip invalid URLs (no scheme or no netloc)

    return urls


def parse_llms_txt(content: str) -> dict[str, Any]:
    """Parse llms.txt content and extract URL entries.

    Handles:
    - Markdown links: [Title](URL): Description
    - Bare URLs: https://example.com/path
    - Optional sections: URLs under ## Optional are flagged

    Args:
        content: llms.txt content (markdown format)

    Returns:
        Dict with "urls" key containing list of URL entries
    """
    urls: list[dict[str, Any]] = []
    in_optional_section = False
    seen_urls: set[str] = set()

    lines = content.split("\n")
    current_section = "Core"

    for line in lines:
        stripped = line.strip()

        # Check for section headers
        if stripped.startswith("## "):
            section_name = stripped[3:].strip()
            if section_name.lower() == "optional":
                in_optional_section = True
                current_section = "Optional"
            else:
                in_optional_section = False
                current_section = section_name
            continue

        # Strip leading list marker (- or *)
        if stripped.startswith("- ") or stripped.startswith("* "):
            stripped = stripped[2:]

        # Match markdown links: [Title](URL): Description or [Title](URL)
        md_link_pattern = r"\[([^\]]+)\]\(([^)]+)\)(?::\s*(.*))?"
        match = re.match(md_link_pattern, stripped)
        if match:
            title = match.group(1).strip()
            url = match.group(2).strip()
            description = match.group(3).strip() if match.group(3) else None

            if url and url not in seen_urls:
                entry: dict[str, Any] = {
                    "url": url,
                    "title": title,
                    "section": current_section,
                }
                if description:
                    entry["description"] = description
                if in_optional_section:
                    entry["optional"] = True
                urls.append(entry)
                seen_urls.add(url)
            continue

        # Match bare URLs
        bare_url_pattern = r'^(https?://[^\s<>"{}|\\^`\[\]]+)'
        match = re.match(bare_url_pattern, stripped)
        if match:
            url = match.group(1).strip()
            if url and url not in seen_urls:
                entry: dict[str, Any] = {
                    "url": url,
                    "section": current_section,
                }
                if in_optional_section:
                    entry["optional"] = True
                urls.append(entry)
                seen_urls.add(url)

    # Determine sources
    sources: list[str] = []
    if urls:
        sources.append("llms_txt")

    return {
        "urls": urls,
        "source": sources,
    }


def _is_sitemap_index(urls: list[str]) -> bool:
    """Check if URL list represents a sitemap index (child sitemap URLs).

    Args:
        urls: List of URLs to check

    Returns:
        True if URLs appear to be child sitemap references
    """
    if not urls:
        return False
    # Check first few URLs - if they all look like sitemap files, it's an index
    sample = urls[:3]
    return all(url.endswith(".xml") or "sitemap" in url.lower() for url in sample)


class SiteScraper(DocumentationScraper):
    """Generic site scraper with discovery and fetch modes.

    Discovery mode: Given a base_url, discovers URLs via llms.txt and/or sitemap.xml
    Fetch mode: Given a list of URLs, fetches each and converts to markdown

    Output structure (fetch mode):
        output_dir/
            README.md      - Metadata and page index
            001-title.md   - Fetched pages as numbered markdown files
            002-title.md
            ...
            .cache/site/   - Cached responses
    """

    name: str = "site"
    description: str = """Scrape generic documentation sites via llms.txt and sitemap.xml discovery.

Supports two modes:
1. Discovery: Find URLs from llms.txt/sitemap.xml
   scrape.py site --base-url https://example.com

2. Fetch: Scrape specific URLs
   scrape.py site https://example.com/docs/page1 https://example.com/docs/page2

Output includes README.md (with page index) and pages/ directory with numbered markdown files.
"""

    def __init__(
        self,
        base_url: str = "",
        output_dir: Path | None = None,
        urls: list[str] | None = None,
        force: bool = False,
        **kwargs: Any,
    ):
        """Initialize SiteScraper.

        Args:
            base_url: Base URL for discovery mode
            output_dir: Output directory for fetched content
            urls: List of URLs to fetch (enables fetch mode)
            force: Force re-fetch, ignoring cache
            **kwargs: Additional arguments passed to base class
        """
        # Determine mode
        self.urls = urls or []

        if self.urls:
            self.mode = "fetch"
            # Derive base_url from first URL if not provided
            if not base_url and self.urls:
                parsed = urlparse(self.urls[0])
                base_url = f"{parsed.scheme}://{parsed.netloc}"
        elif base_url:
            self.mode = "discovery"
        else:
            raise ValueError("Either base_url or urls must be provided")

        # Ensure output_dir has a default
        if output_dir is None:
            output_dir = Path("site-output")

        super().__init__(
            base_url=base_url,
            output_dir=output_dir,
            force=force,
            **kwargs,
        )

    def discover_urls(self) -> dict[str, Any]:
        """Discover URLs from llms.txt and sitemap.xml.

        Returns:
            Dict with "urls" list and "source" list indicating discovery methods
        """
        all_urls: list[dict[str, Any]] = []
        sources: list[str] = []
        seen_urls: set[str] = set()

        # Try llms.txt first
        llms_result = self._discover_from_llms_txt()
        if llms_result["urls"]:
            for entry in llms_result["urls"]:
                url = entry.get("url", "")
                if url and url not in seen_urls:
                    all_urls.append(entry)
                    seen_urls.add(url)
            if "llms_txt" in llms_result.get("source", []):
                sources.append("llms_txt")

        # Then try sitemap.xml for additional URLs
        sitemap_result = self._discover_from_sitemap()
        if sitemap_result["urls"]:
            for entry in sitemap_result["urls"]:
                url = entry.get("url", "")
                if url and url not in seen_urls:
                    all_urls.append(entry)
                    seen_urls.add(url)
            if "sitemap_xml" in sitemap_result.get("source", []):
                sources.append("sitemap_xml")

        # Warning if nothing found
        if not all_urls:
            warnings.warn(
                f"No URLs discovered from llms.txt or sitemap.xml at {self.base_url}",
                UserWarning,
                stacklevel=2,
            )
            print(f"Warning: No URLs discovered from {self.base_url}")

        return {
            "urls": all_urls,
            "source": sources,
        }

    def _discover_from_llms_txt(self) -> dict[str, Any]:
        """Fetch and parse llms.txt from the site."""
        llms_url = urljoin(self.base_url, "/llms.txt")

        try:
            response = self.session.get(llms_url, timeout=self.timeout)
            if response.status_code == 200:
                result = parse_llms_txt(response.text)
                result["source"] = ["llms_txt"]
                return result
        except Exception as e:
            print(f"Warning: Could not fetch llms.txt: {e}")

        return {"urls": [], "source": []}

    def _discover_from_sitemap(self) -> dict[str, Any]:
        """Fetch and parse sitemap.xml from the site."""
        sitemap_url = urljoin(self.base_url, "/sitemap.xml")

        try:
            response = self.session.get(sitemap_url, timeout=self.timeout)
            if response.status_code == 200:
                raw_urls = parse_sitemap_xml(response.text, base_url=self.base_url)

                # Check if it's a sitemap index (returns child sitemap URLs)
                if _is_sitemap_index(raw_urls):
                    # Fetch child sitemaps (with depth limit)
                    all_urls = self._fetch_child_sitemaps(raw_urls, depth=0, max_depth=2)
                else:
                    all_urls = raw_urls

                # Convert to structured entries
                url_entries: list[dict[str, Any]] = []
                for url in all_urls:
                    url_entries.append(
                        {
                            "url": url,
                            "title": self._extract_title_from_url(url),
                        }
                    )

                return {
                    "urls": url_entries,
                    "source": ["sitemap_xml"],
                }
        except Exception as e:
            print(f"Warning: Could not fetch sitemap.xml: {e}")

        return {"urls": [], "source": []}

    def _fetch_child_sitemaps(
        self, sitemap_urls: list[str], depth: int, max_depth: int
    ) -> list[str]:
        """Recursively fetch child sitemaps with depth limit.

        Args:
            sitemap_urls: List of child sitemap URLs
            depth: Current recursion depth
            max_depth: Maximum recursion depth

        Returns:
            List of all discovered URLs from leaf sitemaps
        """
        if depth > max_depth:
            print(f"Warning: Sitemap recursion depth limit ({max_depth}) reached")
            return []

        all_urls: list[str] = []

        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=self.timeout)
                if response.status_code == 200:
                    urls = parse_sitemap_xml(response.text, base_url=self.base_url)

                    # Check if these are more sitemap URLs
                    if _is_sitemap_index(urls):
                        child_urls = self._fetch_child_sitemaps(urls, depth + 1, max_depth)
                        all_urls.extend(child_urls)
                    else:
                        all_urls.extend(urls)
            except Exception as e:
                print(f"Warning: Could not fetch child sitemap {sitemap_url}: {e}")

        return all_urls

    @staticmethod
    def _extract_title_from_url(url: str) -> str:
        """Extract a title from a URL path."""
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")

        if path:
            # Get last segment
            segments = path.split("/")
            last_segment = segments[-1] if segments else ""

            # Remove common extensions
            last_segment = re.sub(r"\.(html?|md)$", "", last_segment, flags=re.IGNORECASE)

            # Clean up and format
            title = last_segment.replace("-", " ").replace("_", " ")
            return title.title() if title else "Untitled"
        else:
            return parsed.netloc

    @staticmethod
    def fetch_github_version(github_url: str) -> str | None:
        """Fetch latest version from GitHub via gh CLI or API fallback.

        Args:
            github_url: GitHub repository URL (e.g., https://github.com/owner/repo)

        Returns:
            Version string (e.g., "v1.2.3") or None if not found
        """
        import subprocess

        # Parse owner/repo from GitHub URL
        parsed = urlparse(github_url)
        if parsed.netloc != "github.com":
            return None

        path = parsed.path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            return None

        owner, repo = parts[0], parts[1]

        # Try gh CLI first
        try:
            result = subprocess.run(
                [
                    "gh",
                    "release",
                    "list",
                    "--repo",
                    f"{owner}/{repo}",
                    "--limit",
                    "1",
                    "--json",
                    "tagName",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json

                data = json.loads(result.stdout)
                if data and len(data) > 0:
                    return data[0].get("tagName")
        except Exception:
            pass

        # Fall back to GitHub API
        import requests

        releases_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        try:
            response = requests.get(releases_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("tag_name")
        except Exception:
            pass

        return None

    def fetch_urls(self) -> None:
        """Fetch all configured URLs and write output."""
        # Deduplicate URLs
        unique_urls: list[str] = []
        seen: set[str] = set()
        for url in self.urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track results for README.md page index
        results: list[dict[str, Any]] = []

        # Fetch each URL
        for idx, url in enumerate(unique_urls, start=1):
            print(f"Fetching [{idx}/{len(unique_urls)}]: {url}")

            try:
                content, fmt = self.fetch_page_llm_friendly(url, cache_file=f"page_{idx}")

                if content is None:
                    print(f"  Warning: Failed to fetch {url}")
                    results.append(
                        {
                            "url": url,
                            "status": "error",
                            "error": "Failed to fetch",
                        }
                    )
                    continue

                # Generate filename
                title = self._extract_title_from_url(url)
                filename = self.sanitize_filename(title, section_num=str(idx).zfill(3))
                output_file = self.output_dir / f"{filename}.md"

                # Write content
                output_file.write_text(content, encoding="utf-8")
                print(f"  Written: {output_file.name}")

                results.append(
                    {
                        "url": url,
                        "status": "success",
                        "title": title,
                        "filename": output_file.name,
                    }
                )

            except PermissionError as e:
                print(f"  Error: {e}")
                results.append(
                    {
                        "url": url,
                        "status": "blocked",
                        "error": str(e),
                    }
                )
            except Exception as e:
                print(f"  Error: {e}")
                results.append(
                    {
                        "url": url,
                        "status": "error",
                        "error": str(e),
                    }
                )

        # Generate README.md (includes page index)
        self._generate_readme(results)

    def _generate_readme(self, results: list[dict[str, Any]]) -> None:
        """Generate README.md with template placeholders for LLM to fill."""
        readme_path = self.output_dir / "README.md"

        now = datetime.now(UTC)
        date_str = now.strftime("%Y-%m-%d")

        # Build page index
        page_lines = []
        for result in results:
            url = result.get("url", "Unknown")
            status = result.get("status", "unknown")

            if status == "success":
                title = result.get("title", "Untitled")
                filename = result.get("filename", "")
                page_lines.append(f"- [{title}]({filename}) — {url}")
            else:
                error = result.get("error", "Unknown error")
                page_lines.append(f"- {url} — **{status}**: {error}")

        lines = [
            "# {PROJECT_NAME}",
            "",
            "{BRIEF_INTRODUCTION}",
            "",
            "## Metadata",
            "",
            "- **Version:** {VERSION}",
            "- **GitHub:** {GITHUB_URL}",
            f"- **Scraped:** {date_str}",
            f"- **Source:** {self.base_url}",
            "",
            "## Tech Stack",
            "",
            "{TECH_STACK}",
            "",
            "## Pages",
            "",
        ]
        lines.extend(page_lines)
        lines.extend(
            [
                "",
                "---",
                f"*Generated by scraper skill on {date_str}*",
                "*Author: Rianico, Email: zhxuankun@163.com*",
            ]
        )

        readme_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Generated: {readme_path}")

    def run(self) -> None:
        """Execute the scraping workflow based on mode."""
        if self.mode == "discovery":
            result = self.discover_urls()
            print(json.dumps(result, indent=2))
        else:
            self.fetch_urls()
