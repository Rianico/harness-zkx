"""`CHANGELOG.md` must open with `# Changelog` — and the shipped guard must say so.

The shipped template states the rule, and `--detect` reports it, but nothing in CI held it: the
title regressed below the template's comment block in a real repo (`5276f34`, whose stated intent
was only dropping an empty `## [Unreleased]`) and no gate failed (#117). The guard that owns the
ledger owns the file's shape.

`test_changelog_waiver.py` covers the other half of the same workflow; `test_detect_drift.py`
covers the detector's half of this rule.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _scaffold_git_repo(tmp_path: Path) -> None:
    _ = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--flavor",
            "git",
            "--project-name",
            "demo",
            "--cwd",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "t@example.invalid"),
        ("config", "user.name", "t"),
        ("add", "-A"),
        ("commit", "-qm", "chore: init"),
    ):
        _ = subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True, text=True)


def _ledger_gate(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/changelog-gate.py", *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def _strand_the_title(changelog: Path) -> None:
    body = changelog.read_text(encoding="utf-8")
    assert body.startswith("# Changelog\n"), "the shipped template must open with the title"
    _ = changelog.write_text(f"<!-- keep the ledger curated -->\n{body}", encoding="utf-8")


def test_the_shipped_ledger_passes_the_guard_that_owns_its_shape(tmp_path: Path) -> None:
    _scaffold_git_repo(tmp_path)

    result = _ledger_gate(tmp_path, "ledger")

    assert result.returncode == 0, result.stdout + result.stderr


def test_the_gate_rejects_a_title_that_is_not_the_first_line(tmp_path: Path) -> None:
    _scaffold_git_repo(tmp_path)
    _strand_the_title(tmp_path / "CHANGELOG.md")

    result = _ledger_gate(tmp_path, "ledger")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "[title]" in result.stderr
    assert "must be the file's first line" in result.stderr
    assert "line 2" in result.stderr


def test_a_recorded_waiver_covers_the_title_finding(tmp_path: Path) -> None:
    """The title finding is fixable, so the waiver the workflow wires is its escape hatch."""
    _scaffold_git_repo(tmp_path)
    _strand_the_title(tmp_path / "CHANGELOG.md")

    result = _ledger_gate(tmp_path, "ledger", "--waiver", "title move tracked separately")

    assert result.returncode == 0, result.stdout + result.stderr


def test_the_detector_and_the_gate_read_the_title_rule_the_same_way(tmp_path: Path) -> None:
    """A detector that accepts a shape the gate rejects is the defect class #116 is about."""
    _scaffold_git_repo(tmp_path)

    def detector_says_title_at_top() -> bool:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--detect", "--json", "--cwd", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        census = cast("dict[str, object]", json.loads(result.stdout))
        changelog_state = cast("dict[str, object]", census["changelog"])
        return cast("bool", changelog_state["title_at_top"])

    def gate_accepts() -> bool:
        return _ledger_gate(tmp_path, "ledger").returncode == 0

    assert detector_says_title_at_top() is True
    assert gate_accepts() is True

    _strand_the_title(tmp_path / "CHANGELOG.md")

    assert detector_says_title_at_top() is False
    assert gate_accepts() is False
