"""Tests for the changelog-sync hidden-type guardrail fix.

Regression: a changelog sync committed with a visible type (e.g. ``docs:``)
re-triggers the Unreleased guard, which then demands the sync commit itself
be listed — an infinite loop. Sync commits must use a hidden type
(``chore: sync changelog unreleased section``), which the generator already
skips unless breaking (see TYPE_SECTIONS in changelog-unreleased.py).
"""

import importlib.util
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"
SYNC_SCRIPT = SKILL_DIR / "scripts" / "changelog-unreleased.py"
GIT_SKILL = SKILL_DIR / "subskills" / "git-scaffolding" / "SKILL.md"

SYNC_EXAMPLE = "chore: sync changelog unreleased section"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_sync", SCRIPT)
sync_mod = _load("changelog_unreleased_mod", SYNC_SCRIPT)


# --- fix-hint templates prescribe hidden-type sync ---------------------------


def test_check_workflow_fix_hint_uses_hidden_type():
    hint = scaffold.CHANGELOG_CHECK_YML
    assert SYNC_EXAMPLE in hint
    assert "loops forever" in hint


def test_check_workflow_comment_body_uses_hidden_type():
    body = scaffold.CHANGELOG_CHECK_YML
    assert "git commit -m 'chore: sync changelog unreleased section'" in body


def test_pre_push_hook_fix_hint_uses_hidden_type():
    hook = scaffold.GITHOOK_PRE_PUSH
    assert SYNC_EXAMPLE in hook
    assert "loops forever" in hook
    assert "git commit --amend --no-edit" in hook  # amend alternative retained


def test_contributing_templates_prescribe_hidden_sync():
    for tmpl in (
        scaffold.CONTRIBUTING_MD_TMPL,
        scaffold.CONTRIBUTING_MD_TMPL_PYTHON,
        scaffold.CONTRIBUTING_MD_TMPL_TYPESCRIPT,
    ):
        assert SYNC_EXAMPLE in tmpl
        assert "loops forever" in tmpl


def test_git_subskill_docs_prescribe_hidden_sync():
    text = GIT_SKILL.read_text(encoding="utf-8")
    assert SYNC_EXAMPLE in text
    assert "loops forever" in text


# --- loop warning is stderr-only ---------------------------------------------


def test_visible_sync_head_warns(capsys):
    sync_mod.warn_if_visible_sync_head([("docs: sync changelog unreleased section", "")])
    err = capsys.readouterr().err
    assert "visible-type changelog sync" in err
    assert "hidden type" in err


def test_hidden_sync_head_stays_silent(capsys):
    sync_mod.warn_if_visible_sync_head([(SYNC_EXAMPLE, "")])
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_ordinary_visible_commit_stays_silent(capsys):
    sync_mod.warn_if_visible_sync_head([("feat: add search filters", "")])
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_empty_commits_stays_silent(capsys):
    sync_mod.warn_if_visible_sync_head([])
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


# --- normal generator path unchanged -----------------------------------------


def test_hidden_types_still_skipped_unless_breaking():
    sections = sync_mod.commits_to_sections(
        [
            ("feat: add search filters", ""),
            ("chore: sync changelog unreleased section", ""),
        ]
    )
    flat = [e for entries in sections.values() for e in entries]
    assert any("add search filters" in e for e in flat)
    assert not any("sync changelog" in e for e in flat)


def test_hidden_breaking_still_visible():
    sections = sync_mod.commits_to_sections(
        [("chore!: sync changelog unreleased section", "")]
    )
    flat = [e for entries in sections.values() for e in entries]
    assert any("sync changelog" in e for e in flat)


