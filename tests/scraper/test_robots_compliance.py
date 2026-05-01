"""Tests for robots.txt compliance.

Test IDs: RT-01 through RT-07
"""

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from fixtures import (
    TEST_PAGE_URL,
    TEST_BASE_URL,
    ALLOW_ALL_ROBOTS,
    BLOCK_ALL_ROBOTS,
    CRAWL_DELAY_ROBOTS,
    SPECIFIC_UA_ROBOTS,
)


class TestRobotsCompliance:
    """Test suite for robots.txt compliance."""

    def test_rt_01_allowed_by_robots_txt(self, temp_output_dir, temp_cache_dir):
        """RT-01: Allowed by robots.txt.

        URL permitted in robots.txt should fetch normally.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # Mock robots.txt response (allow all)
        robots_response = MagicMock(
            status_code=200,
            text=ALLOW_ALL_ROBOTS,
            content=ALLOW_ALL_ROBOTS.encode(),
            headers={},
        )
        robots_response.raise_for_status = lambda: None

        # Mock page response
        page_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        page_response.raise_for_status = lambda: None

        def mock_get(url, *args, **kwargs):
            if "robots.txt" in url:
                return robots_response
            return page_response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should succeed since robots.txt allows
        assert result is not None

    def test_rt_02_disallowed_by_robots_txt(self, temp_output_dir, temp_cache_dir):
        """RT-02: Disallowed by robots.txt.

        URL blocked in robots.txt should raise PermissionError before fetching.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # Mock robots.txt response (block all)
        robots_response = MagicMock(
            status_code=200,
            text=BLOCK_ALL_ROBOTS,
            content=BLOCK_ALL_ROBOTS.encode(),
            headers={},
        )
        robots_response.raise_for_status = lambda: None

        mock_session.get = MagicMock(return_value=robots_response)
        mock_session.headers = {}
        scraper.session = mock_session

        # Should raise PermissionError for disallowed URL
        with pytest.raises(PermissionError):
            scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

    def test_rt_03_missing_robots_txt(self, temp_output_dir, temp_cache_dir):
        """RT-03: Missing robots.txt.

        404 on robots.txt fetch should proceed with warning (conservative: allow).
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # Mock robots.txt 404
        robots_response = MagicMock(
            status_code=404,
            text="Not Found",
            content=b"Not Found",
            headers={},
        )
        robots_response.raise_for_status = lambda: (
            _ for _ in ()
        ).throw(requests.exceptions.HTTPError("404 Not Found", response=robots_response))

        # Mock page response (should succeed since no robots.txt)
        page_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        page_response.raise_for_status = lambda: None

        def mock_get(url, *args, **kwargs):
            if "robots.txt" in url:
                return robots_response
            return page_response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should succeed even without robots.txt (fail-open)
        assert result is not None

    def test_rt_04_robots_txt_fetch_failure(self, temp_output_dir, temp_cache_dir):
        """RT-04: robots.txt fetch failure.

        Network error on robots.txt should proceed with warning (conservative: allow).
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # Mock page response (should succeed despite robots.txt failure)
        page_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        page_response.raise_for_status = lambda: None

        def mock_get(url, *args, **kwargs):
            if "robots.txt" in url:
                raise requests.exceptions.ConnectionError("Network error")
            return page_response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should succeed even with robots.txt network failure (fail-open)
        assert result is not None

    def test_rt_05_crawl_delay_directive(self, temp_output_dir, temp_cache_dir):
        """RT-05: Crawl-delay directive.

        'Crawl-delay: 2' in robots.txt should use max(request_delay, crawl_delay).
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
            delay=1.0,  # Default delay
        )

        mock_session = MagicMock()

        # Mock robots.txt with Crawl-delay: 2
        robots_response = MagicMock(
            status_code=200,
            text=CRAWL_DELAY_ROBOTS,
            content=CRAWL_DELAY_ROBOTS.encode(),
            headers={},
        )
        robots_response.raise_for_status = lambda: None

        # Mock page response
        page_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        page_response.raise_for_status = lambda: None

        def mock_get(url, *args, **kwargs):
            if "robots.txt" in url:
                return robots_response
            return page_response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            scraper.fetch_page(TEST_PAGE_URL, cache_file="test1.html")
            scraper.fetch_page(TEST_PAGE_URL, cache_file="test2.html")

        # Crawl-delay of 2s should override default 1s delay
        assert len(sleep_times) == 1
        assert 1.8 <= sleep_times[0] <= 2.2

    def test_rt_06_user_agent_specific_rules(self, temp_output_dir, temp_cache_dir):
        """RT-06: User-agent specific rules.

        robots.txt has rules for scraper UA should apply matching rules.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "base"  # Match the user-agent in SPECIFIC_UA_ROBOTS
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # Mock robots.txt with specific UA rules
        robots_response = MagicMock(
            status_code=200,
            text=SPECIFIC_UA_ROBOTS,
            content=SPECIFIC_UA_ROBOTS.encode(),
            headers={},
        )
        robots_response.raise_for_status = lambda: None

        # Mock page response
        page_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        page_response.raise_for_status = lambda: None

        def mock_get(url, *args, **kwargs):
            if "robots.txt" in url:
                return robots_response
            return page_response

        mock_session.get = mock_get
        # Set User-Agent header to match the scraper name
        mock_session.headers = {"User-Agent": "base"}
        scraper.session = mock_session

        # URL blocked for 'base' user-agent
        blocked_url = f"{TEST_BASE_URL}/blocked-for-base/page.html"
        with pytest.raises(PermissionError):
            scraper.fetch_page(blocked_url, cache_file="test.html")

    def test_rt_07_wildcard_user_agent(self, temp_output_dir, temp_cache_dir):
        """RT-07: Wildcard user-agent.

        'User-agent: *' rule blocks if no specific UA match.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"  # Does not match 'other' in SPECIFIC_UA_ROBOTS
            description = "Test scraper"

            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url=TEST_BASE_URL,
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            respect_robots_txt=True,
        )

        mock_session = MagicMock()

        # BLOCK_ALL_ROBOTS uses User-agent: * Disallow: /
        robots_response = MagicMock(
            status_code=200,
            text=BLOCK_ALL_ROBOTS,
            content=BLOCK_ALL_ROBOTS.encode(),
            headers={},
        )
        robots_response.raise_for_status = lambda: None

        mock_session.get = MagicMock(return_value=robots_response)
        mock_session.headers = {}
        scraper.session = mock_session

        # Should be blocked by wildcard rule
        with pytest.raises(PermissionError):
            scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")
