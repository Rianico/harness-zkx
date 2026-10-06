"""The git flavor's boundary: scaffold ships infrastructure, never another skill's bytes.

Regression this locks down: `_write_gh_router` copied the `gh-router` skill — three subskills,
their scripts, and embedded fallback literals for repos without the harness — into every
scaffolded repo. The copy drifted from the harness original (the one found in the wild still
pointed at `pr-land/scripts/pr.sh` through a path that had moved) and pi already discovers the
skill from `~/.agents/skills`, so the duplicate bought nothing and cost a second source of
truth. Scaffold now writes no `skills/` directory at all, and a pre-existing copy is a decision
for the repo, never a silent refresh or delete.

Flipped intent: this file used to assert that the projection was complete and well-formed.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_git_flavor", SCRIPT)


def test_git_flavor_exposes_no_skill_projection():
    assert "gh-router" not in scaffold.GIT_COMPONENTS
    for gone in ("_write_gh_router", "GH_ROUTER_SKILL", "GH_RELEASE_SKILL", "PR_LAND_SKILL"):
        assert not hasattr(scaffold, gone), gone


def test_git_run_writes_no_skills_directory(tmp_path):
    scaffold.do_git(tmp_path, "demo", dry_run=False)

    assert not (tmp_path / "skills").exists()


def test_dry_run_does_not_offer_a_skill_projection(tmp_path, capsys):
    scaffold.do_git(tmp_path, "demo", dry_run=True)

    out = capsys.readouterr().out
    # Shipped prose may *name* the gh-router template (ownership moved there); what stays
    # forbidden is any action writing under a skills/ tree.
    assert not re.search(r"^would[^\n]*skills/", out, re.MULTILINE), out


def test_update_leaves_a_vendored_copy_to_the_project(tmp_path):
    vendored = tmp_path / "skills" / "gh-router"
    vendored.mkdir(parents=True)
    (vendored / "SKILL.md").write_text("hand-kept copy\n", encoding="utf-8")

    scaffold.do_git(tmp_path, "demo", dry_run=False, update=True)

    assert (vendored / "SKILL.md").read_text(encoding="utf-8") == "hand-kept copy\n"


def _run_main(*argv: str) -> int:
    old = sys.argv
    sys.argv = ["scaffold.py", *argv]
    try:
        return scaffold.main()
    finally:
        sys.argv = old


def test_node_repo_receives_no_typecheck_budget_and_no_baseline(tmp_path: pathlib.Path):
    _ = (tmp_path / "package.json").write_text('{"name": "demo-node"}\n', encoding="utf-8")
    assert _run_main("--cwd", str(tmp_path), "--flavor", "git") == 0
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")
    assert ".config/basedpyright-baseline.txt" not in releaserc
    assert _run_main("--cwd", str(tmp_path), "--check") == 0


def test_python_repo_receives_no_typecheck_budget_and_no_baseline(tmp_path: pathlib.Path):
    """The retired budget component left the scaffold entirely — the python flavor ships none."""
    _ = (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo-py"\n', encoding="utf-8")
    assert _run_main("--cwd", str(tmp_path), "--flavor", "all") == 0
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")
    assert ".config/basedpyright-baseline.txt" not in releaserc
    assert _run_main("--cwd", str(tmp_path), "--check") == 0


def test_python_repo_git_flavor_receives_no_typecheck_budget_and_no_baseline(
    tmp_path: pathlib.Path,
):
    _ = (tmp_path / ".python-version").write_text("3.14\n", encoding="utf-8")
    assert _run_main("--cwd", str(tmp_path), "--flavor", "git") == 0
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")
    assert ".config/basedpyright-baseline.txt" not in releaserc
    assert _run_main("--cwd", str(tmp_path), "--check") == 0


def test_node_repo_cannot_opt_in_to_typecheck_budget_anymore(tmp_path: pathlib.Path):
    """The old opt-in spelling is the retirement bridge: notice, exit 0, no budget script."""
    _ = (tmp_path / "package.json").write_text('{"name": "demo-node"}\n', encoding="utf-8")
    assert (
        _run_main(
            "--cwd",
            str(tmp_path),
            "--flavor",
            "git",
            "--only",
            "releaserc,typecheck-budget",
        )
        == 0
    )
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")
    assert ".config/basedpyright-baseline.txt" not in releaserc


def test_python_repo_without_typecheck_budget_writes_no_budget(tmp_path: pathlib.Path):
    """`--without` the retired spelling is also a bridge, not an error or a gate."""
    _ = (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo-py"\n', encoding="utf-8")
    assert (
        _run_main(
            "--cwd",
            str(tmp_path),
            "--flavor",
            "git",
            "--without",
            "typecheck-budget",
        )
        == 0
    )
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    releaserc = (tmp_path / ".releaserc.json").read_text(encoding="utf-8")
    assert ".config/basedpyright-baseline.txt" not in releaserc


def test_python_flavor_leaves_existing_releaserc_untouched(tmp_path: pathlib.Path):
    """No flavor rewrites `.releaserc.json` for a typecheck baseline any more — none exists."""
    _ = (tmp_path / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    assert _run_main("--cwd", str(tmp_path), "--flavor", "git") == 0
    releaserc_before = (tmp_path / ".releaserc.json").read_bytes()

    _ = (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    assert _run_main("--cwd", str(tmp_path), "--flavor", "python") == 0
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    assert (tmp_path / ".releaserc.json").read_bytes() == releaserc_before
    assert _run_main("--cwd", str(tmp_path), "--check") == 0


def test_typecheck_budget_component_retires_with_a_pointer(tmp_path, capsys):
    """All three retired spellings exit 0, write nothing, and name the native runner."""
    _ = (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo-py"\n', encoding="utf-8")
    for spelling in ("typecheck-budget", "typecheck_budget", "typecheck"):
        scaffold._typecheck_budget_retirement_notice_shown = False  # pyright: ignore[reportAttributeAccessIssue]
        capsys.readouterr()
        assert _run_main("--update", "--only", spelling, "--no-format", "--cwd", str(tmp_path)) == (
            0
        ), spelling
        err = capsys.readouterr().err
        assert "basedpyright" in err, spelling
        assert "unknown component" not in err, spelling
    assert not (tmp_path / "scripts" / "typecheck-budget.py").exists()
    assert not (tmp_path / ".releaserc.json").exists()
