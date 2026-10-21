"""Tests for the TypeScript scaffold flavor — templates, variants, detect, CI wiring."""

import importlib.util
import json
import sys
from pathlib import Path

import yaml

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


def test_dev_dependencies_stay_inside_reviewed_majors():
    """`>=7` accepts v8, v9 and every major after — a generated repo could resolve a major nobody
    reviewed, with no change on its side, and the failure surfaces as a red gate. `^7` keeps the
    reviewed major while the committed lockfile pins the bytes (#26)."""
    pkg = json.loads(scaffold.build_package_json("demo", "lib", with_coverage=True))
    specs: dict[str, str] = pkg["devDependencies"]
    assert specs["oxfmt"] == scaffold.OXFMT_VERSION, "the byte contract stays exact"
    for name, spec in specs.items():
        if name == "oxfmt":
            continue  # the one exact pin, asserted above
        assert ">=" not in spec, f"{name}: {spec!r} accepts every later major"
        assert spec.startswith("^"), f"{name}: {spec!r} is not a caret range"
    assert specs["conventional-changelog-conventionalcommits"] == "^9", (
        "the writer constraint is a range, not a second bound"
    )


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
        "audit": "pnpm audit --audit-level high --registry https://registry.npmjs.org/",
        "verify": "pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test",
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


def _verify_runs(yml: str) -> list[str]:
    """The run steps of a workflow's `verify` job, in order."""
    doc = yaml.safe_load(yml)
    assert isinstance(doc, dict)
    return [step["run"] for step in doc["jobs"]["verify"]["steps"] if "run" in step]


def test_verify_script_is_the_whole_gate_in_ci_order():
    """One command, one exit code: `verify` is the chain CI runs, not a second spelling."""
    pkg = json.loads(scaffold.build_package_json("demo", "lib", with_coverage=False))
    verify = pkg["scripts"]["verify"]
    assert verify.split(" && ") == [
        "pnpm run lint",
        "pnpm run format",
        "pnpm run typecheck",
        "pnpm test",
    ]
    assert _verify_runs(scaffold.render_ci_release("node", False, 80))[-1] == "pnpm run verify"


def test_coverage_verify_ends_on_the_project_coverage_script():
    """Coverage projects gate on their own script name, and it stays the last step."""
    pkg = json.loads(scaffold.build_package_json("demo", "lib", with_coverage=True))
    assert pkg["scripts"]["verify"] == (
        "pnpm run lint && pnpm run format && pnpm run typecheck && pnpm run coverage"
    )
    aliased = json.loads(scaffold.build_package_json("demo", "lib", True, "test:coverage"))
    assert aliased["scripts"]["verify"].endswith("&& pnpm run test:coverage")
    assert (
        _verify_runs(scaffold.render_ci_release("node", True, 80, "test:coverage"))[-1]
        == "pnpm run verify"
    )


def test_agents_runtime_pointer_cites_verify(tmp_path):
    """The agent-facing pointer names one command, not the four-step chain."""
    rc = _run_main(
        "--flavor",
        "typescript",
        "--ts-variant",
        "lib",
        "--project-name",
        "demo",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    text = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    runtime = text.split("### Runtime", 1)[1]
    assert "`pnpm run verify`" in runtime
    assert "oxlint/oxfmt/tsc/vitest" not in runtime


def test_existing_manifest_adopts_verify_with_one_script(tmp_path):
    """A consumer repo adds the script and nothing else; existing entries keep their values."""
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "scripts": {"test": "vitest run"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    rc = _run_main(
        "ensure",
        "--cwd",
        str(tmp_path),
        "ts-script",
        "--name",
        "verify",
        "--cmd",
        "pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test",
    )
    assert rc == 0
    pkg = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["verify"] == (
        "pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test"
    )
    assert pkg["scripts"]["test"] == "vitest run"


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
        "pnpm-workspace.yaml",
        "index.ts",
        "cli.ts",
        "index.test.ts",
        "ci.yml",
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
    assert _verify_runs(release_yml) == [
        "pnpm install",
        "pnpm run audit",
        "pnpm run verify",
    ]
    assert "pnpm audit --audit-level" not in release_yml, "CI spells the audit command twice"
    assert "npm ci" not in release_yml


def test_node_ci_does_not_fork_on_coverage():
    """The coverage variant lives in the manifest's `verify` script, so CI bytes match."""
    plain = scaffold.render_ci_release("node", with_coverage=False, threshold=80)
    covered = scaffold.render_ci_release("node", with_coverage=True, threshold=80)
    assert plain == covered
    assert "- run: pnpm run verify" in covered


def test_audit_script_pins_the_public_registry():
    """A mirror without the audit endpoint answers ERR_PNPM_AUDIT_ENDPOINT_NOT_EXISTS (#288)."""
    for coverage in (False, True):
        pkg = json.loads(scaffold.build_package_json("demo", "lib", coverage))
        assert pkg["scripts"]["audit"] == (
            "pnpm audit --audit-level high --registry https://registry.npmjs.org/"
        )


def test_typescript_emits_a_pr_workflow_with_the_release_gate(tmp_path):
    """The PR workflow must run the release verify block, skip drafts, and cancel in flight."""
    rc = _run_main(
        "--flavor",
        "typescript",
        "--ts-variant",
        "lib",
        "--project-name",
        "demo",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    ci = (tmp_path / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    doc = yaml.safe_load(ci)
    triggers = doc.get("on") or doc.get(True)
    assert "synchronize" in triggers["pull_request"]["types"]
    assert "ready_for_review" in triggers["pull_request"]["types"]
    assert triggers["push"]["branches"] == ["main"]
    assert doc["concurrency"]["cancel-in-progress"] is True
    assert doc["permissions"] == {"contents": "read"}
    assert doc["jobs"]["verify"]["if"] == (
        "github.event_name == 'push' || github.event.pull_request.draft == false"
    )
    assert _verify_runs(ci) == _verify_runs(
        scaffold.render_ci_release("node", with_coverage=True, threshold=80)
    )


def test_existing_manifest_adopts_audit_with_one_script(tmp_path):
    """A consumer repo adds the audit script; CI regenerates with no hand edit (#288)."""
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "scripts": {"verify": "pnpm test"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    rc = _run_main(
        "ensure",
        "--cwd",
        str(tmp_path),
        "ts-script",
        "--name",
        "audit",
        "--cmd",
        "pnpm audit --audit-level high --registry https://registry.npmjs.org/",
    )
    assert rc == 0
    pkg = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["audit"] == (
        "pnpm audit --audit-level high --registry https://registry.npmjs.org/"
    )
    assert pkg["scripts"]["verify"] == "pnpm test"


def test_pnpm_workspace_allows_one_build_and_suppresses_one_advisory(tmp_path):
    """A scaffolded repo must install and audit clean, without a blanket suppression (#288)."""
    rc = _run_main(
        "--flavor",
        "typescript",
        "--ts-variant",
        "lib",
        "--project-name",
        "demo",
        "--cwd",
        str(tmp_path),
    )
    assert rc == 0
    text = (tmp_path / "pnpm-workspace.yaml").read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    assert doc["allowBuilds"] == {"esbuild": True}
    assert doc["auditConfig"]["ignoreGhsas"] == ["GHSA-vfj7-8cjw-p6xm"], (
        "the suppression must stay singular: any other high advisory still gates"
    )
    assert "Removal condition" in text
    pkg = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))
    audit = pkg["scripts"]["audit"]
    assert "--prod" not in audit, "dev advisories must stay visible"
    assert "--ignore-registry-errors" not in audit


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
