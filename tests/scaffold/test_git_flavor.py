"""Tests for the git flavor's gh-router projection.

Regression: the `pr` subskill was renamed to `pr-land` (breaking) and the
harness dropped the legacy `TRIGGER:` description pseudo-syntax, but the git
flavor kept generating the old two-subskill router — a retrofit would have
deleted `pr-land` and re-introduced a description form `validate-deps` flags.
"""

import importlib.util
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"

SUBSKILLS = ["gh-release", "pr-land", "pr-enhance"]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_git_flavor", SCRIPT)


# --- router projection declares all three subskills ---------------------------


def test_router_skill_manages_all_subskills():
    skill = scaffold.GH_ROUTER_SKILL
    assert "manage: [gh-release, pr-land, pr-enhance]" in skill
    assert "  pr-land [--watch --merge]" in skill
    assert "| `pr-land`" in skill


def test_router_skill_has_no_legacy_trigger_syntax():
    for skill in (scaffold.GH_ROUTER_SKILL, scaffold.GH_RELEASE_SKILL, scaffold.PR_ENHANCE_SKILL):
        assert "TRIGGER:" not in skill


def test_subskill_loop_covers_pr_land():
    src = SCRIPT.read_text(encoding="utf-8")
    assert 'for sub in ["gh-release", "pr-land", "pr-enhance"]' in src


def test_pr_land_fallback_is_not_a_dead_link():
    # non-harness target repos fall back to the embedded stub; the router still
    # advertises pr-land, so the subskill file must exist
    assert "name: pr-land" in scaffold.PR_LAND_SKILL


# --- generated tree carries pr-land + executable scripts ----------------------


def test_write_gh_router_emits_pr_land(tmp_path):
    scaffold._write_gh_router(tmp_path, dry_run=False)
    base = tmp_path / "skills" / "gh-router"
    for sub in SUBSKILLS:
        assert (base / "subskills" / sub / "SKILL.md").is_file(), sub
    pr_sh = base / "subskills" / "pr-land" / "scripts" / "pr.sh"
    assert pr_sh.is_file()
    assert pr_sh.stat().st_mode & 0o111  # scripts stay executable


def test_generated_router_skills_have_no_trigger_syntax(tmp_path):
    scaffold._write_gh_router(tmp_path, dry_run=False)
    base = tmp_path / "skills" / "gh-router"
    for md in [base / "SKILL.md", *(base / "subskills" / sub / "SKILL.md" for sub in SUBSKILLS)]:
        assert "TRIGGER:" not in md.read_text(encoding="utf-8"), md
