"""Tests for rate limiting functionality.

Test IDs: RL-01 through RL-04
"""

from typing import override
from unittest.mock import MagicMock

from fixtures import TEST_PAGE_URL


class TestRateLimiting:
    """Test suite for rate limiting behavior."""

    def test_rl_01_default_delay_between_requests(self, scraper_with_mock_session, fake_clock):
        """RL-01: Default delay between requests.

        Two consecutive fetch_page() calls should have second call
        delayed by ~1s from first.
        """
        scraper = scraper_with_mock_session
        mock_session = scraper.session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Test</html>",
            content=b"<html>Test</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None

        # First call should NOT sleep (no previous request)
        scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")

        # Second call SHOULD sleep for default delay (1.0s)
        scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        # Verify sleep was called once (for second request) with exactly 1.0s
        assert fake_clock.sleep_calls == [1.0]
        assert fake_clock.sleep_calls[0] == 1.0

    def test_rl_02_custom_delay_configuration(self, temp_output_dir, temp_cache_dir, fake_clock):
        """RL-02: Custom delay configuration.

        delay=2.5 in constructor should result in delay of 2.5s between requests.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            @override
            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            delay=2.5,  # Custom delay
        )

        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Test</html>",
            content=b"<html>Test</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None
        scraper.session = mock_session

        _ = scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
        _ = scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        assert fake_clock.sleep_calls == [2.5]
        assert fake_clock.sleep_calls[0] == 2.5

    def test_rl_03_zero_delay_allowed(self, temp_output_dir, temp_cache_dir, fake_clock):
        """RL-03: Zero delay allowed.

        delay=0 should result in no delay between requests.
        """
        from base import DocumentationScraper

        class ConcreteScraper(DocumentationScraper):
            name = "test"
            description = "Test scraper"

            @override
            def run(self):
                pass

        scraper = ConcreteScraper(
            base_url="https://example.com",
            output_dir=temp_output_dir,
            cache_base=temp_cache_dir,
            delay=0,  # No delay
        )

        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Test</html>",
            content=b"<html>Test</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None
        scraper.session = mock_session

        _ = scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
        _ = scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        # With delay=0, sleep should not be called
        assert fake_clock.sleep_calls == []

    def test_rl_04_delay_precision(self, scraper_with_mock_session, fake_clock):
        """RL-04: Delay precision.

        Measured actual wait time should be within +/-10% of configured delay.
        """
        scraper = scraper_with_mock_session
        mock_session = scraper.session
        mock_session.get.return_value = MagicMock(
            status_code=200,
            text="<html>Test</html>",
            content=b"<html>Test</html>",
            headers={},
        )
        mock_session.get.return_value.raise_for_status = lambda: None

        # Default delay is 1.0 seconds
        scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
        scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        assert fake_clock.sleep_calls == [1.0]
        assert fake_clock.sleep_calls[0] == 1.0
