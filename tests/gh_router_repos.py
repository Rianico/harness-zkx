"""Shared git fixtures and the brief runner for the gh-router test suite.

`tests/gh-router/` cannot be imported as a package (the dash blocks module
syntax), so the helpers that were copy-pasted across its test files live here.
The brief runner executes `brief.py` in-process (see `tests.in_process`): the
script's contract is argv/cwd in, stdout/exit code out, which is exactly what
these tests assert on.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests.in_process import run_script_in_process

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (
    REPO_ROOT / "skills" / "gh-router" / "subskills" / "git-diff-digest" / "scripts" / "brief.py"
)


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def seed_diverged_repo(repo: Path) -> dict[str, str]:
    """Build a diverged feature branch with conventional commits."""
    _ = git(repo, "init")
    _ = git(repo, "config", "user.name", "Tester Author")
    _ = git(repo, "config", "user.email", "tester@example.com")
    _ = git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "src").mkdir()
    _ = (repo / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _ = (repo / "src" / "parser.py").write_text("def parse(x):\n    return x\n", encoding="utf-8")
    _ = git(repo, "add", ".")
    _ = git(repo, "commit", "-m", "chore: base commit")
    base = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _ = git(repo, "checkout", "-b", "feature")
    _ = (repo / "src" / "app.py").write_text("print('v1')\nprint('v2')\n", encoding="utf-8")
    _ = git(repo, "add", ".")
    _ = git(repo, "commit", "-m", "feat: add parser")
    first = git(repo, "rev-parse", "HEAD")
    _ = (repo / "tests").mkdir()
    _ = (repo / "tests" / "test_app.py").write_text(
        "def test_v2():\n    assert True\n", encoding="utf-8"
    )
    _ = git(repo, "add", ".")
    _ = git(
        repo,
        "commit",
        "-m",
        f"fix: handle empty input\n\nCovers the empty case.\n\nRefs #12, follow-up to {first[:7]}.",
    )
    _ = (repo / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    _ = (repo / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    _ = git(repo, "add", ".")
    _ = git(repo, "commit", "-m", "feat(api)!: drop legacy field\n\nBREAKING CHANGE: legacy gone.")
    _ = git(repo, "mv", "src/parser.py", "src/scanner.py")
    _ = git(repo, "commit", "-m", "refactor: rename parser module")
    _ = git(repo, "checkout", base)
    _ = (repo / "docs").mkdir()
    _ = (repo / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    _ = git(repo, "add", ".")
    _ = git(repo, "commit", "-m", "docs: tweak guide")
    return {"base": base, "first": first}


def run_brief(repo: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return run_script_in_process(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd if cwd is not None else repo,
    )


def brief_payload(repo: Path, *args: str) -> Any:
    result = run_brief(repo, *args)
    assert result.returncode == 0, f"brief failed: {result.stderr}"
    return json.loads(result.stdout)
