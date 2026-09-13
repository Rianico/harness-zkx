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
