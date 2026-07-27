from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    return subprocess.run(
        ["uv", "run", str(SCRIPT_PATH), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def write_skill(root: Path, name: str, depends_on: str | None = None) -> None:
    skill_dir = root / "skills" / name
    skill_dir.mkdir(parents=True)
    metadata = f"metadata:\n  depends-on: [{depends_on}]\n" if depends_on else ""
    (skill_dir / "SKILL.md").write_text(
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
    (skill_dir / "SKILL.md").write_text(
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
        tmp_path, "inline-desc",
        "name: inline-desc\ndescription: some inline string\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 1
    assert "LINT FAIL:" in result.stdout
    assert "block scalar" in result.stdout or "inline value" in result.stdout


def test_lint_detects_duplicate_skill_name(tmp_path: Path) -> None:
    """lint exits 1 when two SKILL.md files declare the same name."""
    write_raw_skill(
        tmp_path, "dup-a",
        "name: duplicate-name\ndescription: >-\n  first copy\n",
    )
    write_raw_skill(
        tmp_path, "dup-b",
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
        tmp_path, "valid",
        "name: valid-skill\ndescription: >-\n  A valid skill for testing.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "lint")

    assert result.returncode == 0
    assert "Lint passed" in result.stdout


def test_check_detects_missing_dependency(tmp_path: Path) -> None:
    """check exits 1 when a skill depends on a nonexistent skill."""
    write_raw_skill(
        tmp_path, "consumer",
        "name: consumer\ndescription: >-\n  A consumer.\n"
        "metadata:\n  depends-on: [nonexistent]\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 1
    assert "depends on missing skill 'nonexistent'" in result.stdout


def test_check_passes_valid_dependencies(tmp_path: Path) -> None:
    """check exits 0 when all depends-on references exist."""
    write_raw_skill(
        tmp_path, "provider",
        "name: provider\ndescription: >-\n  A provider.\n",
    )
    write_raw_skill(
        tmp_path, "consumer",
        "name: consumer\ndescription: >-\n  A consumer.\n"
        "metadata:\n  depends-on: [provider]\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "check")

    assert result.returncode == 0
    assert "All dependencies validated successfully" in result.stdout


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
        tmp_path, "over-budget",
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
        tmp_path, "no-trigger",
        "name: no-trigger\ndescription: >-\n  A plain description that does not have any of the key phrases.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "WARN" in result.stdout
    assert "trigger vocabulary" in result.stdout


def test_context_check_passes_clean(tmp_path: Path) -> None:
    """context-check passes a skill with proper description and trigger words."""
    write_raw_skill(
        tmp_path, "good-skill",
        "name: good-skill\ndescription: >-\n  Use this skill when you need to validate stuff.\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "context-check")

    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_fix_actually_modifies(tmp_path: Path) -> None:
    """fix without --dry-run changes the file on disk."""
    write_raw_skill(
        tmp_path, "inline-desc",
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
        tmp_path, "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path, "caller",
        "name: caller\ndescription: >-\n  A caller.\n"
        "metadata:\n  depends-on: [old-name]\n",
    )

    old_dir = tmp_path / "skills" / "old-name"
    caller_content_before = (
        tmp_path / "skills" / "caller" / "SKILL.md"
    ).read_text(encoding="utf-8")

    result = run_validate_deps(
        "--project-root", str(tmp_path), "rename", "--dry-run", "old-name", "new-name",
    )

    assert result.returncode == 0
    assert "Would rename:" in result.stdout
    assert "Would update:" in result.stdout
    # Directory must remain named old-name
    assert old_dir.is_dir()
    # Caller must remain unchanged
    assert (
        tmp_path / "skills" / "caller" / "SKILL.md"
    ).read_text(encoding="utf-8") == caller_content_before


def test_rename_runs_check_after_mutation(tmp_path: Path) -> None:
    """rename re-runs check after renaming and reports verification."""
    write_raw_skill(
        tmp_path, "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path, "caller",
        "name: caller\ndescription: >-\n  A caller.\n"
        "metadata:\n  depends-on: [old-name]\n",
    )

    result = run_validate_deps(
        "--project-root", str(tmp_path), "rename", "old-name", "new-name",
    )

    assert result.returncode == 0
    assert "Verifying with check..." in result.stdout
    assert "All dependencies validated successfully" in result.stdout


def test_rename_cascades_updates(tmp_path: Path) -> None:
    """rename changes directory name and updates references."""
    write_raw_skill(
        tmp_path, "old-name",
        "name: old-name\ndescription: >-\n  A skill to rename.\n",
    )
    write_raw_skill(
        tmp_path, "caller",
        "name: caller\ndescription: >-\n  A caller.\n"
        "metadata:\n  depends-on: [old-name]\n",
    )

    result = run_validate_deps(
        "--project-root", str(tmp_path), "rename", "old-name", "new-name",
    )

    assert result.returncode == 0
    assert "RENAMED:" in result.stdout
    assert "UPDATED:" in result.stdout
    assert "UPDATED REFERENCES:" in result.stdout
    # Directory renamed
    assert (tmp_path / "skills" / "new-name").is_dir()
    assert not (tmp_path / "skills" / "old-name").is_dir()
    # Caller references new name
    caller_content = (
        tmp_path / "skills" / "caller" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "new-name" in caller_content
    assert "old-name" not in caller_content


def test_make_validate_deps_runs_check(tmp_path: Path) -> None:
    """make validate-deps executes check against PROJECT_ROOT."""
    # Give the temp project a valid skill so check passes
    write_raw_skill(
        tmp_path, "skill-a",
        "name: skill-a\ndescription: >-\n  A valid skill.\n",
    )

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["make", "validate-deps", f"PROJECT_ROOT={tmp_path}"],
        capture_output=True, text=True, timeout=60,
        cwd=str(project_root),
    )
    assert result.returncode == 0
    assert "All dependencies validated successfully" in result.stdout


def test_make_validate_deps_fix_dry_run_default(tmp_path: Path) -> None:
    """make validate-deps-fix defaults to --dry-run (safe mode)."""
    write_raw_skill(
        tmp_path, "fixme",
        "name: fixme\ndescription: inline value\n",
    )

    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["make", "validate-deps-fix", f"PROJECT_ROOT={tmp_path}"],
        capture_output=True, text=True, timeout=60,
        cwd=str(project_root),
    )
    assert result.returncode == 0
    assert "Would fix:" in result.stdout
    # Verify no verification runs in dry-run mode
    assert "Verifying" not in result.stdout


def test_rename_dry_run_detects_missing_skill(tmp_path: Path) -> None:
    """rename --dry-run exits 1 if the source skill does not exist."""
    result = run_validate_deps(
        "--project-root", str(tmp_path), "rename", "--dry-run",
        "nonexistent", "newname",
    )

    assert result.returncode == 1
    assert "nonexistent" in result.stderr


def test_fix_runs_lint_after_mutation(tmp_path: Path) -> None:
    """fix re-runs lint after fixing and reports verification."""
    write_raw_skill(
        tmp_path, "fixme",
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
        tmp_path, "first",
        "name: duplicate\ndescription: inline val one\n",
    )
    write_raw_skill(
        tmp_path, "second",
        "name: duplicate\ndescription: inline val two\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix")

    assert result.returncode == 1
    assert "Verifying with lint..." in result.stdout
    assert "lint still has issues" in result.stderr


def test_fix_dry_run_skips_verification(tmp_path: Path) -> None:
    """fix --dry-run does not run post-mutation verification."""
    write_raw_skill(
        tmp_path, "inline-desc",
        "name: inline-desc\ndescription: some inline value\n",
    )

    result = run_validate_deps("--project-root", str(tmp_path), "fix", "--dry-run")

    assert result.returncode == 0
    assert "Would fix:" in result.stdout
    assert "Verifying" not in result.stdout


def test_fix_dry_run_reports_without_modifying(tmp_path: Path) -> None:
    """fix --dry-run prints what would change without writing to disk."""
    write_raw_skill(
        tmp_path, "inline-desc",
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
        capture_output=True, text=True,
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
