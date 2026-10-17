"""Exit-coded exception types for the pr-land CLI (`pr.py`) and its submodules.

A leaf module: it imports nothing from the entry script.
"""


class PrError(Exception):
    """Base exception for pr module."""


class UsageError(PrError):
    """Usage or configuration error (exit code 2)."""


class RefusalError(PrError):
    """Operation refused by policy (exit code 1)."""

    def __init__(
        self,
        message: str = "",
        *,
        refusals: list[dict[str, str]] | None = None,
        transitions: list[dict[str, object]] | None = None,
    ) -> None:
        super().__init__(message)
        self.refusals: list[dict[str, str]] = list(refusals or [])
        self.transitions: list[dict[str, object]] = list(transitions or [])


class CheckFailureError(PrError):
    """Checks failed (exit code 1)."""
