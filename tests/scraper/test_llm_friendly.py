"""Tests for LLM-friendly fetching methods."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fixtures import TEST_BASE_URL, TEST_PAGE_URL


class TestCheckLlmsTxt:
    """Tests for check_llms_txt method."""

    def test_returns_url_when_llms_txt_exists(self, scraper_with_mock_session) -> None:
        """Should return llms.txt URL when it exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        scraper_with_mock_session.session.head = MagicMock(return_value=mock_response)

        result = scraper_with_mock_session.check_llms_txt()

        assert result == f"{TEST_BASE_URL}/llms.txt"
        scraper_with_mock_session.session.head.assert_called_once()

    def test_returns_none_when_llms_txt_missing(self, scraper_with_mock_session) -> None:
        """Should return None when llms.txt doesn't exist."""
        import requests

        scraper_with_mock_session.session.head = MagicMock(
            side_effect=requests.exceptions.RequestException()
        )

        result = scraper_with_mock_session.check_llms_txt()

        assert result is None

    def test_uses_custom_base_url(self, scraper_with_mock_session) -> None:
        """Should use provided base_url instead of instance base_url."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        scraper_with_mock_session.session.head = MagicMock(return_value=mock_response)

        result = scraper_with_mock_session.check_llms_txt("https://other.com")

        assert result == "https://other.com/llms.txt"


class TestFetchMarkdownViaNegotiation:
    """Tests for fetch_markdown_via_negotiation method."""

    def test_returns_markdown_when_server_supports(self, scraper_with_mock_session) -> None:
        """Should return markdown when server returns text/markdown."""
        mock_response = MagicMock()
        mock_response.text = "# Title\n\nContent"
        mock_response.headers = {
            "content-type": "text/markdown; charset=utf-8",
            "x-markdown-tokens": "100",
        }

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            content, fmt = scraper_with_mock_session.fetch_markdown_via_negotiation(
                TEST_PAGE_URL
            )

            assert content == "# Title\n\nContent"
            assert fmt == "markdown"

    def test_returns_html_when_server_returns_html(self, scraper_with_mock_session) -> None:
        """Should return HTML format when server returns HTML."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Content</body></html>"
        mock_response.headers = {"content-type": "text/html"}

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            content, fmt = scraper_with_mock_session.fetch_markdown_via_negotiation(
                TEST_PAGE_URL
            )

            assert content == "<html><body>Content</body></html>"
            assert fmt == "html"

    def test_returns_none_on_failure(self, scraper_with_mock_session) -> None:
        """Should return (None, 'html') when request fails."""
        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = None

            content, fmt = scraper_with_mock_session.fetch_markdown_via_negotiation(
                TEST_PAGE_URL
            )

            assert content is None
            assert fmt == "html"

    def test_restores_original_accept_header(self, scraper_with_mock_session) -> None:
        """Should restore original Accept header after request."""
        scraper_with_mock_session.session.headers["Accept"] = "text/html"

        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.headers = {"content-type": "text/html"}

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            scraper_with_mock_session.fetch_markdown_via_negotiation(TEST_PAGE_URL)

            assert scraper_with_mock_session.session.headers["Accept"] == "text/html"


class TestFetchMarkdownExtension:
    """Tests for fetch_markdown_extension method."""

    def test_returns_markdown_for_md_url(self, scraper_with_mock_session) -> None:
        """Should return markdown when .md URL exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Markdown Content"
        mock_response.headers = {"content-type": "text/markdown"}

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            content, fmt = scraper_with_mock_session.fetch_markdown_extension(
                f"{TEST_BASE_URL}/page.html"
            )

            assert content == "# Markdown Content"
            assert fmt == "markdown"
            mock_get.assert_called_once_with(f"{TEST_BASE_URL}/page.html.md")

    def test_appends_index_md_for_trailing_slash(self, scraper_with_mock_session) -> None:
        """Should append index.md for URLs ending with slash."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Index"
        mock_response.headers = {"content-type": "text/plain"}

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            content, fmt = scraper_with_mock_session.fetch_markdown_extension(
                f"{TEST_BASE_URL}/docs/"
            )

            assert content == "# Index"
            assert fmt == "markdown"
            mock_get.assert_called_once_with(f"{TEST_BASE_URL}/docs/index.md")

    def test_returns_none_html_when_md_not_found(self, scraper_with_mock_session) -> None:
        """Should return (None, 'html') when .md URL doesn't exist."""
        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = None

            content, fmt = scraper_with_mock_session.fetch_markdown_extension(
                f"{TEST_BASE_URL}/page"
            )

            assert content is None
            assert fmt == "html"

    def test_returns_none_for_wrong_content_type(self, scraper_with_mock_session) -> None:
        """Should return None when content type is not markdown/text."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>...</html>"
        mock_response.headers = {"content-type": "text/html"}

        with patch.object(scraper_with_mock_session, "_rate_limited_get") as mock_get:
            mock_get.return_value = mock_response

            content, fmt = scraper_with_mock_session.fetch_markdown_extension(
                f"{TEST_BASE_URL}/page"
            )

            assert content is None
            assert fmt == "html"


class TestFetchPageLlmFriendly:
    """Tests for fetch_page_llm_friendly method."""

    def test_prefers_markdown_from_cache(self, temp_cache_dir, temp_output_dir) -> None:
        """Should return cached markdown if available."""
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        cache_dir = temp_cache_dir / "test"
        cache_dir.mkdir(parents=True)
        (cache_dir / "page.md").write_text("# Cached Content", encoding="utf-8")

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=False,
        )

        content, fmt = scraper.fetch_page_llm_friendly(
            f"{TEST_BASE_URL}/page", cache_file="page"
        )

        assert content == "# Cached Content"
        assert fmt == "markdown"

    def test_tries_negotiation_then_extension(self, scraper_with_mock_session) -> None:
        """Should try negotiation first, then extension."""
        # Negotiation returns HTML, extension returns markdown
        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=("<html>...</html>", "html"),
        ):
            with patch.object(
                scraper_with_mock_session,
                "fetch_markdown_extension",
                return_value=("# Real Markdown", "markdown"),
            ):
                content, fmt = scraper_with_mock_session.fetch_page_llm_friendly(
                    TEST_PAGE_URL
                )

                assert content == "# Real Markdown"
                assert fmt == "markdown"

    def test_falls_back_to_html_conversion(self, scraper_with_mock_session) -> None:
        """Should fall back to HTML conversion when markdown not available."""
        from bs4 import BeautifulSoup

        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=(None, "html"),
        ):
            with patch.object(
                scraper_with_mock_session,
                "fetch_markdown_extension",
                return_value=(None, "html"),
            ):
                with patch.object(
                    scraper_with_mock_session,
                    "fetch_via_jina_reader",
                    return_value=(None, "html"),
                ):
                    with patch.object(
                        scraper_with_mock_session,
                        "fetch_page",
                        return_value=BeautifulSoup(
                            "<html><body><h1>Title</h1></body></html>", "html.parser"
                        ),
                    ):
                        content, fmt = scraper_with_mock_session.fetch_page_llm_friendly(
                            TEST_PAGE_URL
                        )

                        assert content is not None
                        assert fmt == "html"

    def test_returns_none_on_all_failures(self, scraper_with_mock_session) -> None:
        """Should return (None, 'html') when all methods fail."""
        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=(None, "html"),
        ):
            with patch.object(
                scraper_with_mock_session,
                "fetch_markdown_extension",
                return_value=(None, "html"),
            ):
                with patch.object(
                    scraper_with_mock_session,
                    "fetch_via_jina_reader",
                    return_value=(None, "html"),
                ):
                    with patch.object(
                        scraper_with_mock_session, "fetch_page", return_value=None
                    ):
                        content, fmt = scraper_with_mock_session.fetch_page_llm_friendly(
                            TEST_PAGE_URL
                        )

                        assert content is None
                        assert fmt == "html"

    def test_caches_markdown_response(self, scraper_with_mock_session) -> None:
        """Should cache markdown response to .md file."""
        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=("# New Content", "markdown"),
        ):
            scraper_with_mock_session.fetch_page_llm_friendly(TEST_PAGE_URL)

            cache_file = scraper_with_mock_session.cache_dir / "page.md"
            assert cache_file.exists()
            assert cache_file.read_text() == "# New Content"

    def test_uses_jina_reader_as_fallback(self, scraper_with_mock_session) -> None:
        """Should use Jina Reader when negotiation and extension fail."""
        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=(None, "html"),
        ):
            with patch.object(
                scraper_with_mock_session,
                "fetch_markdown_extension",
                return_value=(None, "html"),
            ):
                with patch.object(
                    scraper_with_mock_session,
                    "fetch_via_jina_reader",
                    return_value=("# Jina Content", "markdown"),
                ):
                    content, fmt = scraper_with_mock_session.fetch_page_llm_friendly(
                        TEST_PAGE_URL, use_jina=True
                    )

                    assert content == "# Jina Content"
                    assert fmt == "markdown"

    def test_skips_jina_when_disabled(self, scraper_with_mock_session) -> None:
        """Should skip Jina Reader when use_jina=False."""
        from bs4 import BeautifulSoup

        with patch.object(
            scraper_with_mock_session,
            "fetch_markdown_via_negotiation",
            return_value=(None, "html"),
        ):
            with patch.object(
                scraper_with_mock_session,
                "fetch_markdown_extension",
                return_value=(None, "html"),
            ):
                with patch.object(
                    scraper_with_mock_session,
                    "fetch_via_jina_reader",
                ) as mock_jina:
                    with patch.object(
                        scraper_with_mock_session,
                        "fetch_page",
                        return_value=BeautifulSoup(
                            "<html><body><h1>Title</h1></body></html>", "html.parser"
                        ),
                    ):
                        scraper_with_mock_session.fetch_page_llm_friendly(
                            TEST_PAGE_URL, use_jina=False
                        )

                        # Jina Reader should not be called
                        mock_jina.assert_not_called()


class TestFetchViaJinaReader:
    """Tests for fetch_via_jina_reader method."""

    def test_returns_markdown_on_success(self, scraper_with_mock_session) -> None:
        """Should return markdown from Jina Reader."""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "# Title\n\nContent from Jina"

        with patch("requests.get", return_value=mock_response):
            content, fmt = scraper_with_mock_session.fetch_via_jina_reader(
                TEST_PAGE_URL
            )

            assert content == "# Title\n\nContent from Jina"
            assert fmt == "markdown"

    def test_returns_none_on_failure(self, scraper_with_mock_session) -> None:
        """Should return (None, 'html') on failure."""
        import requests

        with patch("requests.get", side_effect=requests.exceptions.RequestException()):
            content, fmt = scraper_with_mock_session.fetch_via_jina_reader(
                TEST_PAGE_URL
            )

            assert content is None
            assert fmt == "html"

    def test_constructs_correct_jina_url(self, scraper_with_mock_session) -> None:
        """Should construct correct r.jina.ai URL."""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "content"

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response

            scraper_with_mock_session.fetch_via_jina_reader("https://example.com/page")

            mock_get.assert_called_once_with(
                "https://r.jina.ai/https://example.com/page",
                timeout=scraper_with_mock_session.timeout,
            )
