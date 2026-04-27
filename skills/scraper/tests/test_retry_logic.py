"""Tests for retry logic with exponential backoff.

Test IDs: RB-01 through RB-07
"""

from unittest.mock import MagicMock, patch

import pytest
import requests.exceptions

from fixtures import TEST_PAGE_URL, SERVER_ERROR_RESPONSE, SUCCESS_RESPONSE


class TestRetryLogic:
    """Test suite for retry behavior."""

    def test_rb_01_success_on_first_attempt(self, scraper_with_mock_session):
        """RB-01: Success on first attempt.

        200 OK response should result in no retry, immediate return.
        """
        scraper = scraper_with_mock_session
        mock_session = scraper.session

        success_response = MagicMock(
            status_code=200,
            text="<html>Success</html>",
            content=b"<html>Success</html>",
            headers={},
        )
        success_response.raise_for_status = lambda: None
        mock_session.get.return_value = success_response

        result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should return BeautifulSoup, not None
        assert result is not None
        # Should only call get once (no retries)
        # Note: robots.txt is disabled in scraper_with_mock_session fixture
        assert mock_session.get.call_count == 1

    def test_rb_02_success_on_second_attempt(self, temp_output_dir, temp_cache_dir):
        """RB-02: Success on second attempt.

        500 then 200 should result in one retry, success returned.
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
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: 500 error
                response = MagicMock(
                    status_code=500,
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
                # Second call: success
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

        with patch("time.sleep"):  # Mock sleep to avoid delays
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert call_count[0] == 2  # Initial + 1 retry

    def test_rb_03_success_on_third_attempt(self, temp_output_dir, temp_cache_dir):
        """RB-03: Success on third attempt.

        500, 500, then 200 should result in two retries, success returned.
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
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 2:
                # First two calls: 500 error
                response = MagicMock(
                    status_code=500,
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
                # Third call: success
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

        assert result is not None
        assert call_count[0] == 3  # Initial + 2 retries

    def test_rb_04_failure_after_max_retries(self, temp_output_dir, temp_cache_dir):
        """RB-04: Failure after max retries.

        Three 500 responses should return None after 3 attempts.
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
            max_retries=3,
            respect_robots_txt=False,  # Disable to avoid extra calls
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            response = MagicMock(
                status_code=500,
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

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        with patch("time.sleep"):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should return None after exhausting retries
        assert result is None
        # Initial + max_retries attempts
        assert call_count[0] == 4  # 1 initial + 3 retries

    def test_rb_05_exponential_backoff_timing(self, temp_output_dir, temp_cache_dir):
        """RB-05: Exponential backoff timing.

        Connection error on first try should result in second attempt after ~1s,
        third after ~2s.
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
            if call_count[0] < 3:
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

        sleep_times = []

        def capture_sleep(duration):
            sleep_times.append(duration)

        with patch("time.sleep", side_effect=capture_sleep):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        assert result is not None
        assert len(sleep_times) == 2
        # First retry: ~1s, second retry: ~2s (with tolerance)
        assert 0.8 <= sleep_times[0] <= 1.5
        assert 1.6 <= sleep_times[1] <= 3.0

    def test_rb_06_max_retries_configurable(self, temp_output_dir, temp_cache_dir):
        """RB-06: Max retries configurable.

        max_retries=5 with 4 failures then success should retry 4 times,
        succeed on 5th.
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
            max_retries=5,
        )

        mock_session = MagicMock()
        call_count = [0]

        def mock_get(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 5:
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

        assert result is not None
        # 1 initial + 4 retries = 5 calls (succeeds on 5th)
        assert call_count[0] == 5

    def test_rb_07_zero_retries_allowed(self, temp_output_dir, temp_cache_dir):
        """RB-07: Zero retries allowed.

        max_retries=0 should return None on first failure without retrying.
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
            max_retries=0,
        )

        mock_session = MagicMock()

        def mock_get(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Connection failed")

        mock_session.get = mock_get
        mock_session.headers = {}
        scraper.session = mock_session

        with patch("time.sleep"):
            result = scraper.fetch_page(TEST_PAGE_URL, cache_file="test.html")

        # Should return None immediately without retrying
        assert result is None
