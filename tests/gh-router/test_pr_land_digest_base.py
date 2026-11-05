"""The digest range forks from the remote-tracking base, never a stale local branch.

#350: `_draft_range` and `_digest_range_spec` built `<base>..<head_ref>` from the
bare branch name `resolve_base` returns. A local `main` behind `origin/main` then
absorbed the commits another PR had already landed, so the digest's trailer
authors, its commit count, and the squash subject disagreed with the remote.

`digest_base` is the one home for the preference: a SHA or an `origin/…` ref
passes through untouched, a bare name prefers `origin/<base>` when that ref exists
locally, and the single-ref fallback is unchanged when no base is given. Every
test below names the mutation it kills.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"

from _draft import _draft_range  # noqa: E402
from _github import _branch_subject, _digest_range_spec, digest_base  # noqa: E402

from tests.gh_helpers import run_git, write_gh_stub  # noqa: E402


def _commit(repo: Path, filename: str, content: str, message: str, who: tuple[str, str]) -> str:
    """Commit one file under `who`; return the new HEAD sha."""
    _ = (repo / filename).write_text(content, encoding="utf-8")
    _ = run_git(repo, "add", filename)
    name, email = who
    _ = run_git(
        repo,
        "-c",
        f"user.name={name}",
        "-c",
        f"user.email={email}",
        "commit",
        "-m",
        message,
    )
    return run_git(repo, "rev-parse", "HEAD").strip()


def _init(repo: Path) -> None:
    _ = subprocess.run(["git", "init", "-b", "main", str(repo)], capture_output=True, check=True)
    _ = run_git(repo, "config", "user.name", "Base Bau")
    _ = run_git(repo, "config", "user.email", "base@x.io")
    _ = run_git(repo, "config", "commit.gpgsign", "false")


def _make_stale_main_repo(repo: Path) -> None:
    """`origin/main` has landed a foreign commit; local `main` still points below it.

    Shape: base <- foreign (on `origin/main`) <- ada, bo (on `feature`). Local
    `main` stays at base, so `main..feature` counts three commits while
    `origin/main..feature` counts the two this branch actually authored.
    """
    _init(repo)
    base_sha = _commit(repo, "base.txt", "base\n", "chore: base", ("Base Bau", "base@x.io"))
    foreign_sha = _commit(
        repo, "foreign.txt", "foreign\n", "feat: foreign work", ("Foreign Fil", "foreign@x.io")
    )
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", foreign_sha)
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _ = run_git(repo, "update-ref", "refs/heads/main", base_sha)
    _ = run_git(repo, "checkout", "-b", "feature", foreign_sha)
    _ = _commit(repo, "ada.txt", "ada\n", "feat: ada work", ("Ada", "ada@x.io"))
    _ = _commit(repo, "bo.txt", "bo\n", "feat: bo work", ("Bo", "bo@x.io"))


def _make_local_main_repo(repo: Path) -> None:
    """A local `main` and a `feature` branch, with no `refs/remotes/origin/*` at all."""
    _init(repo)
    _ = _commit(repo, "base.txt", "base\n", "chore: base", ("Base Bau", "base@x.io"))
    _ = run_git(repo, "checkout", "-b", "feature")
    _ = _commit(repo, "ada.txt", "ada\n", "feat: ada work", ("Ada", "ada@x.io"))


def _mocked_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """A PATH whose `gh` answers the reads `--check` makes, plus a call log."""
    bindir = tmp_path / "bin"
    _ = write_gh_stub(
        bindir,
        """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
args="$*"
case "$args" in
  *"pulls?head="*) printf 'null\\n'; exit 0 ;;
  *"api user"*) printf 'merger-user\\n'; exit 0 ;;
  *"repo view"*) printf 'test/repo\\n'; exit 0 ;;
  *"repos/test/repo"*) printf '\\n'; exit 0 ;;
esac
echo "unexpected gh call: $*" >&2
exit 1
""",
    )
    log = tmp_path / "gh.log"
    _ = log.write_text("", encoding="utf-8")
    monkeypatch.setenv("GH_LOG", str(log))
    path = f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}"
    monkeypatch.setenv("PATH", path)
    return {**os.environ, "PATH": path, "GH_LOG": str(log)}


def _check(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--check",
            "--head",
            "feature",
            "--title",
            "feat: x",
            "--body",
            "## Summary\nReal work.\n",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def test_digest_range_forks_from_origin_main_when_local_main_is_stale(tmp_path: Path) -> None:
    """The range excludes the foreign commit and equals `git log origin/main..HEAD`.

    Mutation: drop `digest_base` from `_digest_range_spec` -> the spec stays
    `main..feature`, three commits, and the count stops matching the remote's.
    """
    repo = tmp_path / "stale-repo"
    _make_stale_main_repo(repo)

    assert len(run_git(repo, "rev-list", "main..feature").split()) == 3
    assert len(run_git(repo, "rev-list", "origin/main..feature").split()) == 2

    assert digest_base("main", cwd=repo) == "origin/main"
    assert _digest_range_spec("main", "feature", cwd=repo) == "origin/main..feature"

    resolution = _draft_range("main", "feature", cwd=repo)
    assert resolution is not None
    assert resolution.base_ref == "origin/main"
    foreign = run_git(repo, "rev-parse", "origin/main").strip()
    assert foreign not in resolution.commits
    assert resolution.counts.commits == 2


def test_check_dry_run_counts_only_this_branchs_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`pr.py --check` on the stale-main repo reports this branch's two trailers.

    Mutation: revert `_digest_range_spec` to the bare base -> the foreign author
    joins the trailer set and the count reads three.
    """
    repo = tmp_path / "stale-repo"
    _make_stale_main_repo(repo)
    env = _mocked_env(tmp_path, monkeypatch)

    res = _check(repo, env)
    assert res.returncode == 0, res.stderr
    assert "trailers: 2" in res.stdout, res.stdout
    assert "Foreign Fil" not in res.stdout


def test_digest_base_passes_a_sha_or_remote_qualified_base_through(tmp_path: Path) -> None:
    """An explicit SHA or an `origin/…` ref is the caller's naming and stays put.

    Mutation: prefix unconditionally (`return f"origin/{base}"`) -> the SHA becomes
    `origin/<sha>`, which resolves to nothing, and the range refuses.
    """
    repo = tmp_path / "stale-repo"
    _make_stale_main_repo(repo)
    sha = run_git(repo, "rev-parse", "origin/main").strip()

    assert digest_base(sha, cwd=repo) == sha
    assert digest_base(sha[:12], cwd=repo) == sha[:12]
    assert digest_base("origin/main", cwd=repo) == "origin/main"
    assert _digest_range_spec(sha, "feature", cwd=repo) == f"{sha}..feature"


def test_digest_base_keeps_the_local_name_when_no_remote_ref_exists(tmp_path: Path) -> None:
    """No `origin/<base>`: the local name is used, and nothing refuses.

    Mutation: return `origin/{base}` without probing -> an unverifiable ref, so
    `_digest_range_spec` refuses and the digest loses its commit set.
    """
    repo = tmp_path / "local-repo"
    _make_local_main_repo(repo)

    assert digest_base("main", cwd=repo) == "main"
    assert _digest_range_spec("main", "feature", cwd=repo) == "main..feature"

    resolution = _draft_range("main", "feature", cwd=repo)
    assert resolution is not None
    assert resolution.counts.commits == 1


def test_draft_range_keeps_the_single_ref_fallback_when_no_base(tmp_path: Path) -> None:
    """No base at all: the authority's own single-ref derivation still resolves.

    Mutation: build the spec list only when `base` is truthy -> `_draft_range`
    returns None and the digest drops every commit.
    """
    repo = tmp_path / "stale-repo"
    _make_stale_main_repo(repo)

    resolution = _draft_range(None, "feature", cwd=repo)
    assert resolution is not None
    assert resolution.base_ref == "origin/HEAD"
    assert resolution.counts.commits == 2


def test_digest_base_is_the_only_home_for_the_preference() -> None:
    """Both range builders call `digest_base`; neither inlines the prefix.

    Mutation: re-inline `f"origin/{base}"` in `_draft_range` -> the two consumers
    drift and the `f"{base}..{head_ref}"` assertion below fails.
    """
    sources = {p.name: p.read_text(encoding="utf-8") for p in PR_SCRIPTS.glob("*.py")}
    assert [name for name, text in sources.items() if "def digest_base(" in text] == ["_github.py"]
    assert "digest_base(" in sources["_draft.py"]
    assert 'f"{base}..{head_ref}"' not in sources["_draft.py"]
    assert 'f"{base}..{head_ref}"' not in sources["_github.py"]


# --- the title range: `_branch_subject` routes its base through `digest_base` -------------
#
# `resolve_title_and_body` derives the PR title from `_branch_subject(ref, base)`, where
# `base` is `resolve_base`'s bare branch name. A bare local `main` behind `origin/main`
# could let another PR's landed commit into the walk, so the range must fork from the
# remote-tracking ref, exactly as `_digest_range_spec` and `_draft_range` already do.
#
# `git log --first-parent --no-merges -1` walks one linear first-parent chain and always
# leads with the tip, so a foreign commit can only lead the walk when it sits on that
# chain ahead of the branch's own commits. The fixtures below put it there; a plain
# "foreign newer than the branch commits" layout cannot, because the walk is ordered by
# parentage, not by date.


def _make_foreign_leads_repo(repo: Path) -> None:
    """`origin/main` leads the branch's first-parent chain; local `main` is behind it.

    Shape: base <- foreign (on `origin/main`); base <- ada <- bo (branch work).
    `feature` starts at foreign and merges the work, so its tip merge's first parent
    is foreign. `main..feature` then leads with foreign, while
    `origin/main..feature` never admits it.
    """
    _init(repo)
    base_sha = _commit(repo, "base.txt", "base\n", "chore: base", ("Base Bau", "base@x.io"))
    foreign_sha = _commit(
        repo, "foreign.txt", "foreign\n", "feat: foreign work", ("Foreign Fil", "foreign@x.io")
    )
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", foreign_sha)
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _ = run_git(repo, "update-ref", "refs/heads/main", base_sha)
    _ = run_git(repo, "checkout", "-b", "work", base_sha)
    _ = _commit(repo, "ada.txt", "ada\n", "feat: ada work", ("Ada", "ada@x.io"))
    _ = _commit(repo, "bo.txt", "bo\n", "feat: bo work", ("Bo", "bo@x.io"))
    _ = run_git(repo, "checkout", "-b", "feature", foreign_sha)
    _ = run_git(repo, "merge", "--no-edit", "work")


def test_branch_subject_forks_from_origin_main_so_the_foreign_commit_never_leads(
    tmp_path: Path,
) -> None:
    """The derived title cannot name another PR's landed commit.

    Mutation: drop `digest_base` from `_branch_subject` -> the bare `main..feature`
    first-parent walk leads with the foreign commit and the subject becomes
    `"feat: foreign work"`.
    """
    repo = tmp_path / "foreign-leads"
    _make_foreign_leads_repo(repo)

    assert digest_base("main", cwd=repo) == "origin/main"
    assert _branch_subject("feature", "main", cwd=repo) != "feat: foreign work"
    assert _branch_subject("feature", "main", cwd=repo) == _branch_subject(
        "feature", "origin/main", cwd=repo
    )


def _make_local_base_hides_the_branch_repo(repo: Path) -> None:
    """Local `main` already holds the branch's first-parent tip; `origin/main` does not.

    Shape: base <- ada <- bo (branch work) and base <- side; `feature` merges side onto
    bo, so its tip merge's first parent is bo. Local `main` points at bo, so the bare
    `main..feature` range is empty and the fallback yields ""; `origin/main` sits at a
    separate foreign commit, so `origin/main..feature` leads with bo.
    """
    _init(repo)
    base_sha = _commit(repo, "base.txt", "base\n", "chore: base", ("Base Bau", "base@x.io"))
    _ = run_git(repo, "checkout", "-b", "work", base_sha)
    _ = _commit(repo, "ada.txt", "ada\n", "feat: ada work", ("Ada", "ada@x.io"))
    bo_sha = _commit(repo, "bo.txt", "bo\n", "feat: bo work", ("Bo", "bo@x.io"))
    _ = run_git(repo, "checkout", "-b", "side", base_sha)
    _ = _commit(repo, "side.txt", "side\n", "feat: side work", ("Side", "side@x.io"))
    _ = run_git(repo, "checkout", "-b", "feature", bo_sha)
    _ = run_git(repo, "merge", "--no-edit", "side")
    _ = run_git(repo, "checkout", "-b", "foreignbranch", base_sha)
    foreign_sha = _commit(
        repo, "foreign.txt", "foreign\n", "feat: foreign work", ("Foreign Fil", "foreign@x.io")
    )
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", foreign_sha)
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _ = run_git(repo, "update-ref", "refs/heads/main", bo_sha)


def test_branch_subject_derives_the_branch_commit_over_a_local_base_that_hides_it(
    tmp_path: Path,
) -> None:
    """The branch's own commit is the subject, not the empty fallback the bare base gives.

    Mutation: drop `digest_base` from `_branch_subject` -> the bare `main..feature`
    range is empty and the merge-tip fallback returns `""` instead of `"feat: bo work"`.
    """
    repo = tmp_path / "local-base-hides"
    _make_local_base_hides_the_branch_repo(repo)

    assert digest_base("main", cwd=repo) == "origin/main"
    assert _branch_subject("feature", "main", cwd=repo) == "feat: bo work"


def test_branch_subject_without_a_base_uses_the_head_single_ref(tmp_path: Path) -> None:
    """No base at all keeps the single-ref walk of the head's own history.

    Mutation: drop the `if base` guard so the spec becomes `None..feature` -> git
    errors and the subject collapses to `""`.
    """
    repo = tmp_path / "stale-repo"
    _make_stale_main_repo(repo)

    assert _branch_subject("feature", None, cwd=repo) == "feat: bo work"


def _make_merge_of_base_repo(repo: Path) -> None:
    """`feature`'s only commit is a merge of the base: base <- side, and feature merges it."""
    _init(repo)
    base_sha = _commit(repo, "base.txt", "base\n", "chore: base", ("Base Bau", "base@x.io"))
    _ = run_git(repo, "checkout", "-b", "side", base_sha)
    _ = _commit(repo, "side.txt", "side\n", "feat: side work", ("Side", "side@x.io"))
    _ = run_git(repo, "checkout", "-b", "feature", base_sha)
    _ = run_git(repo, "merge", "--no-ff", "--no-edit", "side")
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", base_sha)
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _ = run_git(repo, "update-ref", "refs/heads/main", base_sha)


def test_branch_subject_merge_of_the_base_still_yields_empty(tmp_path: Path) -> None:
    """A branch whose only commit is a merge of the base yields `""`, base or remote.

    Mutation: drop `--no-merges` -> the tip merge's own subject leaks into the title.
    """
    repo = tmp_path / "merge-of-base"
    _make_merge_of_base_repo(repo)

    assert _branch_subject("feature", "main", cwd=repo) == ""
    assert _branch_subject("feature", "origin/main", cwd=repo) == ""
