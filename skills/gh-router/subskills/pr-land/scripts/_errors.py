"""Exit-coded exception types for the pr-land CLI (`pr.py`) and its submodules.

A leaf module: it imports nothing from the entry script.
"""

from typing import override

REFUSAL_SCHEMA = "gh-router/pr-land/refusal@1"


def make_refusal(code: str, reason: str, remedy: str, site: str) -> dict[str, str]:
    """One `refusals[]` entry. `site` names the caller's input or artifact.

    `site` is a flag (`--title`), a caller file (`pr_body.md:12`), a caller ref
    (`origin/feat-x`), or the `gh` dependency — never a pr-land source location,
    which stays behind `--verbose`.
    """
    return {"code": code, "reason": reason, "remedy": remedy, "site": site}


def make_transition(command: str, preconditions: list[str], mutation: str) -> dict[str, object]:
    """One legal `transitions[]` entry: the command, what it needs, what it mutates."""
    if mutation not in ("none", "local", "remote"):
        raise ValueError(f"unknown mutation {mutation!r}")
    return {"command": command, "preconditions": list(preconditions), "mutation": mutation}


class PrError(Exception):
    """Base exception for pr module."""


class CommandFailed(PrError):
    """A subprocess that ran and failed (or never ran): the package wire format.

    `tool` comes from `argv[0]` (`git` / `gh` / other) — structural, never
    parsed from stderr. `returncode` is None when the command never produced an
    exit status (timeout, missing binary). `str()` keeps the legacy message
    shape so prose asserts keep passing.
    """

    tool: str
    argv: list[str]
    returncode: int | None
    stderr: str

    def __init__(
        self,
        tool: str,
        argv: list[str],
        returncode: int | None,
        stderr: str,
    ) -> None:
        self.tool = tool
        self.argv = list(argv)
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(stderr)

    @override
    def __str__(self) -> str:
        return self.stderr


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
