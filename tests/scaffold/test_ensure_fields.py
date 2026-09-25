"""Tests for per-field `ensure` ops and aliased coverage-script detection.

Boundary contract: manifests (`Cargo.toml`, `pyproject.toml`, `package.json`) and
`CONTRIBUTING.md` are user-owned — `--update` preserves them (see `test_update.py`).
`ensure <op>` performs one confirmed field edit the model decided on: absent fields
are added with minimal bytes, present fields report unchanged, never rewritten.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_ensure", SCRIPT)

CARGO = (
    '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2024"\n\n[dependencies]\nserde = "1"\n'
)
PYPROJECT = '[project]\nname = "demo"\nversion = "0.1.0"\ndependencies = []\n'
PKG = {
    "name": "demo",
    "scripts": {"test": "vitest run"},
    "devDependencies": {"vitest": "^5"},
}
VITEST = "export default { test: { coverage: { thresholds: { lines: 80, functions: 80 } } } };\n"


# --- rust-dep ---------------------------------------------------------------


def test_rust_dep_adds_entry_and_keeps_existing(tmp_path: Path):
    _ = (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    note = scaffold.ensure_cargo_dep(tmp_path, "tokio", "1")
    assert "added dependency" in note
    body = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    assert 'serde = "1"' in body
    assert 'tokio = "1"' in body


def test_rust_dep_present_reports_unchanged(tmp_path: Path):
    _ = (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    assert "unchanged" in scaffold.ensure_cargo_dep(tmp_path, "serde")


def test_rust_dep_creates_missing_section(tmp_path: Path):
    _ = (tmp_path / "Cargo.toml").write_text('[package]\nname = "demo"\n', encoding="utf-8")
    scaffold.ensure_cargo_dep(tmp_path, "serde")
    assert "[dependencies]" in (tmp_path / "Cargo.toml").read_text(encoding="utf-8")


def test_rust_dep_missing_file_and_bad_name(tmp_path: Path):
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_cargo_dep(tmp_path, "serde")
    _ = (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_cargo_dep(tmp_path, "bad name")


def test_rust_dep_dry_run_writes_nothing(tmp_path: Path):
    _ = (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    note = scaffold.ensure_cargo_dep(tmp_path, "tokio", dry_run=True)
    assert "dry-run" in note
    assert "tokio" not in (tmp_path / "Cargo.toml").read_text(encoding="utf-8")


# --- py-dep -----------------------------------------------------------------


def test_py_dep_adds_to_empty_and_nonempty_array(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    scaffold.ensure_py_dep(tmp_path, "httpx>=0.27")
    first = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '"httpx>=0.27",' in first
    scaffold.ensure_py_dep(tmp_path, "pydantic>=2")
    second = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert '"httpx>=0.27",' in second and '"pydantic>=2",' in second


def test_py_dep_present_reports_unchanged(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text(
        PYPROJECT.replace("[]", '[\n    "httpx>=0.27",\n]'), encoding="utf-8"
    )
    assert "unchanged" in scaffold.ensure_py_dep(tmp_path, "httpx")


def test_py_dep_missing_array_and_bad_req(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_py_dep(tmp_path, "httpx")
    _ = (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_py_dep(tmp_path, "!!!")


# --- ts-dep / ts-script ------------------------------------------------------


def test_ts_dep_and_script_add_and_keep_data(tmp_path: Path):
    _ = (tmp_path / "package.json").write_text(json.dumps(PKG, indent=2), encoding="utf-8")
    assert "added" in scaffold.ensure_ts_dep(tmp_path, "zod", "^3")
    assert "added" in scaffold.ensure_ts_script(tmp_path, "test:coverage", "vitest run --coverage")
    data = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert data["devDependencies"]["vitest"] == "^5"
    assert data["devDependencies"]["zod"] == "^3"
    assert data["scripts"]["test:coverage"] == "vitest run --coverage"


def test_ts_present_fields_report_unchanged(tmp_path: Path):
    _ = (tmp_path / "package.json").write_text(json.dumps(PKG, indent=2), encoding="utf-8")
    assert "unchanged" in scaffold.ensure_ts_dep(tmp_path, "vitest")
    assert "unchanged" in scaffold.ensure_ts_script(tmp_path, "test", "vitest run")


def test_ts_invalid_json_and_missing_section(tmp_path: Path):
    _ = (tmp_path / "package.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_ts_dep(tmp_path, "zod")
    # Missing section policy: create it (like ensure rust-dep creates
    # [dependencies]) — never advise re-running a whole flavor over
    # project-owned files.
    _ = (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    note = scaffold.ensure_ts_script(tmp_path, "lint", "oxlint .")
    assert "added" in note
    data = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert data["scripts"]["lint"] == "oxlint ."
    _ = (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    assert "added" in scaffold.ensure_ts_dep(tmp_path, "zod", "^3")
    data = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert data["devDependencies"]["zod"] == "^3"


def test_ts_non_object_section_refuses_with_narrow_hint(tmp_path: Path):
    _ = (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "scripts": "nope"}), encoding="utf-8"
    )
    with pytest.raises(scaffold.EnsureError) as excinfo:
        scaffold.ensure_ts_script(tmp_path, "lint", "oxlint .")
    assert "--flavor" not in str(excinfo.value)
    assert "by hand" in str(excinfo.value)


# --- coverage-threshold ------------------------------------------------------


def test_coverage_threshold_python_and_typescript(tmp_path: Path):
    _ = (tmp_path / "pyproject.toml").write_text(
        PYPROJECT + "\n[tool.coverage.report]\nfail_under = 80\n", encoding="utf-8"
    )
    assert "90" in scaffold.ensure_coverage_threshold(tmp_path, "python", 90)
    assert "fail_under = 90" in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    _ = (tmp_path / "vitest.config.ts").write_text(VITEST, encoding="utf-8")
    scaffold.ensure_coverage_threshold(tmp_path, "typescript", 90)
    assert "lines: 90" in (tmp_path / "vitest.config.ts").read_text(encoding="utf-8")


def test_coverage_threshold_refuses_bad_value_and_rust(tmp_path: Path):
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_coverage_threshold(tmp_path, "python", 101)
    with pytest.raises(scaffold.EnsureError):
        scaffold.ensure_coverage_threshold(tmp_path, "rust", 80)


# --- ensure_main dispatch ----------------------------------------------------


def test_ensure_main_end_to_end(tmp_path: Path, capsys):
    _ = (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    assert scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio"]) == 0
    assert "added dependency" in capsys.readouterr().out
    assert scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio"]) == 0
    assert "unchanged" in capsys.readouterr().out


def test_ensure_main_missing_file_exits_1(tmp_path: Path, capsys):
    assert scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx"]) == 1
    assert "error:" in capsys.readouterr().err


# --- aliased coverage detection (#50) ----------------------------------------


def test_aliased_coverage_script_is_detected(tmp_path: Path):
    pkg = dict(PKG)
    pkg["scripts"] = {"test:coverage": "vitest run --coverage"}
    _ = (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    release = tmp_path / ".github" / "workflows"
    release.mkdir(parents=True)
    _ = (release / "release.yml").write_text(
        "jobs:\n  verify:\n    steps:\n      - run: pnpm run test:coverage\n", encoding="utf-8"
    )
    result = scaffold.detect_project(tmp_path)
    assert result["typescript"]["coverage"] is True
    assert result["ci"]["coverage"] is True


def test_coverage_script_flag_threads_through_generation():
    pkg = json.loads(scaffold.build_package_json("demo", "lib", True, "test:coverage"))
    assert pkg["scripts"]["test:coverage"] == "vitest run --coverage"
    assert "coverage" not in pkg["scripts"]
    rendered = scaffold.render_ci_release(
        "node", with_coverage=True, threshold=80, coverage_script="test:coverage"
    )
    assert "pnpm run test:coverage" in rendered
