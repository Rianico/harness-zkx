"""Tests for pr-enhance's read-only drafting-template resolution (`--print-template`).

The resolution rule: the target repo's `.github/pull_request_template.md` is the schema when
present, else the canonical `skills/gh-router/references/pull_request_template.md`; exit 3 when
neither exists. pr-enhance must never write into the repo it analyzes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ANALYZE = REPO_ROOT / "skills/gh-router/subskills/pr-enhance/scripts/analyze-pr.py"
CANONICAL = REPO_ROOT / "skills/gh-router/references/pull_request_template.md"


def run_analyze(*args: str, cwd: Path, template_src: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("GH_ROUTER_TEMPLATE_SRC", None)
    if template_src is not None:
        env["GH_ROUTER_TEMPLATE_SRC"] = template_src
    return subprocess.run(
        [sys.executable, str(ANALYZE), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=30,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_print_template_prefers_repo_template(tmp_path: Path) -> None:
    repo_tpl = tmp_path / ".github" / "pull_request_template.md"
    repo_tpl.parent.mkdir(parents=True)
    repo_tpl.write_text("## Why\n")
    r = run_analyze("--print-template", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert Path(r.stdout.strip()) == repo_tpl.resolve()


def test_print_template_falls_back_to_canonical(tmp_path: Path) -> None:
    r = run_analyze("--print-template", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert CANONICAL.is_file(), "T1 canonical template must exist"
    assert Path(r.stdout.strip()) == CANONICAL.resolve()


def test_print_template_exits_three_when_no_schema_exists(tmp_path: Path) -> None:
    r = run_analyze("--print-template", cwd=tmp_path, template_src="/nonexistent/template.md")
    assert r.returncode == 3
    assert "template" in r.stderr
    assert not (tmp_path / ".github").exists()
    assert list(tmp_path.iterdir()) == []


def test_analysis_modes_never_write(tmp_path: Path) -> None:
    """Never-write invariant: --print-template and the analysis mode leave the tree byte-identical."""
    (tmp_path / "notes.md").write_text("keep\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "x.py").write_text("print(1)\n")
    before = snapshot(tmp_path)

    r = run_analyze("--print-template", cwd=tmp_path)
    assert r.returncode == 0, r.stderr

    # Analysis mode on a non-git temp repo must also write nothing and keep exiting 0.
    r2 = run_analyze("main", cwd=tmp_path)
    assert r2.returncode == 0, r2.stderr

    assert snapshot(tmp_path) == before
    assert not (tmp_path / ".github").exists()


def test_existing_analysis_output_shape_unchanged(tmp_path: Path) -> None:
    """The --print-template seam must not disturb the JSON analysis contract."""
    r = run_analyze("main", cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert r.stdout.lstrip().startswith("{")
