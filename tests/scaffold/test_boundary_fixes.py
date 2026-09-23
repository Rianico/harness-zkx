"""Falsifiable tests for the 12 scaffold-boundary fixes (fix-r1).

Each test fails when its fix is reverted: invalid values exit non-zero with an
unchanged file, non-ASCII stays literal, all four thresholds move together, the
rust probe is scoped, missing sections are created, configs are preserved,
detection is name-agnostic, coverage-script defaults and threads, docs state
the contract, changelog copies stay equal, and NEXT hints are runnable.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_boundary", SCRIPT)

CARGO = '[package]\nname = "demo"\nversion = "0.1.0"\nedition = "2024"\n\n[dependencies]\nserde = "1"\n'
PYPROJECT = '[project]\nname = "demo"\nversion = "0.1.0"\ndependencies = []\n'


def _run_main(*argv: str) -> int:
    old = sys.argv
    sys.argv = ["scaffold.py", *argv]
    try:
        return scaffold.main()
    finally:
        sys.argv = old


# --- 1: ensure_main runs self_check and exits non-zero on blocking ---
def test_1_ensure_main_runs_self_check_on_written_path(tmp_path: Path, monkeypatch):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    seen: list = []
    orig = scaffold.self_check

    def spy(targets):
        seen.extend(targets)
        return orig(targets)

    monkeypatch.setattr(scaffold, "self_check", spy)
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio"])
    assert rc == 0
    assert any(str(p).endswith("Cargo.toml") for p in seen)


def test_1_ensure_main_exits_1_on_blocking_finding(tmp_path: Path, monkeypatch):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")

    def fake(_targets):
        return [scaffold.Finding("x", "python syntax error: bad", "", True)]

    monkeypatch.setattr(scaffold, "self_check", fake)
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio2"])
    assert rc == 1


def test_1_flavor_path_reports_blocking_findings(tmp_path: Path, monkeypatch, capsys):
    def fake(_targets):
        return [scaffold.Finding("x", "invalid JSON: oops", "", True)]

    monkeypatch.setattr(scaffold, "self_check", fake)
    rc = _run_main("--flavor", "git", "--project-name", "demo", "--cwd", str(tmp_path))
    assert rc == 1


# --- 2: validate VALUE (quote/newline) + coverage-script shape ---
def test_2_py_dep_newline_rejected_with_unchanged_file(tmp_path: Path, capsys):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    before = (tmp_path / "pyproject.toml").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "py-dep", "--req", "foo\nbar"]
    )
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_bytes() == before
    assert "error:" in capsys.readouterr().err


def test_2_py_dep_quote_rejected_with_unchanged_file(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    before = (tmp_path / "pyproject.toml").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "py-dep", "--req", 'foo"bar']
    )
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_bytes() == before


def test_2_rust_version_quote_rejected_with_unchanged_file(tmp_path: Path, capsys):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    before = (tmp_path / "Cargo.toml").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "rust-dep", "--name", "tokio", "--version", '1"2']
    )
    assert rc == 1
    assert (tmp_path / "Cargo.toml").read_bytes() == before


def test_2_rust_version_newline_rejected(tmp_path: Path):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    before = (tmp_path / "Cargo.toml").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "rust-dep", "--name", "tokio", "--version", "1\n2"]
    )
    assert rc == 1
    assert (tmp_path / "Cargo.toml").read_bytes() == before


def test_2_empty_coverage_script_rejected(tmp_path: Path, capsys):
    rc = _run_main(
        "--flavor", "typescript", "--project-name", "demo",
        "--coverage-script", "", "--cwd", str(tmp_path),
    )
    assert rc == 2
    assert "invalid coverage script" in capsys.readouterr().err


def test_2_bad_coverage_script_rejected(tmp_path: Path, capsys):
    rc = _run_main(
        "--flavor", "typescript", "--project-name", "demo",
        "--coverage-script", "bad name!", "--cwd", str(tmp_path),
    )
    assert rc == 2


# --- 3: non-ASCII round trip + trailing newline ---
def test_3_json_preserves_non_ascii_and_newline(tmp_path: Path):
    pkg = {"name": "demo", "description": "café 🎉", "scripts": {"test": "vitest run"}}
    raw = json.dumps(pkg, indent=2, ensure_ascii=False) + "\n"
    (tmp_path / "package.json").write_text(raw, encoding="utf-8")
    scaffold.ensure_ts_dep(tmp_path, "zod", "^3")
    out = (tmp_path / "package.json").read_text(encoding="utf-8")
    assert "café 🎉" in out
    assert "\\u00e9" not in out and "\\ud83c" not in out.lower()
    assert out.endswith("\n")


def test_3_json_keeps_missing_trailing_newline(tmp_path: Path):
    pkg = {"name": "demo", "scripts": {"test": "x"}}
    raw = json.dumps(pkg, indent=2, ensure_ascii=False)  # no trailing newline
    assert not raw.endswith("\n")
    (tmp_path / "package.json").write_text(raw, encoding="utf-8")
    scaffold.ensure_ts_dep(tmp_path, "zod", "^3")
    out = (tmp_path / "package.json").read_text(encoding="utf-8")
    assert not out.endswith("\n")


# --- 4: four thresholds move together ---
def test_4_typescript_sets_all_four_thresholds(tmp_path: Path):
    cfg = (
        "export default { test: { coverage: { thresholds: "
        "{ lines: 80, functions: 80, branches: 80, statements: 80 } } } };\n"
    )
    (tmp_path / "vitest.config.ts").write_text(cfg, encoding="utf-8")
    scaffold.ensure_coverage_threshold(tmp_path, "typescript", 90)
    out = (tmp_path / "vitest.config.ts").read_text(encoding="utf-8")
    for key in ("lines: 90", "functions: 90", "branches: 90", "statements: 90"):
        assert key in out


def test_4_missing_threshold_key_is_added_not_silently_skipped(tmp_path: Path):
    cfg = (
        "export default { test: { coverage: { thresholds: "
        "{ lines: 80, functions: 80 } } } };\n"
    )
    (tmp_path / "vitest.config.ts").write_text(cfg, encoding="utf-8")
    scaffold.ensure_coverage_threshold(tmp_path, "typescript", 90)
    out = (tmp_path / "vitest.config.ts").read_text(encoding="utf-8")
    assert "branches: 90" in out
    assert "statements: 90" in out


def test_4_python_bare_assert_replaced_with_raise(tmp_path: Path):
    # fail_under present as substring but regex cannot match -> explicit raise, not assert
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n# fail_under mentioned but no digits\n', encoding="utf-8"
    )
    try:
        scaffold.ensure_coverage_threshold(tmp_path, "python", 90)
        pytest.fail("should have raised")
    except scaffold.EnsureError as exc:
        assert "no coverage gate" in str(exc)
    except AssertionError:
        raise
    except Exception as exc:  # noqa: BLE001 - must not be bare assert
        assert not isinstance(exc, AssertionError)


# --- 5: rust scoping ---
def test_5_crate_only_in_dev_dependencies_is_added(tmp_path: Path):
    body = (
        '[package]\nname = "demo"\nversion = "0.1.0"\n\n'
        '[dependencies]\nserde = "1"\n\n'
        '[dev-dependencies]\ntokio = "1"\n'
    )
    (tmp_path / "Cargo.toml").write_text(body, encoding="utf-8")
    note = scaffold.ensure_cargo_dep(tmp_path, "tokio", "1")
    assert "added dependency" in note
    out = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    # must appear under [dependencies], not just dev
    dep_span = out.split("[dependencies]")[1].split("[")[0]
    assert 'tokio = "1"' in dep_span


def test_5_present_in_dependencies_reports_unchanged(tmp_path: Path):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    assert "unchanged" in scaffold.ensure_cargo_dep(tmp_path, "serde")


# --- 6: missing section creates, never whole-flavor advice ---
def test_6_missing_section_creates_without_flavor_advice(tmp_path: Path):
    (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    note = scaffold.ensure_ts_dep(tmp_path, "zod")
    assert "added" in note
    data = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert data["devDependencies"]["zod"] == "*"
    # no EnsureError message in this path advises a whole-flavor rerun
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "scripts": "bad"}), encoding="utf-8"
    )
    try:
        scaffold.ensure_ts_script(tmp_path, "lint", "oxlint .")
        pytest.fail("should have raised")
    except scaffold.EnsureError as exc:
        assert "--flavor" not in str(exc)


# --- 7: run1 creates, run2 preserves ts configs ---
def test_7_run1_creates_run2_preserves_tsconfig_and_oxfmtrc(tmp_path: Path):
    rc = _run_main(
        "--flavor", "typescript", "--project-name", "demo", "--cwd", str(tmp_path)
    )
    assert rc == 0
    assert (tmp_path / "tsconfig.json").is_file()
    assert (tmp_path / ".oxfmtrc.json").is_file()
    assert (tmp_path / ".oxlintrc.json").is_file()
    (tmp_path / "tsconfig.json").write_text('{"include": ["index.ts"]}', encoding="utf-8")
    (tmp_path / ".oxfmtrc.json").write_text('{"ignorePatterns": ["prompts/**"]}', encoding="utf-8")
    notes = scaffold.do_typescript(
        tmp_path, "demo", dry_run=False, ts_variant="lib",
        with_coverage=False, threshold=80, update=True,
    )
    assert (tmp_path / "tsconfig.json").read_text(encoding="utf-8") == '{"include": ["index.ts"]}'
    assert (tmp_path / ".oxfmtrc.json").read_text(encoding="utf-8") == '{"ignorePatterns": ["prompts/**"]}'
    joined = "\n".join(notes)
    assert "tsconfig.json" in joined
    assert ".oxfmtrc.json" in joined


# --- 8: name-agnostic detection ---
def test_8_detect_reports_cov_script(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"cov": "vitest run --coverage"}}), encoding="utf-8"
    )
    data = scaffold.detect_project(tmp_path)
    assert data["typescript"]["coverage"] is True
    assert data["typescript"]["coverage_script"] == "cov"


def test_8_detect_reports_plain_test_script(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest run --coverage"}}), encoding="utf-8"
    )
    data = scaffold.detect_project(tmp_path)
    assert data["typescript"]["coverage"] is True
    assert data["typescript"]["coverage_script"] == "test"


def test_8_detect_reads_inline_threshold(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"cov": "vitest run --coverage --coverage.thresholds.lines=85"}}),
        encoding="utf-8",
    )
    data = scaffold.detect_project(tmp_path)
    assert data["typescript"]["threshold"] == 85


def test_8_ci_detection_is_name_agnostic(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"cov": "vitest run --coverage"}}), encoding="utf-8"
    )
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "release.yml").write_text("steps:\n  - run: pnpm run cov\n", encoding="utf-8")
    data = scaffold.detect_project(tmp_path)
    assert data["ci"]["coverage"] is True


# --- 9: coverage-script defaults and threads ---
def test_9_coverage_script_defaults_to_detected(tmp_path: Path, capsys):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"cov": "vitest run --coverage"}}), encoding="utf-8"
    )
    rc = _run_main(
        "--flavor", "ci", "--ci-variant", "node", "--with-coverage",
        "--cwd", str(tmp_path),
    )
    assert rc == 0
    capsys.readouterr()
    assert (tmp_path / ".github" / "workflows" / "release.yml").exists()
    yml = (tmp_path / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "pnpm run cov" in yml


def test_9_explicit_coverage_script_threads_to_ci(tmp_path: Path):
    rc = _run_main(
        "--flavor", "ci", "--ci-variant", "node", "--with-coverage",
        "--coverage-script", "my-cov", "--cwd", str(tmp_path),
    )
    assert rc == 0
    yml = (tmp_path / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "pnpm run my-cov" in yml


def test_9_all_threads_coverage_script_through_do_ci(tmp_path: Path):
    rc = _run_main(
        "--flavor", "all", "--project-name", "demo", "--with-coverage",
        "--coverage-script", "my-cov", "--cwd", str(tmp_path),
    )
    assert rc == 0
    yml = (tmp_path / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "pnpm run my-cov" in yml


# --- 10: boundary contract docs + CLI self-description ---
def test_10_skill_states_boundary_contract():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "Run 1 (field absent)" in text
    assert "byte-identical" in text
    assert "Run 2" in text
    assert "project owns the file" in text
    assert "replace / update one field / untouched" in text
    assert "--update" in text and "preserves" in text
    assert "ensure <op>" in text
    assert "--coverage-script" in text


def test_10_cli_is_self_describing():
    assert "ensure" in (scaffold.__doc__ or "")
    # argparse epilog carries the boundary so --help is self-describing
    import argparse as _ap  # noqa: F401
    src = SCRIPT.read_text(encoding="utf-8")
    assert "epilog" in src
    assert "ensure <op>" in src


# --- 11: changelog copies byte-equal (mirrors sync guard) ---
def test_11_changelog_copies_byte_equal():
    repo_root = SKILL_DIR.parent.parent
    for name in ("changelog-unreleased.py", "changelog-gate.py"):
        assert (SKILL_DIR / "scripts" / name).read_bytes() == (
            repo_root / "scripts" / name
        ).read_bytes(), name


# --- 12: NEXT hints runnable ---
def test_12_next_hints_are_runnable():
    src = SCRIPT.read_text(encoding="utf-8")
    assert "uv run $SKILL_DIR/scripts/scaffold.py ensure py-dep" in src
    assert "uv run $SKILL_DIR/scripts/scaffold.py ensure rust-dep" in src
    assert "uv run $SKILL_DIR/scripts/scaffold.py ensure ts-dep" in src
    assert "per-field edits via `scaffold.py ensure" not in src


# --- r2 P1-A: do_ci honors --update (release.yml preserved, not clobbered) ---
def test_r2_ci_update_preserves_release_yml(tmp_path: Path):
    assert (
        _run_main(
            "--flavor", "ci", "--ci-variant", "node", "--project-name", "demo",
            "--cwd", str(tmp_path),
        )
        == 0
    )
    rel = tmp_path / ".github" / "workflows" / "release.yml"
    rel.write_text(
        rel.read_text(encoding="utf-8") + "\n# CUSTOM MARKER\n", encoding="utf-8"
    )
    assert (
        _run_main(
            "--flavor", "ci", "--ci-variant", "node", "--update", "--cwd", str(tmp_path)
        )
        == 0
    )
    assert "# CUSTOM MARKER" in rel.read_text(encoding="utf-8")


def test_r2_do_ci_update_returns_preserve_note(tmp_path: Path):
    assert (
        _run_main(
            "--flavor", "ci", "--ci-variant", "node", "--project-name", "demo",
            "--cwd", str(tmp_path),
        )
        == 0
    )
    rel = tmp_path / ".github" / "workflows" / "release.yml"
    rel.write_text(
        rel.read_text(encoding="utf-8") + "\n# CUSTOM MARKER\n", encoding="utf-8"
    )
    notes = scaffold.do_ci(tmp_path, False, "node", False, 80, update=True)
    assert any("release.yml" in note for note in notes)
    assert "# CUSTOM MARKER" in rel.read_text(encoding="utf-8")


def test_r2_all_update_preserves_release_yml(tmp_path: Path):
    assert _run_main("--flavor", "all", "--project-name", "demo", "--cwd", str(tmp_path)) == 0
    rel = tmp_path / ".github" / "workflows" / "release.yml"
    rel.write_text(
        rel.read_text(encoding="utf-8") + "\n# CUSTOM MARKER\n", encoding="utf-8"
    )
    assert (
        _run_main("--flavor", "all", "--project-name", "demo", "--update", "--cwd", str(tmp_path))
        == 0
    )
    assert "# CUSTOM MARKER" in rel.read_text(encoding="utf-8")


# --- r2 P1-B: self_check parses .toml/.ts; ensure refuses corrupt files ---
def test_r2_self_check_flags_invalid_toml(tmp_path: Path):
    bad = tmp_path / "Cargo.toml"
    bad.write_text("INVALID [[[\n", encoding="utf-8")
    findings = scaffold.self_check([bad])
    assert any("invalid TOML" in f.detail and f.blocking for f in findings)


def test_r2_self_check_flags_unbalanced_ts(tmp_path: Path):
    bad = tmp_path / "vitest.config.ts"
    bad.write_text("INVALID(((\n", encoding="utf-8")
    findings = scaffold.self_check([bad])
    assert any("unbalanced" in f.detail and f.blocking for f in findings)


def test_r2_self_check_accepts_valid_toml_and_ts(tmp_path: Path):
    good_toml = tmp_path / "Cargo.toml"
    good_toml.write_text(
        '[package]\nname = "demo"\nversion = "0.1.0"\n\n[dependencies]\n', encoding="utf-8"
    )
    good_ts = tmp_path / "index.ts"
    good_ts.write_text(
        'export const greeting: string = `hello ${"world"}`;\n', encoding="utf-8"
    )
    assert not [f for f in scaffold.self_check([good_toml, good_ts]) if f.blocking]


def test_r2_ensure_rust_dep_refuses_invalid_toml_unchanged(tmp_path: Path):
    bad = '[package\nname = "demo"\n\n[dependencies]\nserde = "1"\n'
    (tmp_path / "Cargo.toml").write_text(bad, encoding="utf-8")
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio"])
    assert rc == 1
    assert (tmp_path / "Cargo.toml").read_text(encoding="utf-8") == bad


def test_r2_ensure_py_dep_refuses_invalid_toml_unchanged(tmp_path: Path):
    bad = '[project\nname = "demo"\ndependencies = []\n'
    (tmp_path / "pyproject.toml").write_text(bad, encoding="utf-8")
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "py-dep", "--req", "httpx>=0.27"])
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == bad


def test_r2_ensure_threshold_refuses_invalid_ts_unchanged(tmp_path: Path):
    bad = (
        "export default { test: { coverage: { thresholds: "
        "{ lines: 80, functions: 80 } } } ;\n((("
    )
    (tmp_path / "vitest.config.ts").write_text(bad, encoding="utf-8")
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "typescript", "--value", "90"]
    )
    assert rc == 1
    assert (tmp_path / "vitest.config.ts").read_text(encoding="utf-8") == bad


# --- r2 P2: JSON normalization is disclosed, not silent ---
def test_r2_ensure_help_discloses_json_normalization(capsys):
    with pytest.raises(SystemExit) as excinfo:
        scaffold.ensure_main(["--help"])
    assert excinfo.value.code == 0
    assert "2-space JSON" in capsys.readouterr().out


def test_r2_skill_discloses_json_normalization():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "2-space JSON" in text


# --- r3: prior-round P1/P2 (falsifiable: revert fix -> fail) ---
def test_r3_cargo_trailing_comment_no_duplicate(tmp_path: Path):
    body = '[package]\nname = "demo"\nversion = "0.1.0"\n\n[dependencies] # comment\nserde = "1"\n'
    (tmp_path / "Cargo.toml").write_text(body, encoding="utf-8")
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "tokio"])
    assert rc == 0
    out = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    import tomllib as _toml

    _toml.loads(out)
    assert out.count("[dependencies]") == 1
    assert 'tokio = "*"' in out.split("[dependencies]")[1].split("[")[0]


def test_r3_cargo_dev_comment_bleed_adds_to_dependencies(tmp_path: Path):
    body = (
        '[package]\nname = "demo"\nversion = "0.1.0"\n\n'
        '[dependencies]\nserde = "1"\n\n'
        '[dev-dependencies] # comment\ntokio = "1"\n'
    )
    (tmp_path / "Cargo.toml").write_text(body, encoding="utf-8")
    note = scaffold.ensure_cargo_dep(tmp_path, "tokio", "1")
    assert "added dependency" in note
    out = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    dep_span = out.split("[dependencies]")[1].split("[")[0]
    assert 'tokio = "1"' in dep_span


def test_r3_python_comment_only_fail_under_refuses(tmp_path: Path):
    bad = '[project]\nname = "demo"\n# fail_under = 80\n'
    (tmp_path / "pyproject.toml").write_text(bad, encoding="utf-8")
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "python", "--value", "90"]
    )
    assert rc == 1
    assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == bad


def test_r3_typescript_comment_only_thresholds_refuses(tmp_path: Path):
    bad = "// thresholds: { lines: 80 }\nexport default {};\n"
    (tmp_path / "vitest.config.ts").write_text(bad, encoding="utf-8")
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "typescript", "--value", "90"]
    )
    assert rc == 1
    assert (tmp_path / "vitest.config.ts").read_text(encoding="utf-8") == bad


def test_r3_ts_newline_version_refused_unchanged(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        '{"name": "demo", "devDependencies": {}, "scripts": {}}', encoding="utf-8"
    )
    before = (tmp_path / "package.json").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "ts-dep", "--name", "zod", "--version", "a\nb"]
    )
    assert rc == 1
    assert (tmp_path / "package.json").read_bytes() == before


def test_r3_ts_newline_script_name_refused_unchanged(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        '{"name": "demo", "devDependencies": {}, "scripts": {}}', encoding="utf-8"
    )
    before = (tmp_path / "package.json").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "ts-script", "--name", "bad\nname", "--cmd", "echo hi"]
    )
    assert rc == 1
    assert (tmp_path / "package.json").read_bytes() == before


def test_r3_git_skill_ownership_table_lists_ts_configs():
    text = (SKILL_DIR / "subskills" / "git-scaffolding" / "SKILL.md").read_text(encoding="utf-8")
    assert "tsconfig.json" in text
    assert ".oxlintrc.json" in text
    assert ".oxfmtrc.json" in text


# --- r4: round-3 review (string-aware python gate, byte-based write gate, shared name shape) ---
def test_r4_python_string_fail_under_untouched(tmp_path: Path):
    body = (
        '[project]\ndescription = "fail_under = 80 stays in docs"\n\n'
        "[tool.coverage.report]\nfail_under = 80\n"
    )
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "python", "--value", "90"]
    )
    assert rc == 0
    out = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'description = "fail_under = 80 stays in docs"' in out
    assert "fail_under = 90" in out


def test_r4_python_other_section_fail_under_untouched(tmp_path: Path):
    body = (
        '[project]\nname = "demo"\n\n'
        "[tool.coverage.report]\nfail_under = 80\n\n"
        "[tool.other]\nfail_under = 70\n"
    )
    (tmp_path / "pyproject.toml").write_text(body, encoding="utf-8")
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "coverage-threshold", "--flavor", "python", "--value", "90"]
    )
    assert rc == 0
    out = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.other]\nfail_under = 70" in out


def test_r4_ensure_main_self_check_runs_for_unchanged_named_crate(
    tmp_path: Path, monkeypatch
):
    (tmp_path / "Cargo.toml").write_text(CARGO, encoding="utf-8")
    seen: list = []
    orig = scaffold.self_check

    def spy(targets):
        seen.extend(targets)
        return orig(targets)

    monkeypatch.setattr(scaffold, "self_check", spy)
    rc = scaffold.ensure_main(["--cwd", str(tmp_path), "rust-dep", "--name", "unchanged"])
    assert rc == 0
    assert any(str(p).endswith("Cargo.toml") for p in seen)


def test_r4_ts_script_bad_name_refused_unchanged(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        '{"name": "demo", "scripts": {}}', encoding="utf-8"
    )
    before = (tmp_path / "package.json").read_bytes()
    rc = scaffold.ensure_main(
        ["--cwd", str(tmp_path), "ts-script", "--name", "bad name!", "--cmd", "vitest run --coverage"]
    )
    assert rc == 1
    assert (tmp_path / "package.json").read_bytes() == before


def test_r4_detect_ignores_invalid_coverage_script_name(tmp_path: Path):
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"bad name!": "vitest run --coverage"}}), encoding="utf-8"
    )
    data = scaffold.detect_project(tmp_path)
    assert data["typescript"]["coverage_script"] is None
