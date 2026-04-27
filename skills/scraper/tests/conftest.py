"""Pytest configuration and shared fixtures for scraper tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the scraper scripts directory to the path for imports
# When running from project root: skills/scraper/scripts/scrapers
scraper_path = Path(__file__).parent.parent / "scripts" / "scrapers"
scraper_path = scraper_path.resolve()
if str(scraper_path) not in sys.path:
    sys.path.insert(0, str(scraper_path))

# Add the tests directory for fixture imports
tests_path = Path(__file__).parent.resolve()
if str(tests_path) not in sys.path:
    sys.path.insert(0, str(tests_path))

from fixtures import (
    MockResponse,
    SUCCESS_RESPONSE,
    NOT_FOUND_RESPONSE,
    RATE_LIMIT_RESPONSE,
    SERVER_ERROR_RESPONSE,
    SERVICE_UNAVAILABLE,
    TIMEOUT_ERROR,
    CONNECTION_ERROR,
    ALLOW_ALL_ROBOTS,
    BLOCK_ALL_ROBOTS,
    CRAWL_DELAY_ROBOTS,
    TEST_BASE_URL,
    TEST_PAGE_URL,
    USER_AGENT_POOL,
)


@pytest.fixture
def mock_session():
    """Create a mock requests.Session for testing."""
    session = MagicMock()
    session.headers = {}
    session.get = MagicMock(return_value=SUCCESS_RESPONSE)
    return session


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for testing."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def scraper_with_mock_session(mock_session, temp_output_dir, temp_cache_dir):
    """Create a DocumentationScraper instance with mocked session.

    Note: respect_robots_txt is set to False by default for tests that
    don't specifically test robots.txt functionality. This prevents
    interference from robots.txt fetches in the test call counts.
    """
    # Import here to avoid import errors during collection
    # The path was added at module load time, so we can import base directly
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
        respect_robots_txt=False,  # Disable robots.txt for non-robots tests
    )
    scraper.session = mock_session
    return scraper
