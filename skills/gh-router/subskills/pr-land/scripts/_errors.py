"""Exit-coded exception types for the pr-land CLI (`pr.py`) and its submodules.

A leaf module: it imports nothing from the entry script.
"""

import re

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


def failing_tool(message: str) -> str:
    """Tool name from a `run_command` failure message, or empty when unknown."""
    marker = "command not found or not executable: "
    if marker in message:
        return message.split(marker, 1)[1].split(":")[0].strip().split(" ")[0]
    marker = "command timed out after "
    if marker in message:
        _span, sep, cmd = message.split(marker, 1)[1].partition(":")
        if sep:
            argv = cmd.strip().split(" ")
            return argv[0] if argv else ""
    return ""


def infer_tool(message: str) -> str:
    """Guess the failing layer from message fingerprints, or empty when unknown.

    `gh`-side fingerprints win over `git`-side ones: a `gh api` failure quoting a
    `github.com` URL is still a `gh` failure, while a bare push/fetch-shaped
    message is `git`. Anything unrecognized stays empty and generic.
    """
    lowered = message.lower()
    if re.search(r"\bgh\b|gh api|pulls|mergeable|\bprs?\b|checks", lowered):
        return "gh"
    if any(
        marker in lowered
        for marker in (
            "github.com",
            "git ",
            "git:",
            "push",
            "fetch",
            "rev-list",
            "merge-base",
            "rebase",
            "origin/",
        )
    ):
        return "git"
    return ""


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
