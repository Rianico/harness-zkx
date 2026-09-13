"""Tests for the scaffold's self-reporting surface — `--check`/`--summary`/`--json`, the
self-check, and the ownership fixes behind them.

Each block locks down a defect that used to be invisible:

- `--update --dry-run` reprinted unified diffs a caller had to grep; `--check` answers the same
  question in one line per file plus an exit code.
- Scaffold vendored the sibling `gh-router` skill into every target repo, so the copy drifted
  from the harness original — the defect was the projection, not the completeness of the copy.
- `patch_releaserc_lockfile` was only reachable through the TypeScript flavor, so a pnpm repo
  refreshed with `--update` silently regained `package-lock.json` in its release assets.
- `do_typescript` wrote `src/index.ts` / `tests/index.test.ts` unconditionally, so
  `--update --flavor typescript` would have replaced a project's own code with a skeleton.
- `--update` reported "hand-merge the 'Before PR' line" while the actually-missing sections
  (`Reporting Issues`, `Pull Requests`) went unnamed.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import stat
import sys

import pytest

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
TEMPLATES = SKILL_DIR / "templates"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_self_report", SCRIPT)

STALE_HOOK = "stale-hook\n"


@pytest.fixture(autouse=True)
def _fresh_plan():
    """A plan is per-run state: never let one test's entries leak into the next."""
    scaffold.REPORT.start(scaffold.VERBOSE, pathlib.Path("/"))
    yield


def _seed_repo(cwd: pathlib.Path) -> None:
    (cwd / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (cwd / ".githooks").mkdir(parents=True, exist_ok=True)
    (cwd / "CHANGELOG.md").write_text("# Changelog\n\n## [1.0.0] - 2026-01-01\n", encoding="utf-8")
    (cwd / ".githooks" / "pre-push").write_text(STALE_HOOK, encoding="utf-8")


def _run_main(*argv: str) -> int:
    old = sys.argv
    sys.argv = ["scaffold.py", *argv]
    try:
        return scaffold.main()
    finally:
        sys.argv = old


# --- --check: one line per file, exit code as the verdict -----------------------


def test_check_is_clean_after_a_real_git_run(tmp_path, capsys):
    _seed_repo(tmp_path)
    assert _run_main("--flavor", "git", "--project-name", "demo", "--cwd", str(tmp_path)) == 0
    capsys.readouterr()

    assert _run_main("--check", "--cwd", str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "drift 0" in out


def test_check_reports_drift_and_fails_the_run(tmp_path, capsys):
    _seed_repo(tmp_path)

    assert _run_main("--check", "--cwd", str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "stale      .githooks/pre-push" in out
    assert "missing    .github/pull_request_template.md" in out
    assert "drift " in out


def test_check_writes_nothing(tmp_path):
    _seed_repo(tmp_path)
    _run_main("--check", "--cwd", str(tmp_path))

    assert (tmp_path / ".githooks" / "pre-push").read_text(encoding="utf-8") == STALE_HOOK
    assert not (tmp_path / ".releaserc.json").exists()


def test_check_without_flavor_is_not_a_usage_error(tmp_path, capsys):
    _seed_repo(tmp_path)

    assert _run_main("--check", "--cwd", str(tmp_path)) in (0, 1)
    assert "usage:" not in capsys.readouterr().err


# --- --summary / --json: the plan as data, not as a diff dump -------------------


def test_summary_drops_the_diff_payload(tmp_path, capsys):
    _seed_repo(tmp_path)

    _run_main("--update", "--dry-run", "--summary", "--cwd", str(tmp_path))
    out = capsys.readouterr().out

    assert "stale      .githooks/pre-push" in out
    assert "@@" not in out  # no unified diff a caller would have to parse
    assert "\ndiff" not in out


def test_json_plan_is_machine_readable(tmp_path, capsys):
    _seed_repo(tmp_path)

    _run_main("--update", "--dry-run", "--json", "--cwd", str(tmp_path))
    plan = json.loads(capsys.readouterr().out)

    assert plan["dry_run"] is True and plan["update"] is True
    assert plan["drift"] is True
    kinds = {(entry["path"], entry["kind"]) for entry in plan["entries"]}
    assert (".githooks/pre-push", "stale") in kinds
    assert (".github/pull_request_template.md", "missing") in kinds
    assert all({"kind", "area", "detail", "remedy"} <= set(f) for f in plan["findings"])


def test_report_start_resets_the_plan(tmp_path):
    scaffold.REPORT.start(scaffold.VERBOSE, tmp_path)
    scaffold.REPORT.record(tmp_path / "a.txt", scaffold.STALE)
    scaffold.REPORT.start(scaffold.VERBOSE, tmp_path)

    assert scaffold.REPORT.entries == []


# --- self-check: what a run writes must parse, run and resolve ------------------


def test_self_check_flags_broken_bytes_as_blocking(tmp_path):
    bad_py = tmp_path / "broken.py"
    bad_py.write_text("def f(:\n", encoding="utf-8")
    bad_json = tmp_path / "broken.json"
    bad_json.write_text("{not json", encoding="utf-8")
    bare_hook = tmp_path / "pre-push"
    bare_hook.write_text("#!/bin/sh\ntrue\n", encoding="utf-8")
    bare_hook.chmod(stat.S_IRUSR | stat.S_IWUSR)

    findings = scaffold.self_check([bad_py, bad_json, bare_hook])
    blocking = [f for f in findings if f.blocking]
    details = " ".join(f"{f.area}: {f.detail}" for f in blocking)

    assert "python syntax error" in details
    assert "invalid JSON" in details
    assert "not executable" in details


def test_self_check_flags_a_shell_syntax_error(tmp_path):
    script = tmp_path / "go.sh"
    script.write_text("if true; then\n", encoding="utf-8")
    script.chmod(0o755)

    findings = scaffold.self_check([script])

    assert any("shell syntax error" in f.detail for f in findings)


def test_self_check_reports_dangling_reference_without_failing(tmp_path):
    hook = tmp_path / ".githooks" / "pre-push"
    hook.parent.mkdir(parents=True)
    hook.write_text("#!/bin/sh\npython3 scripts/ghost.py\n", encoding="utf-8")
    hook.chmod(0o755)
    scaffold.REPORT.start(scaffold.VERBOSE, tmp_path)

    findings = scaffold.self_check([hook])

    assert [f.detail for f in findings] == ["references absent path 'scripts/ghost.py'"]
    assert not any(f.blocking for f in findings)


def test_self_check_resolves_router_references_under_subskills(tmp_path):
    root = tmp_path / "skills" / "gh-router"
    (root / "subskills" / "pr-land" / "scripts").mkdir(parents=True)
    (root / "subskills" / "pr-land" / "scripts" / "pr.sh").write_text(
        "#!/bin/sh\n", encoding="utf-8"
    )
    (root / "SKILL.md").write_text("| land | `pr-land/scripts/pr.sh` |\n", encoding="utf-8")

    assert scaffold.self_check([root / "SKILL.md"]) == []


def test_pnpm_repo_gets_the_pnpm_lockfile_asset(tmp_path):
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

    scaffold.do_git(tmp_path, "demo", dry_run=False)
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")

    assert '"pnpm-lock.yaml"' in releaserc
    assert '"package-lock.json"' not in releaserc


def test_check_is_clean_for_a_pnpm_repo(tmp_path, capsys):
    """Regression: the plan compared the raw template, so a pnpm repo reported drift forever."""
    _seed_repo(tmp_path)
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    assert _run_main("--flavor", "git", "--project-name", "demo", "--cwd", str(tmp_path)) == 0
    capsys.readouterr()

    assert _run_main("--check", "--cwd", str(tmp_path)) == 0
    assert "drift 0" in capsys.readouterr().out
    assert '"pnpm-lock.yaml"' in (tmp_path / ".releaserc.json").read_text(encoding="utf-8")


def test_npm_repo_keeps_the_template_asset_bytes(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)

    written = (tmp_path / ".releaserc.json").read_bytes()
    assert written == (TEMPLATES / "git/.releaserc.json").read_bytes()


def test_declares_pnpm_probes_three_signals(tmp_path):
    assert scaffold._declares_pnpm(tmp_path) is False

    (tmp_path / "pnpm-workspace.yaml").write_text("packages: []\n", encoding="utf-8")
    assert scaffold._declares_pnpm(tmp_path) is True

    (tmp_path / "pnpm-workspace.yaml").unlink()
    (tmp_path / "package.json").write_text('{"packageManager": "pnpm@12.0.0"}', encoding="utf-8")
    assert scaffold._declares_pnpm(tmp_path) is True


def test_update_preserves_hand_grown_sources(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    mine = {
        "src/index.ts": "export const realExtension = 1;\n",
        "tests/index.test.ts": "import './index.js';\n",
        "vitest.config.ts": "export default { test: { coverage: { lines: 95 } } };\n",
    }
    for rel, body in mine.items():
        (tmp_path / rel).write_text(body, encoding="utf-8")

    notes = scaffold.do_typescript(
        tmp_path,
        "demo",
        dry_run=False,
        ts_variant="pi-extension",
        with_coverage=True,
        threshold=80,
        update=True,
    )

    for rel, body in mine.items():
        assert (tmp_path / rel).read_text(encoding="utf-8") == body, rel
    assert any("src/index.ts" in note for note in notes)
    assert any("vitest.config.ts" in note for note in notes)


def test_greenfield_typescript_run_still_ships_the_skeleton(tmp_path):
    scaffold.do_typescript(
        tmp_path,
        "demo",
        dry_run=False,
        ts_variant="pi-extension",
        with_coverage=False,
        threshold=80,
    )

    assert (tmp_path / "src" / "index.ts").read_text(encoding="utf-8") == (
        scaffold.render_template("typescript/src/index.ts.j2", project_name="demo")
    )
    assert (tmp_path / "tests" / "index.test.ts").read_text(encoding="utf-8") == (
        scaffold.INDEX_TEST_TS
    )


# --- mixed files: name the gap, then merge it only when asked ------------------


TEMPLATE_MD = (
    "# Contributing to demo\n\n"
    "## Commits\n\nkeep\n\n"
    "## Reporting Issues\n\ntemplate body\n\n"
    "## Before PR\n\n`pnpm test`\n\n"
    "## Pull Requests\n\nsquash\n"
)


def test_missing_sections_lists_template_headings_in_order():
    existing = "# Contributing to demo\n\n## Commits\n\nkeep\n\n## Pull Requests\n\nsquash\n"

    assert scaffold.missing_sections(existing, TEMPLATE_MD) == ["Reporting Issues", "Before PR"]


def test_merge_inserts_missing_sections_and_keeps_existing_bytes(tmp_path):
    path = tmp_path / "CONTRIBUTING.md"
    existing = "# Contributing to demo\n\n## Commits\n\nkeep\n\n## Pull Requests\n\nsquash\n"
    path.write_text(existing, encoding="utf-8")

    assert scaffold.merge_missing_sections(path, TEMPLATE_MD, dry_run=False) is True
    merged = path.read_text(encoding="utf-8")

    assert "## Reporting Issues" in merged and "## Before PR" in merged
    assert merged.index("## Reporting Issues") < merged.index("## Before PR")
    assert merged.index("## Before PR") < merged.index("## Pull Requests")
    for original_line in ("## Commits", "keep", "squash"):
        assert original_line in merged


def test_merge_dry_run_writes_nothing(tmp_path):
    path = tmp_path / "CONTRIBUTING.md"
    existing = "# Contributing to demo\n\n## Commits\n\nkeep\n"
    path.write_text(existing, encoding="utf-8")

    assert scaffold.merge_missing_sections(path, TEMPLATE_MD, dry_run=True) is False
    assert path.read_text(encoding="utf-8") == existing


def test_write_contributing_names_the_missing_sections(tmp_path):
    (tmp_path / "CONTRIBUTING.md").write_text(
        "# Contributing to demo\n\n## Commits\n\nkeep\n", encoding="utf-8"
    )

    note = scaffold.write_contributing(
        tmp_path, TEMPLATE_MD, dry_run=False, warn_mixed="mixed", update=True
    )

    assert note is not None
    assert "missing template sections: Reporting Issues, Before PR, Pull Requests" in note
    assert (tmp_path / "CONTRIBUTING.md").read_text(encoding="utf-8").endswith("keep\n")


def test_write_contributing_merges_when_asked(tmp_path):
    path = tmp_path / "CONTRIBUTING.md"
    path.write_text("# Contributing to demo\n\n## Commits\n\nkeep\n", encoding="utf-8")

    note = scaffold.write_contributing(
        tmp_path, TEMPLATE_MD, dry_run=False, warn_mixed="mixed", update=True, merge_mixed=True
    )

    assert note is None  # recorded as a patch, not reported as a hand-merge
    assert "## Reporting Issues" in path.read_text(encoding="utf-8")


# --- detect: a census that names remedies ---------------------------------------


def test_detect_findings_name_the_remedy(tmp_path):
    (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (tmp_path / ".releaserc.json").write_text('{"assets": ["package-lock.json"]}', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## [1.0.0] - 2026-01-01\n\n# Changelog\n\nAll notable changes.\n", encoding="utf-8"
    )
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "changelog-check.yml").write_text(
        "name: x\n", encoding="utf-8"
    )

    data = scaffold.detect_project(tmp_path)
    areas = {f["area"] for f in data["findings"]}
    remedies = " ".join(f["remedy"] for f in data["findings"])

    assert ".github/pull_request_template.md" in areas
    assert ".releaserc.json" in areas
    assert "CHANGELOG.md" in areas
    assert "changelogTitle" in remedies  # the title is stranded mid-file
    assert data["changelog"]["title_at_top"] is False
    assert data["changelog"]["title_line"] == 3  # version heading, blank, then the title


def test_detect_census_counts_the_pr_template(tmp_path):
    data = scaffold.detect_project(tmp_path)

    assert data["files"][".github/pull_request_template.md"] is False


def test_detect_reports_a_vendored_sibling_skill(tmp_path):
    """A copy scaffold did not write, and must not delete: report it as a decision."""
    vendored = tmp_path / "skills" / "gh-router"
    vendored.mkdir(parents=True)
    (vendored / "SKILL.md").write_text("---\nname: gh-router\n---\n", encoding="utf-8")

    findings = scaffold.detect_project(tmp_path)["findings"]
    finding = next(f for f in findings if f["area"] == "skills/gh-router")

    assert "no longer manages" in finding["detail"]
    assert "git rm -r skills/gh-router" in finding["remedy"]


def test_detect_json_drops_the_human_summary(tmp_path, capsys):
    _seed_repo(tmp_path)

    assert _run_main("--detect", "--json", "--cwd", str(tmp_path)) == 0
    captured = capsys.readouterr()

    assert json.loads(captured.out)["inferred_shape"] == "greenfield"
    assert captured.err == ""
