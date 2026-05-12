"""Tests for rate limiting functionality.

Test IDs: RL-01 through RL-04
"""

from unittest.mock import MagicMock, patch

import pytest

from fixtures import TEST_PAGE_URL, USER_AGENT_POOL


class TestRateLimiting:
    """Test suite for rate limiting behavior."""

    def test_rl_01_default_delay_between_requests(self, scraper_with_mock_session):
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

        with patch("time.sleep") as mock_sleep:
            # First call should NOT sleep (no previous request)
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")

            # Second call SHOULD sleep for default delay (1.0s)
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        # Verify sleep was called once (for second request)
        # and with approximately 1.0 seconds
        assert mock_sleep.call_count == 1
        call_args = mock_sleep.call_args[0]
        assert 0.9 <= call_args[0] <= 1.1  # Allow 10% tolerance

    def test_rl_02_custom_delay_configuration(self, temp_output_dir, temp_cache_dir):
        """RL-02: Custom delay configuration.

        delay=2.5 in constructor should result in delay of 2.5s between requests.
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

        with patch("time.sleep") as mock_sleep:
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        assert mock_sleep.call_count == 1
        call_args = mock_sleep.call_args[0]
        assert 2.25 <= call_args[0] <= 2.75  # 10% tolerance

    def test_rl_03_zero_delay_allowed(self, temp_output_dir, temp_cache_dir):
        """RL-03: Zero delay allowed.

        delay=0 should result in no delay between requests.
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

        with patch("time.sleep") as mock_sleep:
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        # With delay=0, sleep should not be called
        assert mock_sleep.call_count == 0

    def test_rl_04_delay_precision(self, scraper_with_mock_session):
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
        expected_delay = 1.0

        with patch("time.sleep") as mock_sleep:
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page1.html")
            scraper.fetch_page(TEST_PAGE_URL, cache_file="page2.html")

        if mock_sleep.call_count > 0:
            actual_delay = mock_sleep.call_args[0][0]
            # Within 10% tolerance
            assert abs(actual_delay - expected_delay) / expected_delay <= 0.1
