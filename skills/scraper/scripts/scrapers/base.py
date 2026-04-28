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
import time
from abc import ABC, abstractmethod
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import html2text
import requests
from bs4 import BeautifulSoup, Tag


# Default User-Agent pool for rotation
DEFAULT_USER_AGENT_POOL: list[dict[str, str]] = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
    },
]

# Retryable HTTP status codes
RETRYABLE_STATUS_CODES: set[int] = {408, 429, 500, 502, 503, 504}

# Maximum Retry-After delay in seconds
MAX_RETRY_AFTER: float = 60.0

# Default headers when no user-agent pool is provided
_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
}


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
        *,
        delay: float = 1.0,
        max_retries: int = 3,
        user_agent_pool: list[dict[str, str]] | None = None,
        respect_robots_txt: bool = True,
        timeout: float = 30.0,
    ):
        self.base_url = base_url
        self.output_dir = output_dir
        self.force = force
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self.respect_robots_txt = respect_robots_txt

        # Unified cache directory: .cache/<scraper-name>/
        self.cache_base = cache_base or (output_dir.parent / ".cache")
        self.cache_dir = self.cache_base / self.name

        # User-Agent rotation
        self.user_agent_pool = user_agent_pool if user_agent_pool else []
        self._ua_index = 0

        # Rate limiting state
        self._last_request_time: float = 0.0

        # Robots.txt state
        self._robots_parser: RobotFileParser | None = None
        self._robots_fetched: bool = False
        self._crawl_delay: float | None = None

        # HTTP session with headers
        self.session = requests.Session()
        self._set_default_headers()

        # html2text configuration
        self.h2t = html2text.HTML2Text()
        self.h2t.body_width = 0
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.skip_internal_links = False
        self.h2t.unicode_snob = True
        self.h2t.decode_errors = "ignore"

    def _set_default_headers(self) -> None:
        """Set default headers for the session."""
        headers = self.user_agent_pool[0] if self.user_agent_pool else _DEFAULT_HEADERS
        self.session.headers.update(headers)

    def _get_next_user_agent(self) -> dict[str, str]:
        """Get next User-Agent from rotation pool."""
        if not self.user_agent_pool:
            return _DEFAULT_HEADERS.copy()
        headers = self.user_agent_pool[self._ua_index]
        self._ua_index = (self._ua_index + 1) % len(self.user_agent_pool)
        return headers

    def _rotate_user_agent(self) -> None:
        """Rotate to the next User-Agent in the pool."""
        headers = self._get_next_user_agent()
        self.session.headers.update(headers)

    def _wait_for_rate_limit(self) -> None:
        """Apply rate limiting delay between requests."""
        if self.delay <= 0:
            return

        # Determine effective delay (considering crawl-delay from robots.txt)
        effective_delay = self.delay
        if self._crawl_delay is not None:
            effective_delay = max(self.delay, self._crawl_delay)

        elapsed = time.time() - self._last_request_time
        if elapsed < effective_delay:
            wait_time = effective_delay - elapsed
            time.sleep(wait_time)

    def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt.

        Returns True if allowed, raises PermissionError if disallowed.
        """
        if not self.respect_robots_txt:
            return True

        # Initialize robots.txt parser if not already done
        if not self._robots_fetched:
            self._fetch_robots_txt()

        if self._robots_parser is None:
            # No robots.txt available, allow by default (fail-open)
            return True

        # Check if URL is allowed
        if not self._robots_parser.can_fetch(self.session.headers.get("User-Agent", "*"), url):
            raise PermissionError(f"URL blocked by robots.txt: {url}")

        return True

    def _fetch_robots_txt(self) -> None:
        """Fetch and parse robots.txt."""
        self._robots_fetched = True

        robots_url = urljoin(self.base_url, "/robots.txt")

        try:
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 404:
                # No robots.txt, allow all (fail-open)
                return

            response.raise_for_status()

            # Parse robots.txt
            self._robots_parser = RobotFileParser()
            self._robots_parser.set_url(robots_url)
            self._robots_parser.parse(response.text.splitlines())

            # Extract crawl-delay if specified
            # Note: RobotFileParser doesn't expose crawl-delay directly,
            # so we parse it manually
            for line in response.text.splitlines():
                line = line.strip().lower()
                if line.startswith("crawl-delay:"):
                    try:
                        delay_str = line.split(":", 1)[1].strip()
                        self._crawl_delay = float(delay_str)
                    except (ValueError, IndexError):
                        pass
                    break

        except requests.exceptions.RequestException as e:
            # Network error fetching robots.txt - allow all (fail-open)
            print(f"Warning: Failed to fetch robots.txt: {e}")
        except Exception as e:
            # Any other error - allow all (fail-open)
            print(f"Warning: Error parsing robots.txt: {e}")

    def _is_retryable_error(self, status_code: int) -> bool:
        """Check if HTTP status code should trigger retry."""
        return status_code in RETRYABLE_STATUS_CODES

    def _get_retry_delay(self, exception: Exception, attempt: int) -> float:
        """Calculate delay before next retry.

        Considers exponential backoff and Retry-After header.
        """
        # Check for Retry-After header
        if isinstance(exception, requests.exceptions.HTTPError):
            response = exception.response
            if response is not None:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        # Try parsing as integer seconds
                        delay = float(retry_after)
                        return min(delay, MAX_RETRY_AFTER)
                    except ValueError:
                        # Try parsing as HTTP date
                        try:
                            dt = parsedate_to_datetime(retry_after)
                            delay = (dt.timestamp() - time.time())
                            if delay > 0:
                                return min(delay, MAX_RETRY_AFTER)
                        except (ValueError, TypeError):
                            pass

        # Exponential backoff: 1s, 2s, 4s, ...
        # attempt is 0-indexed, so first retry (attempt=0) gets 1s
        base_delay = 1.0 * (2 ** attempt)
        return min(base_delay, MAX_RETRY_AFTER)

    def _rate_limited_get(self, url: str, **kwargs: Any) -> requests.Response | None:
        """Make GET request with rate limiting and retry logic.

        Returns Response object or None on non-retryable error.
        """
        # Apply rate limiting
        self._wait_for_rate_limit()

        # Check robots.txt
        self._check_robots_txt(url)

        # Rotate User-Agent
        self._rotate_user_agent()

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                self._last_request_time = time.time()
                return response

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < self.max_retries:
                    delay = self._get_retry_delay(e, attempt)
                    time.sleep(delay)
                    continue
                return None

            except requests.exceptions.HTTPError as e:
                response = e.response
                if response is None:
                    return None

                status_code = response.status_code

                # Non-retryable 4xx errors
                if status_code in (400, 401, 403, 404):
                    return None

                # Retryable errors
                if self._is_retryable_error(status_code) and attempt < self.max_retries:
                    delay = self._get_retry_delay(e, attempt)
                    time.sleep(delay)
                    continue

                return None

            except Exception:
                # Generic exception - don't retry
                return None

        return None

    def check_llms_txt(self, base_url: str | None = None) -> str | None:
        """Check if site has an llms.txt file.

        Args:
            base_url: Base URL to check (defaults to self.base_url)

        Returns:
            URL of llms.txt if found, None otherwise
        """
        check_url = base_url or self.base_url
        llms_url = urljoin(check_url, "/llms.txt")

        try:
            response = self.session.head(llms_url, timeout=self.timeout)
            if response.status_code == 200:
                return llms_url
        except requests.exceptions.RequestException:
            pass

        return None

    def fetch_markdown_via_negotiation(self, url: str) -> tuple[str | None, str]:
        """Fetch markdown via Accept: text/markdown header.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (content, format) where format is "markdown" or "html"
        """
        # Save current Accept header
        original_accept = self.session.headers.get("Accept", "")

        try:
            # Set Accept header to prefer markdown
            self.session.headers["Accept"] = "text/markdown, text/html"

            response = self._rate_limited_get(url)
            if response is None:
                return None, "html"

            content_type = response.headers.get("content-type", "")
            if "text/markdown" in content_type:
                # Server returned markdown directly
                token_count = response.headers.get("x-markdown-tokens", "unknown")
                print(f"   Received markdown directly ({token_count} tokens)")
                return response.text, "markdown"

            # Server returned HTML
            return response.text, "html"

        finally:
            # Restore original Accept header
            if original_accept:
                self.session.headers["Accept"] = original_accept
            else:
                self.session.headers.pop("Accept", None)

    def fetch_markdown_extension(self, url: str) -> tuple[str | None, str]:
        """Try fetching markdown at .md extension.

        Args:
            url: Original URL

        Returns:
            Tuple of (content, format) where format is "markdown" or "html"
        """
        # Build .md URL
        if url.endswith("/"):
            md_url = url + "index.md"
        else:
            md_url = url + ".md"

        try:
            response = self._rate_limited_get(md_url)
            if response is not None and response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if "markdown" in content_type or "text/plain" in content_type:
                    print(f"   Found markdown at .md extension")
                    return response.text, "markdown"
        except requests.exceptions.RequestException:
            pass

        return None, "html"

    def fetch_via_jina_reader(self, url: str) -> tuple[str | None, str]:
        """Fetch markdown via Jina Reader proxy (r.jina.ai).

        Free service that converts any URL to clean markdown.
        No API key required for basic usage.

        Args:
            url: Original URL to fetch

        Returns:
            Tuple of (content, format) where format is "markdown" or "html"
        """
        jina_url = f"https://r.jina.ai/{url}"

        try:
            # Use direct request to Jina (not rate-limited against target site)
            response = requests.get(jina_url, timeout=self.timeout)
            if response.status_code == 200:
                print(f"   Fetched via Jina Reader proxy")
                return response.text, "markdown"
        except requests.exceptions.RequestException:
            pass

        return None, "html"

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
            print(f"Using cached response: {cache_path.relative_to(self.cache_base.parent)}")
            print(f"   (Use --force to re-fetch, or delete .cache/ directory)")
            try:
                content = cache_path.read_text(encoding="utf-8")
                self._last_request_time = time.time()
                return BeautifulSoup(content, "html.parser")
            except Exception as e:
                print(f"Warning: Failed to read cache: {e}")
                print("Falling back to network request...")

        # Force mode: clear cache
        if self.force and self.cache_dir.exists():
            print(f"Clearing cache: {self.cache_dir}")
            shutil.rmtree(self.cache_dir)

        # Fetch from network with retry logic
        try:
            print(f"Fetching: {url}")
            response = self._rate_limited_get(url)

            if response is None:
                return None

            # Save to cache
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(response.text, encoding="utf-8")
            print(f"   Cached to: {cache_path.relative_to(self.cache_base.parent)}")

            return BeautifulSoup(response.content, "html.parser")

        except PermissionError:
            # robots.txt blocked - re-raise to caller
            raise
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def fetch_page_llm_friendly(
        self, url: str, cache_file: str = "page", use_jina: bool = True
    ) -> tuple[str | None, str]:
        """Fetch page content using LLM-friendly methods first.

        Tries in order:
        1. Accept: text/markdown header (content negotiation)
        2. .md extension on URL
        3. Jina Reader proxy (r.jina.ai) if use_jina=True
        4. Falls back to HTML conversion

        Args:
            url: URL to fetch
            cache_file: Base filename for cache storage (without extension)
            use_jina: Whether to use Jina Reader proxy as fallback (default: True)

        Returns:
            Tuple of (content, format) where format is "markdown" or "html"
        """
        cache_path_md = self.cache_dir / f"{cache_file}.md"
        cache_path_html = self.cache_dir / f"{cache_file}.html"

        # Check cache first
        if cache_path_md.exists() and not self.force:
            print(f"Using cached markdown: {cache_path_md.relative_to(self.cache_base.parent)}")
            return cache_path_md.read_text(encoding="utf-8"), "markdown"

        if cache_path_html.exists() and not self.force:
            print(f"Using cached HTML: {cache_path_html.relative_to(self.cache_base.parent)}")
            content = cache_path_html.read_text(encoding="utf-8")
            # Convert cached HTML to markdown
            soup = BeautifulSoup(content, "html.parser")
            markdown = self.convert_to_markdown(soup, url)
            return markdown, "html"

        # Force mode: clear cache
        if self.force and self.cache_dir.exists():
            print(f"Clearing cache: {self.cache_dir}")
            shutil.rmtree(self.cache_dir)

        print(f"Fetching (LLM-friendly): {url}")

        # Try markdown via content negotiation
        content, fmt = self.fetch_markdown_via_negotiation(url)
        if content and fmt == "markdown":
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path_md.write_text(content, encoding="utf-8")
            return content, "markdown"

        # Try .md extension
        content, fmt = self.fetch_markdown_extension(url)
        if content and fmt == "markdown":
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path_md.write_text(content, encoding="utf-8")
            return content, "markdown"

        # Try Jina Reader proxy
        if use_jina:
            content, fmt = self.fetch_via_jina_reader(url)
            if content and fmt == "markdown":
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                cache_path_md.write_text(content, encoding="utf-8")
                return content, "markdown"

        # Fall back to HTML
        soup = self.fetch_page(url, cache_file=f"{cache_file}.html")
        if soup is None:
            return None, "html"

        markdown = self.convert_to_markdown(soup, url)
        return markdown, "html"

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
