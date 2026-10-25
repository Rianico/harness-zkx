from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tests.in_process import run_script_in_process

SCRIPT_PATH = (
    Path(__file__).parent.parent
    / "skills"
    / "ai-engineering-expert"
    / "subskills"
    / "skill-authoring"
    / "scripts"
    / "validate-deps.py"
)


def run_validate_deps(*args: str) -> subprocess.CompletedProcess[str]:
    # Same interpreter and venv the tests run in; `uv run` only wrapped python.
    return run_script_in_process([sys.executable, str(SCRIPT_PATH), *args])


def write_skill(root: Path, name: str, depends_on: str | None = None) -> None:
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    metadata = f"metadata:\n  depends-on: [{depends_on}]\n" if depends_on else ""
    _ = (skill_dir / "SKILL.md").write_text(
        (
            f"---\nname: {name}\n"
            "description: Test skill for dependency validation.\n"
            f"{metadata}---\n\n# {name}\n"
        ),
        encoding="utf-8",
    )


def write_raw_skill(root: Path, name: str, frontmatter: str) -> None:
    """Write a SKILL.md with arbitrary frontmatter for testing."""
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    _ = (skill_dir / "SKILL.md").write_text(
        f"---\n{frontmatter}---\n\n# {name}\n",
        encoding="utf-8",
    )


def test_lint_detects_missing_required_field(tmp_path: Path) -> None:
    """lint exits 1 when a skill is missing 'description'."""
    write_raw_skill(tmp_path, "no-desc", "name: no-desc\n")

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "Missing required field 'description'" in result.stdout


def test_lint_detects_inline_description(tmp_path: Path) -> None:
    """lint exits 1 when 'description' uses inline value instead of block scalar."""
    write_raw_skill(
        tmp_path,
        "inline-desc",
        "name: inline-desc\ndescription: some inline string\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "block scalar" in result.stdout or "inline value" in result.stdout


def test_lint_detects_duplicate_skill_name(tmp_path: Path) -> None:
    """lint exits 1 when two SKILL.md files declare the same name."""
    write_raw_skill(
        tmp_path,
        "dup-a",
        "name: duplicate-name\ndescription: >-\n  first copy\n",
    )
    write_raw_skill(
        tmp_path,
        "dup-b",
        "name: duplicate-name\ndescription: >-\n  second copy\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "duplicate-name" in result.stdout
    assert "dup-a" in result.stdout or "dup-b" in result.stdout


def test_lint_passes_clean_skills(tmp_path: Path) -> None:
    """lint exits 0 for a valid skill with proper block scalar."""
    write_raw_skill(
        tmp_path,
        "valid",
        "name: valid-skill\ndescription: >-\n  A valid skill for testing.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 0
    assert "Lint passed" in result.stdout


def test_check_detects_missing_dependency(tmp_path: Path) -> None:
    """check exits 1 when a skill depends on a nonexistent skill."""
    write_raw_skill(
        tmp_path,
        "consumer",
        "name: consumer\ndescription: >-\n  A consumer.\nmetadata:\n  depends-on: [nonexistent]\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 1
    assert "depends on missing skill 'nonexistent'" in result.stdout


def test_check_passes_valid_dependencies(tmp_path: Path) -> None:
    """check exits 0 when all depends-on references exist."""
    write_raw_skill(
        tmp_path,
        "provider",
        "name: provider\ndescription: >-\n  A provider.\n",
    )
    write_raw_skill(
        tmp_path,
        "consumer",
        "name: consumer\ndescription: >-\n  A consumer.\nmetadata:\n  depends-on: [provider]\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 0
    assert "All dependencies validated successfully" in result.stdout


def test_commands_dir_is_not_scanned(tmp_path: Path) -> None:
    """commands/ is legacy: its files are not registry entries."""
    write_raw_skill(
        tmp_path,
        "caller",
        "name: caller\ndescription: >-\n  A caller.\nmetadata:\n  depends-on: [legacy-cmd]\n",
    )
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    _ = (commands_dir / "legacy-cmd.md").write_text(
        "---\nname: legacy-cmd\n---\n\n# legacy-cmd\n", encoding="utf-8"
    )

    check = run_validate_deps("--project-root", str(tmp_path), "check")

    assert check.returncode == 1
    assert "depends on missing skill 'legacy-cmd'" in check.stdout

    related = run_validate_deps("--project-root", str(tmp_path), "related", "legacy-cmd")

    assert "commands/" not in related.stdout


def test_context_check_fails_missing_description(tmp_path: Path) -> None:
    """context-check exits 1 when a skill has no description."""
    write_raw_skill(tmp_path, "no-desc", "name: no-desc\n")

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 1
    assert "FAIL" in result.stdout
    assert "description missing or empty" in result.stdout


def test_context_check_fails_over_budget(tmp_path: Path) -> None:
    """context-check exits 1 when description exceeds 300 chars."""
    long_text = "x" * 350
    write_raw_skill(
        tmp_path,
        "over-budget",
        f"name: over-budget\ndescription: >-\n  {long_text}\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 1
    assert "FAIL" in result.stdout
    assert "350" in result.stdout
    assert "300" in result.stdout


def test_context_check_warns_missing_triggers(tmp_path: Path) -> None:
    """context-check warns when a valid skill description lacks trigger vocabulary."""
    write_raw_skill(
        tmp_path,
        "no-trigger",
        "name: no-trigger\ndescription: >-\n  A plain description that does not have any of the key phrases.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "trigger vocabulary" in result.stdout


def test_context_check_passes_clean(tmp_path: Path) -> None:
    """context-check passes a skill with proper description and trigger words."""
    write_raw_skill(
        tmp_path,
        "good-skill",
        "name: good-skill\ndescription: >-\n  Use this skill when you need to validate stuff.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_context_check_warns_deprecated_trigger(tmp_path: Path) -> None:
    """context-check warns when a skill uses deprecated TRIGGER: syntax."""
    write_raw_skill(
        tmp_path,
        "legacy-trigger",
        "name: legacy-trigger\ndescription: >-\n  Use when fixing bugs. TRIGGER: bug, fix\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "deprecated 'TRIGGER:' tag" in result.stdout


def test_context_check_warns_missing_symptom_keywords(tmp_path: Path) -> None:
    """context-check warns when Use when lacks symptom keywords or problem-framing signals."""
    write_raw_skill(
        tmp_path,
        "abstract-skill",
        "name: abstract-skill\ndescription: >-\n  General conceptual tool. Use when working with abstractions.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "symptom keywords" in result.stdout


def test_context_check_accepts_opt_in_negative_boundary(tmp_path: Path) -> None:
    """context-check accepts opt-in negative boundary clauses."""
    write_raw_skill(
        tmp_path,
        "boundary-skill",
        "name: boundary-skill\ndescription: >-\n  Audits code invariants. Use when debugging errors. Do not use for unit testing.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "PASS" in result.stdout
    assert "WARN" not in result.stdout


def test_fix_actually_modifies(tmp_path: Path) -> None:
    """fix without --dry-run changes the file on disk."""
    write_raw_skill(
        tmp_path,
        "inline-desc",
        "name: inline-desc\ndescription: some inline value\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix")

    assert result.returncode == 0
    assert "FIXED:" in result.stdout
    # File should now have block scalar indicator
    content = (tmp_path / "skills" / "inline-desc" / "SKILL.md").read_text(encoding="utf-8")
    assert "description: >-" in content

    # Re-running fix reports 0 fixes
    result2 = run_validate_deps("--project-root", str(tmp_path), "fix")
    assert "Would fix 0 files" in result2.stdout or "Fixed 0 files" in result2.stdout


def test_rename_dry_run_reports_without_modifying(tmp_path: Path) -> None:
    """rename --dry-run prints what would change without modifying disk."""
    write_raw_skill(
        tmp_path,
        "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path,
        "caller",
        "name: caller\ndescription: >-\n  A caller.\nmetadata:\n  depends-on: [old-name]\n",
    )

    old_dir = tmp_path / "skills" / "old-name"
    caller_content_before = (tmp_path / "skills" / "caller" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    result = run_validate_deps(
        "--project-root",
        str(tmp_path),
        "rename",
        "--dry-run",
        "old-name",
        "new-name",
    )

    assert result.returncode == 0
    assert "Would rename:" in result.stdout
    assert "Would update:" in result.stdout
    # Directory must remain named old-name
    assert old_dir.is_dir()
    # Caller must remain unchanged
    assert (tmp_path / "skills" / "caller" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == caller_content_before


def test_rename_runs_check_after_mutation(tmp_path: Path) -> None:
    """rename re-runs check after renaming and reports verification."""
    write_raw_skill(
        tmp_path,
        "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path,
        "caller",
        "name: caller\ndescription: >-\n  A caller.\nmetadata:\n  depends-on: [old-name]\n",
    )

    result = run_validate_deps(
        "--project-root",
        str(tmp_path),
        "rename",
        "old-name",
        "new-name",
    )

    assert result.returncode == 0
    assert "Verifying with check..." in result.stdout
    assert "All dependencies validated successfully" in result.stdout


def test_rename_cascades_updates(tmp_path: Path) -> None:
    """rename changes directory name and updates references."""
    write_raw_skill(
        tmp_path,
        "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path,
        "caller",
        "name: caller\ndescription: >-\n  A caller.\nmetadata:\n  depends-on: [old-name]\n",
    )

    result = run_validate_deps(
        "--project-root",
        str(tmp_path),
        "rename",
        "old-name",
        "new-name",
    )

    assert result.returncode == 0
    assert "RENAMED:" in result.stdout
    assert "UPDATED:" in result.stdout
    assert "UPDATED REFERENCES:" in result.stdout
    # Directory renamed
    assert (tmp_path / "skills" / "new-name").is_dir()
    assert not (tmp_path / "skills" / "old-name").is_dir()
    # Caller references new name
    caller_content = (tmp_path / "skills" / "caller" / "SKILL.md").read_text(encoding="utf-8")
    assert "new-name" in caller_content
    assert "old-name" not in caller_content


def test_rename_rewrites_exact_list_item_only(tmp_path: Path) -> None:
    """rename updates the exact flow-list item without corrupting prefixed siblings."""
    write_raw_skill(tmp_path, "pr", "name: pr\ndescription: >-\n  A PR skill.\n")
    write_raw_skill(
        tmp_path,
        "parent",
        "name: parent\ndescription: >-\n  A parent.\nmetadata:\n"
        "  manage: [gh-release, pr-enhance, pr]\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "rename", "pr", "pr-land")

    assert result.returncode == 0
    parent_content = (tmp_path / "skills" / "parent" / "SKILL.md").read_text(encoding="utf-8")
    assert "  manage: [gh-release, pr-enhance, pr-land]" in parent_content
    assert "pr-land-enhance" not in parent_content


def test_make_validate_deps_runs_check(tmp_path: Path) -> None:
    """make validate-deps executes check against PROJECT_ROOT."""
    # Give the temp project a valid skill so check passes
    write_raw_skill(
        tmp_path,
        "skill-a",
        "name: skill-a\ndescription: >-\n  A valid skill.\n",
    )

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["make", "validate-deps", f"PROJECT_ROOT={tmp_path}"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(project_root),
    )
    assert result.returncode == 0
    assert "All dependencies validated successfully" in result.stdout


def test_make_validate_deps_fix_dry_run_default(tmp_path: Path) -> None:
    """make validate-deps-fix defaults to --dry-run (safe mode)."""
    write_raw_skill(
        tmp_path,
        "fixme",
        "name: fixme\ndescription: inline value\n",
    )

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["make", "validate-deps-fix", f"PROJECT_ROOT={tmp_path}"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(project_root),
    )
    assert result.returncode == 0
    assert "Would fix:" in result.stdout
    # Verify no verification runs in dry-run mode
    assert "Verifying" not in result.stdout


def test_rename_dry_run_detects_missing_skill(tmp_path: Path) -> None:
    """rename --dry-run exits 1 if the source skill does not exist."""
    result = run_validate_deps(
        "--project-root",
        str(tmp_path),
        "rename",
        "--dry-run",
        "nonexistent",
        "newname",
    )

    assert result.returncode == 1
    assert "nonexistent" in result.stderr


def test_fix_runs_lint_after_mutation(tmp_path: Path) -> None:
    """fix re-runs lint after fixing and reports verification."""
    write_raw_skill(
        tmp_path,
        "fixme",
        "name: fixme\ndescription: inline description here\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix")

    assert result.returncode == 0
    assert "Verifying with lint..." in result.stdout
    assert "Lint passed" in result.stdout


def test_fix_reports_post_lint_failure(tmp_path: Path) -> None:
    """fix exits 1 when post-fix lint still detects issues."""
    # Two skills with the same name (duplicate) — fix can't correct that
    write_raw_skill(
        tmp_path,
        "first",
        "name: duplicate\ndescription: inline val one\n",
    )
    write_raw_skill(
        tmp_path,
        "second",
        "name: duplicate\ndescription: inline val two\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix")

    assert result.returncode == 1
    assert "Verifying with lint..." in result.stdout
    assert "lint still has issues" in result.stderr


def test_fix_dry_run_skips_verification(tmp_path: Path) -> None:
    """fix --dry-run does not run post-mutation verification."""
    write_raw_skill(
        tmp_path,
        "inline-desc",
        "name: inline-desc\ndescription: some inline value\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix", "--dry-run")

    assert result.returncode == 0
    assert "Would fix:" in result.stdout
    assert "Verifying" not in result.stdout


def test_fix_dry_run_reports_without_modifying(tmp_path: Path) -> None:
    """fix --dry-run prints what would change without writing to disk."""
    write_raw_skill(
        tmp_path,
        "inline-desc",
        "name: inline-desc\ndescription: some inline value\n",
    )

    skill_file = tmp_path / "skills" / "inline-desc" / "SKILL.md"
    content_before = skill_file.read_text(encoding="utf-8")

    result = run_validate_deps("--project-root", str(tmp_path), "fix", "--dry-run")

    assert result.returncode == 0
    assert "Would fix:" in result.stdout
    # File must be unchanged
    assert skill_file.read_text(encoding="utf-8") == content_before


def test_frontmatter_is_hard_dependency() -> None:
    """Running without uv run (no frontmatter installed) prints clear error."""
    base_python = Path(sys.base_exec_prefix) / "bin" / "python3"
    result = subprocess.run(
        [str(base_python), "-I", str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "python-frontmatter" in result.stderr or "python-frontmatter" in result.stdout
    # No raw traceback should escape
    assert "Traceback" not in result.stderr


def test_callers_lists_inbound_depends_on(tmp_path: Path) -> None:
    write_skill(tmp_path, "target")
    write_skill(tmp_path, "caller-a", "target")
    write_skill(tmp_path, "caller-b", "other")

    result = run_validate_deps("--project-root", str(tmp_path), "callers", "target")

    assert result.returncode == 0
    assert "Inbound Dependencies (callers):" in result.stdout
    assert "caller-a" in result.stdout
    assert "caller-b" not in result.stdout


def test_callers_reports_no_dependents(tmp_path: Path) -> None:
    write_skill(tmp_path, "target")

    result = run_validate_deps("--project-root", str(tmp_path), "callers", "target")

    assert result.returncode == 0
    assert "Inbound Dependencies (callers):" in result.stdout
    assert "(None)" in result.stdout


def _credited_frontmatter(credits_body: str) -> str:
    return (
        "name: credited\ndescription: >-\n  A credited skill.\n"
        f"metadata:\n  credits:\n{credits_body}"
    )


def test_lint_passes_single_mapping_credits(tmp_path: Path) -> None:
    """metadata.credits as one mapping with source+author passes lint."""
    write_raw_skill(
        tmp_path,
        "credited",
        _credited_frontmatter(
            "    source: https://github.com/example/upstream\n"
            "    author: example\n"
            "    version: main\n"
            "    note: Adapted from upstream-setup\n"
        ),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 0, result.stdout
    assert "Lint passed" in result.stdout


def test_lint_passes_credits_list(tmp_path: Path) -> None:
    """metadata.credits as a list of mappings, each with source or author, passes lint."""
    write_raw_skill(
        tmp_path,
        "credited",
        _credited_frontmatter(
            "    - source: https://github.com/example/one\n"
            "      author: one\n"
            "    - author: two\n"
            "      note: blog post\n"
        ),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 0, result.stdout
    assert "Lint passed" in result.stdout


def test_lint_fails_credits_as_string(tmp_path: Path) -> None:
    """metadata.credits must be a mapping or list of mappings, not a bare string."""
    write_raw_skill(tmp_path, "credited", _credited_frontmatter("    just-a-string\n"))

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "must be a mapping or a list of mappings" in result.stdout


def test_lint_fails_credit_missing_source_and_author(tmp_path: Path) -> None:
    """A credit entry without source and without author fails lint."""
    write_raw_skill(tmp_path, "credited", _credited_frontmatter("    version: '1.0'\n"))

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "needs a non-empty 'source' or 'author'" in result.stdout


def test_lint_fails_credit_unknown_key(tmp_path: Path) -> None:
    """A credit entry with an unrecognized key fails lint."""
    write_raw_skill(
        tmp_path,
        "credited",
        _credited_frontmatter("    source: https://example.com\n    repo: bad\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "unrecognized keys: repo" in result.stdout


def write_package_file(root: Path, relative: str, body: str) -> None:
    """Write a markdown file at skills/<relative>."""
    path = root / "skills" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(body, encoding="utf-8")


def reference_skill(name: str, body: str) -> str:
    """Valid SKILL.md frontmatter plus a body that carries reference targets."""
    return (
        f"---\nname: {name}\ndescription: >-\n  Test skill for reference validation.\n---\n\n{body}"
    )


def test_refs_passes_clean_package(tmp_path: Path) -> None:
    """refs exits 0 for an intra-package relative link and a $SKILL_DIR path."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read `$SKILL_DIR/references/basics.md` for details.\n"),
    )
    write_package_file(
        tmp_path,
        "alpha/references/basics.md",
        "# Basics\n\nBack to [the skill](../SKILL.md).\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout
    assert "Reference check: 2 checked, 0 failed, 0 warnings." in result.stdout


def test_refs_allows_sibling_hop_within_package(tmp_path: Path) -> None:
    """refs exits 0 for a subskill reaching a sibling via $SKILL_DIR/../."""
    write_package_file(tmp_path, "toolchain/SKILL.md", reference_skill("toolchain", "Parent.\n"))
    write_package_file(
        tmp_path,
        "toolchain/subskills/oxlint/SKILL.md",
        reference_skill("oxlint", "Pair with `$SKILL_DIR/../oxfmt/SKILL.md`.\n"),
    )
    write_package_file(
        tmp_path,
        "toolchain/subskills/oxfmt/SKILL.md",
        reference_skill("oxfmt", "Formatter.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout


def test_refs_fails_on_cross_package_upward_hop(tmp_path: Path) -> None:
    """refs exits 1 for the oxlint:11 shape: a hop out of the package's subskill tree."""
    write_package_file(tmp_path, "scaffold/SKILL.md", reference_skill("scaffold", "Scaffold.\n"))
    target = "$SKILL_DIR/../../scaffold/subskills/typescript-scaffolding/SKILL.md"
    write_package_file(
        tmp_path,
        "toolchain/subskills/oxlint/SKILL.md",
        reference_skill("oxlint", f"Scaffold linter (see `{target}`).\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 1
    assert "REF FAIL: skills/toolchain/subskills/oxlint/SKILL.md:7" in result.stdout
    assert f"missing target: {target}" in result.stdout


def test_refs_fails_when_skill_dir_target_escapes_package(tmp_path: Path) -> None:
    """refs exits 1 when a resolvable $SKILL_DIR target sits outside the package root."""
    write_package_file(tmp_path, "other/SKILL.md", reference_skill("other", "Other.\n"))
    target = "$SKILL_DIR/../../../other/SKILL.md"
    write_package_file(
        tmp_path,
        "toolchain/subskills/demo/SKILL.md",
        reference_skill("demo", f"See `{target}`.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 1
    assert f"target escapes package root: {target}" in result.stdout


def test_refs_fails_on_missing_skill_dir_target(tmp_path: Path) -> None:
    """refs exits 1 when a $SKILL_DIR target does not exist on disk."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read `$SKILL_DIR/references/missing.md`.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 1
    assert "missing target: $SKILL_DIR/references/missing.md" in result.stdout


def test_refs_fails_on_missing_link_target(tmp_path: Path) -> None:
    """refs exits 1 when a real Markdown link points at a nonexistent file."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read [the guide](references/guide.md).\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 1
    assert "missing target: references/guide.md" in result.stdout


def test_refs_ignores_fenced_code_blocks(tmp_path: Path) -> None:
    """refs exits 0 for broken targets inside backtick and tilde fences, even indented."""
    body = (
        "Example:\n\n"
        "```bash\n"
        "cat $SKILL_DIR/references/missing.md\n"
        "[the guide](references/guide.md)\n"
        "```\n\n"
        "  ~~~~markdown\n"
        "  `$SKILL_DIR/../../elsewhere/SKILL.md`\n"
        "  ~~~~\n"
    )
    write_package_file(tmp_path, "alpha/SKILL.md", reference_skill("alpha", body))

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout
    assert "Reference check: 0 checked, 0 failed, 0 warnings." in result.stdout


def test_refs_include_fences_reports_fenced_target(tmp_path: Path) -> None:
    """refs --include-fences reports a broken $SKILL_DIR target inside a fence."""
    body = "Example:\n\n```bash\ncat $SKILL_DIR/references/missing.md\n```\n"
    write_package_file(tmp_path, "alpha/SKILL.md", reference_skill("alpha", body))

    default = run_validate_deps("--project-root", str(tmp_path), "refs")
    strict = run_validate_deps("--project-root", str(tmp_path), "refs", "--include-fences")

    assert default.returncode == 0, default.stdout
    assert "Reference check: 0 checked, 0 failed, 0 warnings." in default.stdout
    assert strict.returncode == 1, strict.stdout
    expected = (
        "REF FAIL: skills/alpha/SKILL.md:10 — missing target: $SKILL_DIR/references/missing.md"
    )
    assert expected in strict.stdout
    assert "Reference check: 1 checked, 1 failed, 0 warnings." in strict.stdout


def test_check_stays_fence_blind(tmp_path: Path) -> None:
    """check ignores fenced targets that refs --include-fences would report."""
    body = "Example:\n\n```bash\ncat $SKILL_DIR/references/missing.md\n```\n"
    write_package_file(tmp_path, "alpha/SKILL.md", reference_skill("alpha", body))

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout
    assert "Reference check: 0 checked, 0 failed, 0 warnings." in result.stdout


def test_refs_ignores_links_inside_backticks(tmp_path: Path) -> None:
    """refs exits 0 for a link shown as an inline-code example."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Write `[the guide](references/guide.md)` to link a doc.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout


def test_refs_ignores_vendored_and_evidence_paths(tmp_path: Path) -> None:
    """refs exits 0 for broken targets under -raw, results, and reference directories."""
    write_package_file(
        tmp_path,
        "alpha/references/guides-raw/capture.md",
        "Scraped `$SKILL_DIR/../../elsewhere/SKILL.md`.\n",
    )
    write_package_file(
        tmp_path,
        "alpha/results/transcript.md",
        "Missed [the guide](references/guide.md).\n",
    )
    write_package_file(
        tmp_path,
        "alpha/reference/spec.md",
        "See [the guide](references/guide.md).\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF FAIL" not in result.stdout


def test_refs_warns_on_bare_skills_path(tmp_path: Path) -> None:
    """refs warns, without failing, on a bare skills/<pkg>/ path in prose."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Coordinates through skills/herdr/SKILL.md when installed.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "REF WARN: skills/alpha/SKILL.md:7" in result.stdout
    assert "bare skills/ path: skills/herdr/SKILL.md" in result.stdout
    assert "Reference check: 0 checked, 0 failed, 1 warnings." in result.stdout


def test_refs_ignores_placeholder_targets(tmp_path: Path) -> None:
    """refs exits 0 and counts nothing for template or label targets."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill(
            "alpha",
            "Read `$SKILL_DIR/references/<module>.md` or `$SKILL_DIR/references/...`.\n"
            "Mirror [docs](URL) and [raw-docs-path]() too.\n",
        ),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert result.returncode == 0, result.stdout
    assert "Reference check: 0 checked, 0 failed, 0 warnings." in result.stdout


def test_check_fails_when_reference_is_broken(tmp_path: Path) -> None:
    """check exits 1 when dependencies resolve but a reference is broken."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read `$SKILL_DIR/references/missing.md`.\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 1
    assert "All dependencies validated successfully." in result.stdout
    assert "REF FAIL" in result.stdout
    assert "Reference check: 1 checked, 1 failed, 0 warnings." in result.stdout


def test_refs_scopes_to_one_package(tmp_path: Path) -> None:
    """refs <skill> ignores broken references in other packages."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read [basics](references/basics.md).\n"),
    )
    write_package_file(tmp_path, "alpha/references/basics.md", "# Basics\n")
    write_package_file(
        tmp_path,
        "beta/SKILL.md",
        reference_skill("beta", "Read `$SKILL_DIR/references/missing.md`.\n"),
    )

    scoped = run_validate_deps("--project-root", str(tmp_path), "refs", "alpha")
    unscoped = run_validate_deps("--project-root", str(tmp_path), "refs")

    assert scoped.returncode == 0, scoped.stdout
    assert "REF FAIL" not in scoped.stdout
    assert unscoped.returncode == 1
    assert "skills/beta/SKILL.md" in unscoped.stdout


def test_refs_unknown_scope_fails(tmp_path: Path) -> None:
    """refs exits 1 when the named package does not exist."""
    write_package_file(tmp_path, "alpha/SKILL.md", reference_skill("alpha", "Alpha.\n"))

    result = run_validate_deps("--project-root", str(tmp_path), "refs", "nope")

    assert result.returncode == 1
    assert "nope" in result.stderr


def test_refs_json_emits_findings(tmp_path: Path) -> None:
    """refs --json emits checked, failures, and warnings with file, line, kind, target."""
    write_package_file(
        tmp_path,
        "alpha/SKILL.md",
        reference_skill("alpha", "Read [the guide](references/guide.md).\n"),
    )

    result = run_validate_deps("--project-root", str(tmp_path), "refs", "--json")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["checked"] == 1
    assert payload["failures"] == [
        {
            "file": "skills/alpha/SKILL.md",
            "line": 7,
            "kind": "link",
            "target": "references/guide.md",
        }
    ]
    assert payload["warnings"] == []
