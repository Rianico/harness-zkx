"""Regression tests for scripts/changelog-unreleased.py (the release handoff)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "changelog-unreleased.py"

RELEASED_CHANGELOG = """\
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Features

- something still unreleased

## [2.0.0](https://example.invalid/compare/v1.0.0...v2.0.0) (2026-09-12)

### Bug Fixes

- something already released
"""


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=str(REPO_ROOT), capture_output=True, text=True
    )


def test_clear_empties_the_block_but_keeps_its_heading(tmp_path: Path) -> None:
    """`clear` must not delete the Unreleased heading.

    @semantic-release/changelog anchors its insertion point on that heading. With the heading
    gone, the plugin prepends the new version section above everything - the v2.0.0 release left
    CHANGELOG.md starting with `## [2.0.0]` and the `# Changelog` title stranded at the bottom.
    """
    changelog = tmp_path / "CHANGELOG.md"
    _ = changelog.write_text(RELEASED_CHANGELOG, encoding="utf-8")

    result = _run("clear", "--changelog", str(changelog))

    assert result.returncode == 0, result.stderr
    cleared = changelog.read_text(encoding="utf-8")
    assert "## [Unreleased]" in cleared, "heading removed — semantic-release loses its anchor"
    assert "something still unreleased" not in cleared, "block should be emptied"
    assert "something already released" in cleared, "released history must survive"
    assert cleared.startswith("# Changelog\n"), "title must stay at the top of the file"
    assert cleared.index("## [Unreleased]") < cleared.index("## [2.0.0]"), "wrong section order"


def test_clear_is_a_noop_without_an_unreleased_section(tmp_path: Path) -> None:
    """Nothing to clear: `clear` reports no change rather than rewriting the file."""
    changelog = tmp_path / "CHANGELOG.md"
    released_only = "# Changelog\n\n## [1.0.0](x) (2026-01-01)\n\n- done\n"
    _ = changelog.write_text(released_only, encoding="utf-8")

    assert _run("clear", "--changelog", str(changelog)).returncode == 0
    assert changelog.read_text(encoding="utf-8") == released_only


def test_update_emits_the_same_bullet_style_as_semantic_release(tmp_path: Path) -> None:
    """Entries use `*`, matching @semantic-release/changelog's notes body.

    A mixed file makes pi-lens's markdown fixer normalise the whole generated section to the
    style of the first bullet it meets, which rode ~230 lines of churn into unrelated commits.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    changelog = repo / "CHANGELOG.md"
    _ = changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.0.0](x) (2026-01-01)\n\n* released\n",
        encoding="utf-8",
    )
    setup: list[list[str]] = [
        ["init", "-q"],
        ["config", "user.email", "t@example.invalid"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "-qm", "chore: init"],
        ["tag", "v1.0.0"],
        ["commit", "-q", "--allow-empty", "-m", "feat(thing): add a thing"],
    ]
    for args in setup:
        _ = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "update", "--changelog", str(changelog)],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    updated = changelog.read_text(encoding="utf-8")
    assert "* **thing:** add a thing" in updated, updated
    assert "- **thing:**" not in updated, updated


def _repo_with_a_visible_commit(tmp_path: Path, changelog_text: str) -> tuple[Path, Path]:
    """Build a repo sitting one visible commit past v1.0.0, with the given CHANGELOG.md."""
    repo = tmp_path / "repo"
    repo.mkdir()
    changelog = repo / "CHANGELOG.md"
    _ = changelog.write_text(changelog_text, encoding="utf-8")
    setup: list[list[str]] = [
        ["init", "-q"],
        ["config", "user.email", "t@example.invalid"],
        ["config", "user.name", "t"],
        ["add", "-A"],
        ["commit", "-qm", "chore: init"],
        ["tag", "v1.0.0"],
        ["commit", "-q", "--allow-empty", "-m", "feat(thing): add a thing"],
    ]
    for args in setup:
        _ = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)
    return repo, changelog


def test_check_reports_drift_without_mutating_the_file(tmp_path: Path) -> None:
    """`check` is read-only: drift exits 1 with a diff and leaves the bytes on disk untouched.

    This is the mode a convergence Finalize runs on the integration worktree. It must fail loud
    on drift without producing the uncommitted diff that marked a fully-merged run BLOCKED.
    """
    stale = "# Changelog\n\n## [Unreleased]\n\n### Features\n\n* stale hand-written bullet\n"
    repo, changelog = _repo_with_a_visible_commit(tmp_path, stale)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--changelog", str(changelog)],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, result.stdout
    assert "add a thing" in result.stderr, result.stderr
    assert changelog.read_text(encoding="utf-8") == stale, "check must not rewrite the file"


def test_check_is_in_sync_after_update(tmp_path: Path) -> None:
    """`check` and `update` share one renderer, so check is green immediately after update."""
    repo, changelog = _repo_with_a_visible_commit(
        tmp_path, "# Changelog\n\n## [Unreleased]\n\n## [1.0.0](x) (2026-01-01)\n\n* released\n"
    )

    upd = subprocess.run(
        [sys.executable, str(SCRIPT), "update", "--changelog", str(changelog)],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert upd.returncode == 0, upd.stderr

    chk = subprocess.run(
        [sys.executable, str(SCRIPT), "check", "--changelog", str(changelog)],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert chk.returncode == 0, chk.stderr
    assert chk.stdout.strip() == "in sync"


def test_repo_changelog_pins_md004_to_asterisk() -> None:
    """This repo's own CHANGELOG.md pins the style it is written in.

    The pin is what keeps pi-lens's markdown fixer from re-normalising the generated
    sections to `-`; without it any markdown touch rewrites the whole file.
    """
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"markdownlint-configure-file\s*(\{.*?\})\s*-->", changelog, re.DOTALL)
    assert match is not None, "CHANGELOG.md lost its markdownlint-configure-file pin"
    assert json.loads(match.group(1))["MD004"]["style"] == "asterisk"
