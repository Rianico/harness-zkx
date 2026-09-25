"""Shared fixtures for the scaffold tests.

A TypeScript scaffold canonicalizes every byte it writes with the pinned formatter
(`skills/scaffold/scripts/scaffold.py` formatter contract), spawning the resolved oxfmt
once per file. That pass is real and tested, but running it for every
generator test here would dominate the suite for no extra signal, so it is off by
default; `test_oxfmt_canonical.py` turns it back on for the test that owns the contract.
"""

import pytest


@pytest.fixture(autouse=True)
def _no_formatter_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCAFFOLD_NO_FORMAT", "1")
