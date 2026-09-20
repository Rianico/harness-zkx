"""Tests for `--update`: refresh generated infrastructure, preserve what the project owns.

`--update` exists because a plain `--flavor git` run rewrites every component,
including `CHANGELOG.md` (release history) and `release.yml` (the `ci` flavor's
projection). The tool decides replacement; the model only works the printed NEXT
list for the preserved files.
"""

import importlib.util
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


scaffold = _load("scaffold_mod_update", SCRIPT)

CHANGELOG = "# Changelog\n\n## [1.2.0] - 2026-01-01\n\n### Features\n\n- keep me\n"
CONTRIBUTING = "# Contributing to demo\n\n## Before PR\n\n`uv run pytest` must pass.\n"
RELEASE_YML = "name: Verify and Release\njobs:\n  verify:\n    steps:\n      - run: uv run pytest\n"


def _seed_repo(cwd: Path) -> None:
    (cwd / ".github" / "workflows").mkdir(parents=True)
    (cwd / ".githooks").mkdir(parents=True)
    (cwd / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
    (cwd / "CONTRIBUTING.md").write_text(CONTRIBUTING, encoding="utf-8")
    (cwd / ".github" / "workflows" / "release.yml").write_text(RELEASE_YML, encoding="utf-8")
    (cwd / ".githooks" / "pre-push").write_text("stale-hook\n", encoding="utf-8")


# --- replacement vs preservation ----------------------------------------------


def test_update_preserves_project_owned_files(tmp_path):
    _seed_repo(tmp_path)
    notes = scaffold.do_git(tmp_path, "demo", dry_run=False, update=True)

    assert (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8") == CHANGELOG
    assert (tmp_path / "CONTRIBUTING.md").read_text(encoding="utf-8") == CONTRIBUTING
    assert (tmp_path / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    ) == RELEASE_YML
    assert len(notes) == 3


def test_update_refreshes_managed_files(tmp_path):
    _seed_repo(tmp_path)
    scaffold.do_git(tmp_path, "demo", dry_run=False, update=True)

    assert (tmp_path / ".githooks" / "pre-push").read_text(encoding="utf-8") == (
        scaffold.GITHOOK_PRE_PUSH
    )
    assert (tmp_path / ".husky" / "pre-push").is_file()
    assert (tmp_path / ".releaserc.json").is_file()
    assert (tmp_path / ".github" / "workflows" / "changelog-check.yml").is_file()


def test_update_notes_name_the_preserved_file(tmp_path):
    _seed_repo(tmp_path)
    notes = scaffold.do_git(tmp_path, "demo", dry_run=False, update=True)
    joined = "\n".join(notes)

    for name in ("CHANGELOG.md", "CONTRIBUTING.md", "release.yml"):
        assert name in joined


def test_fresh_scaffold_has_no_notes(tmp_path):
    _seed_repo(tmp_path)
    assert scaffold.do_git(tmp_path, "demo", dry_run=False) == []


def test_update_dry_run_writes_nothing(tmp_path):
    _seed_repo(tmp_path)
    scaffold.do_git(tmp_path, "demo", dry_run=True, update=True)

    assert (tmp_path / ".githooks" / "pre-push").read_text(encoding="utf-8") == "stale-hook\n"
    assert not (tmp_path / ".releaserc.json").exists()


# --- CLI surface ---------------------------------------------------------------


def test_cli_update_implies_git_flavor(tmp_path, capsys):
    _seed_repo(tmp_path)
    sys.argv = ["scaffold.py", "--update", "--cwd", str(tmp_path)]
    # argparse writes usage to stderr on error; a 0 return proves --flavor was not required
    assert scaffold.main() == 0
    err = capsys.readouterr().err

    assert "NEXT — undetermined" in err
    assert (tmp_path / ".releaserc.json").is_file()


def test_cli_update_prints_next_actions_for_preserved_files(tmp_path, capsys):
    _seed_repo(tmp_path)
    sys.argv = ["scaffold.py", "--update", "--cwd", str(tmp_path)]
    scaffold.main()
    err = capsys.readouterr().err

    assert "preserved" in err
    assert "CHANGELOG.md" in err
    assert "→" in err  # concrete follow-up, not just a warning


# --- shipped source is the project's, not infrastructure ------------------------


def test_update_preserves_shipped_source_files(tmp_path):
    """`src/lib.rs`, the Python package and `tests/test_smoke.py` are starting points the project
    edits, so --update must report them as preserved rather than regenerating over real work."""
    scaffold.do_rust(tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80)
    scaffold.do_python(tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80)
    lib = tmp_path / "src" / "lib.rs"
    package = tmp_path / "src" / "demo" / "__init__.py"
    smoke = tmp_path / "tests" / "test_smoke.py"
    assert lib.read_text(encoding="utf-8") == scaffold.RUST_LIB_RS
    assert package.is_file(), "the flavor ships a covered package (src/<module>/__init__.py)"
    assert smoke.read_text(encoding="utf-8") == scaffold.render_template(
        "python/tests/test_smoke.py.j2", module="demo"
    )
    edited = "//! my crate\n"
    lib.write_text(edited, encoding="utf-8")
    package.write_text('"""mine"""\n', encoding="utf-8")
    smoke.write_text("def test_real() -> None:\n    assert True\n", encoding="utf-8")

    notes = scaffold.do_rust(
        tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80, update=True
    )
    notes += scaffold.do_python(
        tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80, update=True
    )

    assert lib.read_text(encoding="utf-8") == edited
    assert package.read_text(encoding="utf-8") == '"""mine"""\n'
    assert "test_real" in smoke.read_text(encoding="utf-8")
    joined = "\n".join(notes)
    assert "lib.rs" in joined
    assert "__init__.py" in joined, "SOURCE_OWNED_PATTERNS must cover the computed package path"
    assert "test_smoke.py" in joined


# --- ownership follows the path, not the file's presence (issue #51) ------------


def test_update_never_recreates_an_absent_project_owned_path(tmp_path):
    """A repo that renamed `tests/` to `test/` owns its tests: --update must not restore one.

    Presence is not the ownership signal. Without this the fork is re-flagged as drift on
    every `--check`, and `--update` writes a skeleton back into a project that deliberately
    has none.
    """
    scaffold.do_typescript(
        tmp_path, "demo", dry_run=False, ts_variant="lib", with_coverage=False, threshold=80
    )
    moved = tmp_path / "tests" / "index.test.ts"
    assert moved.is_file()
    (tmp_path / "tests").rename(tmp_path / "test")

    notes = scaffold.do_typescript(
        tmp_path,
        "demo",
        dry_run=False,
        ts_variant="lib",
        with_coverage=False,
        threshold=80,
        update=True,
    )

    assert not (tmp_path / "tests").exists(), "an absent project-owned path is not drift"
    joined = "\n".join(notes)
    assert "index.test.ts" in joined
    assert "not recreated" in joined


def test_owned_pattern_paths_get_the_same_rule(tmp_path):
    """`SOURCE_OWNED_PATTERNS` (a computed package dir) is not presence-keyed either."""
    scaffold.do_python(tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80)
    package = tmp_path / "src" / "demo" / "__init__.py"
    assert package.is_file()
    package.unlink()

    scaffold.do_python(
        tmp_path, "demo", dry_run=False, with_coverage=False, threshold=80, update=True
    )

    assert not package.exists()


def test_check_is_green_when_a_project_owned_path_was_renamed(tmp_path, capsys):
    """The acceptance for the fork: `--check` exits 0 on an intentional one."""
    scaffold.do_typescript(
        tmp_path, "demo", dry_run=False, ts_variant="lib", with_coverage=False, threshold=80
    )
    (tmp_path / "tests").rename(tmp_path / "test")
    sys.argv = [
        "scaffold.py",
        "--check",
        "--flavor",
        "typescript",
        "--ts-variant",
        "lib",
        "--project-name",
        "demo",
        "--cwd",
        str(tmp_path),
    ]

    assert scaffold.main() == 0
    captured = capsys.readouterr()
    assert "drift 0" in captured.out + captured.err


def test_check_still_reports_drift_for_a_repo_that_was_never_scaffolded(tmp_path, capsys):
    """The guard for the rule above: ownership must not mask a repo with nothing in it."""
    sys.argv = [
        "scaffold.py",
        "--check",
        "--flavor",
        "typescript",
        "--ts-variant",
        "lib",
        "--project-name",
        "demo",
        "--cwd",
        str(tmp_path),
    ]

    assert scaffold.main() == 1
    captured = capsys.readouterr()
    assert "missing" in captured.out + captured.err
    assert "AGENTS.md" in captured.out + captured.err
