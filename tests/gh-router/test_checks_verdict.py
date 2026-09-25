"""Regression tests for the check verdict (lib/checks.sh).

The verdict used to be an inline jq allowlist naming `verify`, `check`, and `changelog-check`.
This repo's check runs are named `check` and `tests`, so the allowlist matched changelog-check
alone and reported success while the test suite was still running or failing — `--watch --merge`
would have merged red on an unprotected default branch.

The verdict is a pure function (`name<TAB>bucket` lines in, one word out) precisely so these
cases can be pinned without a network, a token, or a pull request.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CHECKS_LIB = REPO_ROOT / "skills/gh-router/lib/checks.sh"
PR_PY = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts/pr.py"
PR_SH = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts/pr.sh"

SCRIPTS_DIR = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from pr import (
    checks_verdict as py_checks_verdict,
)
from pr import (
    squash_message,
)

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
]


def _verdict(payload: str) -> str:
    result = subprocess.run(
        ["bash", "-c", f'source "{CHECKS_LIB}"\nprintf "%s" "$PAYLOAD" | checks_verdict'],
        capture_output=True,
        text=True,
        env={**os.environ, "PAYLOAD": payload},
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.mark.parametrize(("label", "lines", "expected"), CASES, ids=[c[0] for c in CASES])
def test_checks_verdict(label: str, lines: list[str], expected: str) -> None:
    # _verdict feeds the payload with `printf '%s'`, so no case has a trailing newline.
    payload = "\n".join(lines)
    assert _verdict(payload) == expected, f"bash lib mismatch on: {label}"
    assert py_checks_verdict(payload) == expected, f"pr.py mismatch on: {label}"


def test_verdict_ignores_check_names_entirely() -> None:
    """Two arbitrary names failing must fail — the verdict never keys on a name."""
    assert _verdict("some-future-check\tfail") == "failure"
    assert _verdict("some-future-check\tpass\nanother-one\tpass") == "success"
    assert py_checks_verdict("some-future-check\tfail") == "failure"
    assert py_checks_verdict("some-future-check\tpass\nanother-one\tpass") == "success"


def test_pr_no_longer_allowlists_check_names() -> None:
    """The fix must not be reintroduced as another name list."""
    text = PR_PY.read_text()

    assert "checks_verdict" in text, "pr.py does not use the shared verdict"
    assert "select(.name==" not in text, "pr.py filters checks by name again"
    assert ".check_runs[]" not in text, "pr.py hand-rolls check-run aggregation again"


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
