"""Mock response fixtures for scraper tests."""

from typing import Any

import requests


class MockResponse:
    """Mock requests.Response for testing."""

    def __init__(
        self,
        status_code: int = 200,
        text: str = "<html><body>Test</body></html>",
        headers: dict[str, str] | None = None,
        content: bytes | None = None,
        raise_error: Exception | None = None,
    ):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}
        self._content = content or text.encode("utf-8")
        self._raise_error = raise_error

    @property
    def content(self) -> bytes:
        return self._content

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error
        if self.status_code >= 400:
            # Create a mock response for the HTTPError
            raise requests.exceptions.HTTPError(
                f"{self.status_code} Error", response=self
            )

    def json(self) -> Any:
        import json

        return json.loads(self.text)


# Pre-built fixtures
SUCCESS_RESPONSE = MockResponse(200, "<html>Success</html>")
NOT_FOUND_RESPONSE = MockResponse(404)
RATE_LIMIT_RESPONSE = MockResponse(429, headers={"Retry-After": "2"})
RATE_LIMIT_NO_HEADER = MockResponse(429)
SERVER_ERROR_RESPONSE = MockResponse(500)
SERVICE_UNAVAILABLE = MockResponse(503, headers={"Retry-After": "5"})
TIMEOUT_ERROR = requests.exceptions.Timeout("Connection timed out")
CONNECTION_ERROR = requests.exceptions.ConnectionError("Connection failed")
