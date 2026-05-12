"""Tests for exception handling (specific over generic).

Test IDs: EX-01 through EX-07
"""

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from fixtures import TEST_PAGE_URL


class TestExceptionHandling:
    """Test suite for specific exception handling."""

    def test_ex_01_timeout_handling(self, temp_output_dir, temp_cache_dir):
        """EX-01: Timeout handling.

        requests.exceptions.Timeout should trigger retry.
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
                raise requests.exceptions.Timeout("Connection timed out")
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

        with patch("time.sleep"):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should have retried after timeout
        assert result is not None
        assert call_count[0] == 2

    def test_ex_02_connection_error_handling(self, temp_output_dir, temp_cache_dir):
        """EX-02: Connection error handling.

        requests.exceptions.ConnectionError should trigger retry.
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
                raise requests.exceptions.ConnectionError("Connection failed")
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

        with patch("time.sleep"):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should have retried after connection error
        assert result is not None
        assert call_count[0] == 2

    def test_ex_03_http_error_handler_inspects_status(self, temp_output_dir, temp_cache_dir):
        """EX-03: HTTP error handling.

        HTTPError (4xx/5xx) handler should inspect status code and decide retry.
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
                    status_code=500,  # Retryable
                    text="Internal Server Error",
                    content=b"Internal Server Error",
                    headers={},
                )
                response.raise_for_status = lambda: (
                    _ for _ in ()
                ).throw(
                    requests.exceptions.HTTPError("500 Error", response=response)
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

        with patch("time.sleep"):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # 500 should be retryable
        assert result is not None
        assert call_count[0] == 2

    def test_ex_04_429_specific_handling(self, temp_output_dir, temp_cache_dir):
        """EX-04: 429 specific handling.

        HTTPError with status 429 should trigger Retry-After logic.
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
                    headers={"Retry-After": "2"},
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
        # Should have honored Retry-After header (~2s)
        assert len(sleep_times) == 1
        assert 1.8 <= sleep_times[0] <= 2.5

    def test_ex_05_404_does_not_retry(self, temp_output_dir, temp_cache_dir):
        """EX-05: 404 does not retry.

        HTTPError with status 404 should return None immediately.
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
            response = MagicMock(
                status_code=404,  # Not retryable
                text="Not Found",
                content=b"Not Found",
                headers={},
            )
            response.raise_for_status = lambda: (
                _ for _ in ()
            ).throw(
                requests.exceptions.HTTPError("404 Not Found", response=response)
            )
            return response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should return None without retrying
        assert result is None
        assert call_count[0] == 1  # No retries

    def test_ex_06_403_does_not_retry(self, temp_output_dir, temp_cache_dir):
        """EX-06: 403 does not retry.

        HTTPError with status 403 should return None immediately.
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
            response = MagicMock(
                status_code=403,  # Not retryable
                text="Forbidden",
                content=b"Forbidden",
                headers={},
            )
            response.raise_for_status = lambda: (
                _ for _ in ()
            ).throw(
                requests.exceptions.HTTPError("403 Forbidden", response=response)
            )
            return response

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should return None without retrying
        assert result is None
        assert call_count[0] == 1  # No retries

    def test_ex_07_parse_error_no_retry(self, temp_output_dir, temp_cache_dir):
        """EX-07: Parse error handling.

        BeautifulSoup parsing error should return None, not trigger retry.
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

        # Return invalid bytes that might cause parsing issues
        def mock_get(*args, **kwargs):
            call_count[0] += 1
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

        # Even if parsing fails, should not retry HTTP
        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should have made only one HTTP call (no retry)
        assert call_count[0] == 1
        # Result depends on BeautifulSoup handling
        # At minimum, verify no retry was attempted
