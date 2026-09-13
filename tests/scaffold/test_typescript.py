"""Tests for the TypeScript scaffold flavor — templates, variants, detect, CI wiring."""

import importlib.util
import json
import sys
from pathlib import Path

# Add scaffold scripts dir for scaffold.py import (single-file script, no package)
SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold_mod", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["scaffold_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load_scaffold()


def _run_main(*argv: str) -> int:
    old = sys.argv
    sys.argv = ["scaffold.py", *argv]
    try:
        return scaffold.main()
    finally:
        sys.argv = old


# --- package.json builder -------------------------------------------------


def test_lib_variant_fields():
    pkg = json.loads(scaffold.build_package_json("demo-lib", "lib", False))
    assert pkg["name"] == "demo-lib"
    assert pkg["type"] == "module"
    assert pkg["packageManager"] == "pnpm@12.4.1"
    assert pkg["engines"] == {"node": ">=26"}
    assert pkg["main"] == "./src/index.ts"
    assert pkg["exports"] == {".": "./src/index.ts"}
    assert "bin" not in pkg and "pi" not in pkg
    assert pkg["scripts"] == {
        "lint": "oxlint .",
        "format": "oxfmt --check .",
        "format:fix": "oxfmt .",
        "typecheck": "tsc --noEmit",
        "test": "vitest run",
    }
    assert "coverage" not in pkg["scripts"]
    assert "@vitest/coverage-v8" not in pkg["devDependencies"]


def test_cli_variant_bin_and_name_normalization():
    pkg = json.loads(scaffold.build_package_json("demo_cli", "cli", False))
    assert pkg["name"] == "demo-cli"
    assert pkg["bin"] == {"demo-cli": "./src/cli.ts"}
    assert "main" not in pkg


def test_pi_extension_manifest():
    pkg = json.loads(scaffold.build_package_json("demo-pi", "pi-extension", False))
    assert pkg["pi"] == {"extensions": ["./src/index.ts"]}
    assert "bin" not in pkg


def test_coverage_wiring():
    pkg = json.loads(scaffold.build_package_json("demo", "lib", True))
    assert pkg["scripts"]["coverage"] == "vitest run --coverage"
    assert "@vitest/coverage-v8" in pkg["devDependencies"]
    cfg = scaffold.render_template("typescript/vitest.config.ts.j2", threshold=90)
    assert "lines: 90" in cfg and "functions: 90" in cfg


def test_tsconfig_base():
    tsconfig = json.loads(scaffold.build_tsconfig())
    opts = tsconfig["compilerOptions"]
    assert opts["strict"] is True
    assert opts["module"] == "NodeNext"
    assert opts["target"] == "ES2022"
    assert opts["types"] == ["node"]  # explicit: pnpm symlinks defeat auto-inclusion
    assert tsconfig["include"] == ["src", "tests"]  # tests/ layout per branch-worktree-pr


def test_ox_configs_are_valid_json():
    """Ox toolchain configs ship as templates (biome.json was dropped with biome)."""
    lint = json.loads(scaffold.OXLINT_JSON)
    assert lint["rules"]["harness/no-comments"] == "error"
    assert lint["jsPlugins"] == ["./scripts/oxlint-plugin-comment-gate.js"]
    fmt = json.loads(scaffold.OXFMT_JSON)
    assert fmt["$schema"].endswith("oxfmt/configuration_schema.json")


# --- generator + detect round-trip ----------------------------------------


def test_dry_run_lists_expected_files(tmp_path, capsys):
    rc = _run_main(
        "--flavor",
        "typescript",
        "--ts-variant",
        "cli",
        "--project-name",
        "demo",
        "--dry-run",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    out = capsys.readouterr().out
    for name in (
        "package.json",
        "tsconfig.json",
        ".oxlintrc.json",
        ".oxfmtrc.json",
        ".nvmrc",
        "index.ts",
        "cli.ts",
        "index.test.ts",
    ):
        assert name in out


def test_generate_then_detect(tmp_path):
    rc = _run_main(
        "--flavor",
        "typescript",
        "--ts-variant",
        "pi-extension",
        "--project-name",
        "demo",
        "--with-coverage",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    assert (tmp_path / "vitest.config.ts").exists()
    data = scaffold.detect_project(tmp_path)
    assert data["inferred_shape"] == "node"
    ts = data["typescript"]
    assert ts["present"] is True
    assert ts["variant"] == "pi-extension"
    assert ts["coverage"] is True
    assert ts["threshold"] == 80
    assert data["verify_gates"] == {
        "formatter": True,
        "linter": True,
        "typecheck": True,
        "tests": True,
    }


# --- shared-spine guards ----------------------------------------------------


def test_node_ci_variant_is_pnpm_on_the_declared_runtime():
    release_yml = scaffold.render_ci_release(
        "node", with_coverage=False, threshold=scaffold.DEFAULT_COVERAGE_THRESHOLD
    )
    assert f"node-version: {scaffold.NODE_VERSION_NUM}" in release_yml
    assert "node-version: 24" not in release_yml
    assert "pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test" in release_yml
    assert "npm ci" not in release_yml


def test_node_coverage_variant_runs_the_coverage_script():
    """Regression: the coverage cell was a no-op `.replace()` and ran `pnpm test` un-gated."""
    plain = scaffold.render_ci_release("node", with_coverage=False, threshold=80)
    covered = scaffold.render_ci_release("node", with_coverage=True, threshold=80)
    assert "- run: pnpm run coverage" in covered
    assert "pnpm run coverage" not in plain
    assert covered != plain


def test_python_flavor_untouched(tmp_path, capsys):
    """Q3c guard: python bytes keep uv wiring after the TS addition."""
    rc = _run_main(
        "--flavor",
        "python",
        "--project-name",
        "demo",
        "--dry-run",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "pyproject.toml" in out and ".python-version" in out
    pyproj = scaffold.build_pyproject("demo", False, 80)
    assert 'requires-python = ">=3.14"' in pyproj
    assert "basedpyright" in pyproj
