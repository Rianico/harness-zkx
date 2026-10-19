"""Regression tests for the check verdict (`_github.checks_verdict`).

The verdict used to be an inline jq allowlist naming `verify`, `check`, and `changelog-check`.
This repo's check runs are named `check` and `tests`, so the allowlist matched changelog-check
alone and reported success while the test suite was still running or failing — `--watch --merge`
would have merged red on an unprotected default branch.

The shell twin (`lib/checks.sh`) counted all-skipped runs as success; the Python gate
returns `pending` for them (zero CI is not green). The shell copy is deleted — one
implementation, one verdict — and the all-skipped case below pins the unified behavior.

The verdict is a pure function (`name<TAB>bucket` lines in, one word out) precisely so these
cases can be pinned without a network, a token, or a pull request.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
from _github import checks_verdict as py_checks_verdict
from _squash import squash_message

CASES = [
    ("a single passing check is green", ["tests\tpass"], "success"),
    ("skipping checks do not block green", ["a\tpass", "b\tskipping"], "success"),
    ("a failure beside a pass is a failure", ["tests\tpass", "check\tfail"], "failure"),
    ("cancel counts as failure", ["x\tcancel"], "failure"),
    ("pending is not green", ["a\tpass", "b\tpending"], "pending"),
    ("failure outranks pending", ["b\tfail", "a\tpending"], "failure"),
    ("no checks at all is pending, never success", [], "pending"),
    ("a blank line is not a check", [""], "pending"),
    # The bug itself: a check whose name is absent from any allowlist must still count.
    ("a non-allowlisted check still counts", ["tests\tfail"], "failure"),
    ("an unknown bucket degrades to pending", ["x\tbrand-new-bucket"], "pending"),
    ("all skipped is pending, zero CI is not green", ["a\tskipping"], "pending"),
    ("all skipped across many checks is pending", ["a\tskipping", "b\tskipping"], "pending"),
]


@pytest.mark.parametrize(("label", "lines", "expected"), CASES, ids=[c[0] for c in CASES])
def test_checks_verdict(label: str, lines: list[str], expected: str) -> None:
    payload = "\n".join(lines)
    assert py_checks_verdict(payload) == expected, f"verdict mismatch on: {label}"


def test_verdict_ignores_check_names_entirely() -> None:
    """Two arbitrary names failing must fail — the verdict never keys on a name."""
    assert py_checks_verdict("some-future-check\tfail") == "failure"
    assert py_checks_verdict("some-future-check\tpass\nanother-one\tpass") == "success"


def test_pr_no_longer_allowlists_check_names() -> None:
    """The fix must not be reintroduced as another name list.

    pr-land is several modules since the split, so the scan covers the whole module set:
    a re-export line in `pr.py` alone would satisfy a single-file grep while proving nothing.
    """
    texts = {path.name: path.read_text() for path in sorted(SCRIPTS_DIR.glob("*.py"))}
    assert texts, "pr-land scripts directory is empty"

    # A call site, not just a binding: the definition in `_github.py` and the re-export line
    # in `pr.py` both contain the substring `checks_verdict(`, so a text scan proves nothing.
    # Parse each module and require a real `ast.Call` to the verdict.
    callers = [
        name
        for name, text in texts.items()
        if any(
            isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "checks_verdict")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "checks_verdict")
            )
            for node in ast.walk(ast.parse(text, filename=name))
        )
    ]
    assert callers, "no pr-land module calls the shared checks_verdict"
    for name, text in texts.items():
        assert "select(.name==" not in text, f"{name} filters checks by name again"
        assert ".check_runs[]" not in text, f"{name} hand-rolls check-run aggregation again"


def test_squash_message_defaults_to_the_pr_body() -> None:
    """Provenance lives in the PR body, so the squash body must be the PR body.

    The previous hardcoded `Squash merge <head> → <base>` dropped the `Co-authored-by` trailer
    that git-convention requires to survive a squash.
    """
    body = (
        "Summary of the change.\n\nCloses #33\n\nCo-authored-by: deepseek-v4.1-flash <noreply@ai>\n"
    )
    result = squash_message(body)

    assert result == body
    assert "Co-authored-by: deepseek-v4.1-flash <noreply@ai>" in result
    assert "Squash merge" not in result
