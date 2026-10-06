"""Byte-for-byte guard for the conflict extractor golden fixture.

The golden file stores the pre-refactor summary stdout, both exact and with
the volatile ``repo:`` line normalised to ``<REPO_ROOT>``. The guard rebuilds
an identical conflicted repo (summary output carries no SHAs or dates, so it
is deterministic) and compares normalised bytes exactly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
SCRIPT_PATH = (
    REPO_ROOT / "skills" / "gh-router" / "subskills" / "pr-conflict" / "scripts"
) / "extract_conflict_context.py"
GOLDEN_PATH = FIXTURES_DIR / "conflict_extractor_golden.json"


def _git(repo: Path, *args: str) -> None:
    _ = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _build_conflict_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.name", "Tester Author")
    _git(repo, "config", "user.email", "tester@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "common.txt").write_text("base line\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: base commit")
    base = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    _git(repo, "checkout", "-b", "feat/calc")
    _ = (repo / "app.py").write_text("def calc(): return 'feature'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "feat(calc): implement feature calc")
    _git(repo, "checkout", base)
    _ = (repo / "app.py").write_text("def calc(): return 'main'\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "fix(calc): hotfix main calc")
    merged = subprocess.run(
        ["git", "-C", str(repo), "merge", "feat/calc"],
        capture_output=True,
        text=True,
    )
    assert merged.returncode != 0


def _normalise(stdout: str) -> bytes:
    lines = stdout.splitlines(keepends=True)
    assert lines[0].startswith("repo: ")
    return ("repo: <REPO_ROOT>\n" + "".join(lines[1:])).encode("utf-8")


def test_conflict_extractor_golden_bytes(tmp_path: Path) -> None:
    _build_conflict_repo(tmp_path)
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))

    assert completed.returncode == golden["returncode"]
    assert golden["stdout_exact"].splitlines()[1:] == completed.stdout.splitlines()[1:]
    assert _normalise(completed.stdout) == golden["stdout_normalized"].encode("utf-8")
