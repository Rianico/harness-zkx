"""Tests for Retry-After header handling.

Test IDs: RA-01 through RA-05
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from fixtures import TEST_PAGE_URL


class TestRetryAfter:
    """Test suite for Retry-After header handling."""

    def test_ra_01_retry_after_seconds(self, temp_output_dir, temp_cache_dir):
        """RA-01: 429 with Retry-After (seconds).

        Status 429 with header 'Retry-After: 5' should wait 5s, then retry.
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
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock(
                    status_code=429,
                    text="Too Many Requests",
                    content=b"Too Many Requests",
                    headers={"Retry-After": "5"},
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("429 Error", response=response)
                )
                return response
            else:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 1
        # Should have waited approximately 5 seconds
        assert 4.5 <= sleep_times[0] <= 5.5

    def test_ra_02_retry_after_http_date(self, temp_output_dir, temp_cache_dir):
        """RA-02: 429 with Retry-After (HTTP date).

        Status 429 with HTTP date header should wait until specified time.
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
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        # Create a future date 5 seconds from now (more buffer for timing)
        future_time = datetime.now(timezone.utc) + timedelta(seconds=5)
        http_date = future_time.strftime("%a, %d %b %Y %H:%M:%S GMT")

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock(
                    status_code=429,
                    text="Too Many Requests",
                    content=b"Too Many Requests",
                    headers={"Retry-After": http_date},
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("429 Error", response=response)
                )
                return response
            else:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 1
        # Should have waited approximately 5 seconds (with wide tolerance for timing)
        assert 3.5 <= sleep_times[0] <= 6.0

    def test_ra_03_retry_after_missing_uses_backoff(self, temp_output_dir, temp_cache_dir):
        """RA-03: 429 without Retry-After.

        Status 429 without header should use exponential backoff as fallback.
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
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock(
                    status_code=429,
                    text="Too Many Requests",
                    content=b"Too Many Requests",
                    headers={},  # No Retry-After header
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("429 Error", response=response)
                )
                return response
            else:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 1
        # Should have used exponential backoff (~1s for first retry)
        assert 0.8 <= sleep_times[0] <= 1.5

    def test_ra_04_503_with_retry_after(self, temp_output_dir, temp_cache_dir):
        """RA-04: 503 with Retry-After.

        Status 503 with header 'Retry-After: 3' should wait 3s, then retry.
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
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock(
                    status_code=503,
                    text="Service Unavailable",
                    content=b"Service Unavailable",
                    headers={"Retry-After": "3"},
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("503 Error", response=response)
                )
                return response
            else:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 1
        # Should have waited approximately 3 seconds
        assert 2.5 <= sleep_times[0] <= 3.5

    def test_ra_05_retry_after_capped(self, temp_output_dir, temp_cache_dir):
        """RA-05: Retry-After caps at reasonable max.

        Header 'Retry-After: 3600' should cap delay to prevent excessive wait.
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
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                response = MagicMock(
                    status_code=429,
                    text="Too Many Requests",
                    content=b"Too Many Requests",
                    headers={"Retry-After": "3600"},  # 1 hour - way too long
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("429 Error", response=response)
                )
                return response
            else:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 1
        # Should have capped the delay to MAX_RETRY_AFTER (60s by default)
        assert sleep_times[0] <= 60
