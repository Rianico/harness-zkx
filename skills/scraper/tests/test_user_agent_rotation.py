"""Tests for User-Agent rotation.

Test IDs: UA-01 through UA-05
"""

from unittest.mock import MagicMock, patch

import pytest

from fixtures import TEST_PAGE_URL, USER_AGENT_POOL


class TestUserAgentRotation:
    """Test suite for User-Agent rotation."""

    def test_ua_01_pool_contains_valid_count(self, temp_output_dir, temp_cache_dir):
        """UA-01: Pool contains 5-10 UAs.

        Initialize scraper should have user_agent_pool with 5-10 entries.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            user_agent_pool=USER_AGENT_POOL,
        )

        # Should have access to user agent pool
        assert hasattr(scraper, "user_agent_pool")
        assert 5 <= len(scraper.user_agent_pool) <= 10

    def test_ua_02_rotation_on_each_request(self, temp_output_dir, temp_cache_dir):
        """UA-02: Rotation on each request.

        Multiple fetch_page() calls should use different UA per request.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            user_agent_pool=USER_AGENT_POOL,
        )

        mock_session = MagicMock()
        captured_headers = []

        def mock_get(url, *args, **kwargs):
            captured_headers.append(dict(mock_session.headers))
            response = MagicMock(
                status_code=200,
                text="<html>Success</html>",
                content=b"<html>Success</html>",
                headers={},
            )
            response.raise_for_status = lambda: None
            return response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        with patch("time.sleep"):
            for i in range(3):
                scraper.fetch_page(TEST_PAGE_URL, cache_file=f"test{i}.html")

        # Should have rotated User-Agent
        user_agents = [h.get("User-Agent") for h in captured_headers if h.get("User-Agent")]
        # At least 2 different user agents should have been used
        assert len(set(user_agents)) >= 2

    def test_ua_03_accept_headers_present(self, temp_output_dir, temp_cache_dir):
        """UA-03: Accept headers present.

        Inspect session headers should have Accept, Accept-Language, Accept-Encoding.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            user_agent_pool=USER_AGENT_POOL,
        )

        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None
        mock_session.headers = {}
        scraper.session = mock_session

        scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Session headers should include Accept-related headers
        headers = dict(mock_session.headers)
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers

    def test_ua_04_valid_accept_header_format(self, temp_output_dir, temp_cache_dir):
        """UA-04: Valid Accept header format.

        Header should be 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            user_agent_pool=USER_AGENT_POOL,
        )

        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None
        mock_session.headers = {}
        scraper.session = mock_session

        scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        headers = dict(mock_session.headers)
        accept_header = headers.get("Accept", "")
        # Should contain text/html and proper format
        assert "text/html" in accept_header
        assert "application/xhtml+xml" in accept_header

    def test_ua_05_fallback_to_default_ua(self, temp_output_dir, temp_cache_dir):
        """UA-05: Fallback to default UA.

        Empty or invalid pool should fall back to existing static UA.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        # Create scraper with empty pool
        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            user_agent_pool=[],  # Empty pool
        )

        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should succeed with fallback UA
        assert result is not None
        # Should have some User-Agent set
        headers = dict(mock_session.headers)
        assert "User-Agent" in headers
