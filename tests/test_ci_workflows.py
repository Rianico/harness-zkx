"""Pins the harness CI triggers that keep changelog drift visible on `main`.

`changelog-check.yml` triggered on `pull_request` only, so `main` itself was never checked:
its Unreleased section could sit stale until an unrelated PR happened to trip the hook, which
is how one PR's entries stayed un-regenerated until the next PR's push. The check now also
runs on push to `main`, so main reports its own staleness where it happens.
"""

from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
CHANGELOG_CHECK = WORKFLOWS / "changelog-check.yml"


def _text() -> str:
    return CHANGELOG_CHECK.read_text(encoding="utf-8")


def test_changelog_check_runs_on_main_push() -> None:
    """A `pull_request`-only trigger leaves `main` unchecked between merges."""
    assert "  push:\n    branches: [main]\n" in _text(), _text()


def test_changelog_check_concurrency_group_covers_push() -> None:
    """A push run has no pull-request number, so the group must fall back to a ref."""
    assert "github.event.pull_request.number || github.ref" in _text()


def test_changelog_check_comment_step_is_pr_only() -> None:
    """A push run has no PR to comment on; the script would fail on a null issue number."""
    assert "if: failure() && github.event_name == 'pull_request'" in _text()
