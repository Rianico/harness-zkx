"""The waiver the ledger failure comment advertises must be the waiver the workflow passes.

The comment told the contributor the ledger "is waived only with a recorded reason:
`--waiver "<reason>"`, written in this PR body" — while the shipped step parsed only `Landing:` and
never passed `--waiver`. Following the instruction re-ran into the identical failure with no signal
that it could not be followed (#118).

`test_changelog_title_gate.py` covers the title guard the same step wires; this file covers the
trailer, and runs the shipped step's script verbatim under `bash -e`, the shell GitHub Actions
gives it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "scaffold"
WORKFLOW = SKILL_DIR / "templates" / "git" / ".github" / "workflows" / "changelog-check.yml"

# Records the argv the shipped step really builds, one argument per line.
GATE_STUB = """\
import pathlib
import sys

pathlib.Path("argv.txt").write_text("\\n".join(sys.argv[1:]), encoding="utf-8")
"""


def _ledger_floor_script() -> str:
    """The shipped `Ledger floor` step, verbatim — what a contributor's PR actually runs."""
    workflow = cast("dict[str, object]", yaml.safe_load(WORKFLOW.read_text(encoding="utf-8")))
    jobs = cast("dict[str, object]", workflow["jobs"])
    check = cast("dict[str, object]", jobs["check"])
    steps = cast("list[dict[str, object]]", check["steps"])
    step = next(item for item in steps if item.get("name") == "Ledger floor")
    return cast("str", step["run"])


def _run_floor(tmp_path: Path, *, pr_body: str, pr_number: str = "34") -> list[str]:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    _ = (repo / "scripts" / "changelog-gate.py").write_text(GATE_STUB, encoding="utf-8")
    script = tmp_path / "floor.sh"
    _ = script.write_text(_ledger_floor_script(), encoding="utf-8")

    # The step calls `python`, so the shim keeps the script byte-verbatim instead of rewriting it.
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "python").symlink_to(sys.executable)

    result = subprocess.run(
        ["bash", "-e", str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PATH": f"{shim}{os.pathsep}{os.environ['PATH']}",
            "PR_NUMBER": pr_number,
            "PR_BODY": pr_body,
        },
    )

    assert result.returncode == 0, result.stdout + result.stderr
    return (repo / "argv.txt").read_text(encoding="utf-8").splitlines()


def test_the_workflow_forwards_a_ledger_waiver_trailer(tmp_path: Path) -> None:
    argv = _run_floor(
        tmp_path,
        pr_body="Landing: merge\n\nLedger-Waiver: backfilled attribution in #34\n",
    )

    assert argv == [
        "ledger",
        "--pr",
        "34",
        "--landing",
        "merge",
        "--base",
        "main",
        "--waiver",
        "backfilled attribution in #34",
    ]


def test_the_workflow_passes_no_waiver_when_the_pr_body_has_none(tmp_path: Path) -> None:
    argv = _run_floor(tmp_path, pr_body="Landing: squash\n\nno waiver in this body\n")

    assert argv == ["ledger", "--pr", "34", "--landing", "squash", "--base", "main"]


def test_the_advertised_waiver_is_the_one_the_workflow_wires() -> None:
    assert "Ledger-Waiver:" in WORKFLOW.read_text(encoding="utf-8")
    assert "--waiver" in _ledger_floor_script()
