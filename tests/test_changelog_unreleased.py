"""Regression tests for scripts/changelog-unreleased.py (the release handoff)."""

from __future__ import annotations

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
    changelog.write_text(RELEASED_CHANGELOG, encoding="utf-8")

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
    changelog.write_text(released_only, encoding="utf-8")

    assert _run("clear", "--changelog", str(changelog)).returncode == 0
    assert changelog.read_text(encoding="utf-8") == released_only
