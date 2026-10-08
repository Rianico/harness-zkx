"""Exit-coded exception types for the pr-land CLI (`pr.py`) and its submodules.

A leaf module: it imports nothing from the entry script.
"""


class PrError(Exception):
    """Base exception for pr module."""


class UsageError(PrError):
    """Usage or configuration error (exit code 2)."""


class RefusalError(PrError):
    """Operation refused by policy (exit code 1)."""


class CheckFailureError(PrError):
    """Checks failed (exit code 1)."""
