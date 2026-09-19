"""F4 round: section-aware TOML locate + prose-safe threshold detect.

One falsifiable test per finding F1..F4. Reverting the fix makes its test fail.
"""

import importlib.util
import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_fix4", SCRIPT)


def test_f1_single_quoted_dep_reports_unchanged_byte_identical(tmp_path: Path):
    body = '[project]\nname = "demo"\nversion = "0.1.0"\ndependencies = [\'httpx>=0.27\']\n'
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    before = (tmp_path / "pyproject.toml").read_bytes()
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx>=0.27"])
    assert rc == 0
    assert (tmp_path / "pyproject.toml").read_bytes() == before


def test_f2_other_table_dependencies_refuses_naming_table(tmp_path: Path, capsys):
    body = '[project]\nname = "demo"\nversion = "0.1.0"\n\n[tool.other]\ndependencies = []\n'
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    before = (tmp_path / "pyproject.toml").read_bytes()
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx>=0.27"])
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_bytes() == before
    assert "tool.other" in capsys.readouterr().err


def test_f3_run_only_fail_under_refuses_unchanged(tmp_path: Path):
    body = (
        '[project]\nname = "demo"\nversion = "0.1.0"\ndependencies = []\n\n'
        "[tool.coverage.run]\nfail_under = 80\n"
    )
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    before = (tmp_path / "pyproject.toml").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "python", "--value", "90"]
    )
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_bytes() == before


def test_f4_description_prose_threshold_stays_null(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "name": "demo",
                "description": "coverage.thresholds.lines=85",
                "scripts": {"test": "vitest run"},
            }
        ),
        encoding="utf-8",
    )
    data = scaffold.detect_project(tmp_path)
    assert data["typescript"]["coverage"] is False
    assert data["typescript"]["threshold"] is None
