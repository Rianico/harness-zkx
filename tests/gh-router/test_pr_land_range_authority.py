"""pr-land --check derives squash trailers from the shared range authority.

Regression: on a repo whose default branch is NOT main (trunk), the --check
dry run must attribute every commit in the digest's range -- not just the
single head commit the old ``origin/main..head`` -> ``main..head`` -> ``-1``
chain degraded to when no main ref exists.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
LIB_DIR = REPO_ROOT / "skills/gh-router/lib"


from _errors import RefusalError  # noqa: E402
from _github import resolve_base  # noqa: E402
from _squash import pr_co_author_trailers  # noqa: E402
from range_authority import resolve_range  # noqa: E402

from tests.gh_helpers import run_git, write_gh_stub  # noqa: E402


def _make_trunk_repo(repo: Path) -> None:
    """Synthetic repo: default branch trunk, origin/trunk refs, no main refs."""
    _ = subprocess.run(["git", "init", "-b", "trunk", str(repo)], capture_output=True, check=True)
    _ = run_git(repo, "config", "user.name", "Trunk Synthetic")
    _ = run_git(repo, "config", "user.email", "synthetic@x.io")
    _ = run_git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = run_git(repo, "add", "base.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Base Bau",
        "-c",
        "user.email=base@x.io",
        "commit",
        "-m",
        "chore: trunk base",
    )
    trunk_sha = run_git(repo, "rev-parse", "HEAD").strip()
    _ = run_git(repo, "update-ref", "refs/remotes/origin/trunk", trunk_sha)
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk")
    _ = run_git(repo, "checkout", "-b", "feature")
    _ = (repo / "ada.txt").write_text("ada\n", encoding="utf-8")
    _ = run_git(repo, "add", "ada.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Ada",
        "-c",
        "user.email=ada@x.io",
        "commit",
        "-m",
        "feat: ada work",
    )
    _ = (repo / "bo.txt").write_text("bo\n", encoding="utf-8")
    _ = run_git(repo, "add", "bo.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Bo",
        "-c",
        "user.email=bo@x.io",
        "commit",
        "-m",
        "feat: bo work",
    )


def _no_main_refs(repo: Path) -> None:
    for ref in ("refs/heads/main", "refs/remotes/origin/main", "refs/heads/master"):
        probe = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", "-q", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        assert probe.returncode != 0, f"fixture leaked ref {ref}"


def _make_gh_mock(bindir: Path) -> Path:
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
    return bindir


def _wraprun_git(bindir: Path, git_log: Path) -> None:
    """Shadow `git` with an argv-logging shim that delegates to the real binary."""
    real_git = shutil.which("git")
    assert real_git is not None
    git = bindir / "git"
    _ = git.write_text(
        f"""#!/usr/bin/env bash
echo "$@" >> "{git_log}"
exec "{real_git}" "$@"
""",
        encoding="utf-8",
    )
    git.chmod(0o755)


def _make_master_only_repo(repo: Path) -> None:
    """Synthetic repo: only refs/remotes/origin/master, no origin/HEAD."""
    _ = subprocess.run(["git", "init", "-b", "master", str(repo)], capture_output=True, check=True)
    _ = run_git(repo, "config", "user.name", "Master Synthetic")
    _ = run_git(repo, "config", "user.email", "synthetic@x.io")
    _ = run_git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = run_git(repo, "add", "base.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Base Bau",
        "-c",
        "user.email=base@x.io",
        "commit",
        "-m",
        "chore: master base",
    )
    master_sha = run_git(repo, "rev-parse", "HEAD").strip()
    _ = run_git(repo, "update-ref", "refs/remotes/origin/master", master_sha)
    _ = run_git(repo, "checkout", "-b", "feature")
    _ = (repo / "work.txt").write_text("work\n", encoding="utf-8")
    _ = run_git(repo, "add", "work.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Wren",
        "-c",
        "user.email=wren@x.io",
        "commit",
        "-m",
        "feat: wren work",
    )


def _make_no_candidate_repo(repo: Path) -> None:
    """Synthetic repo: no origin/HEAD, no origin/main, no origin/master."""
    _ = subprocess.run(["git", "init", "-b", "trunk", str(repo)], capture_output=True, check=True)
    _ = run_git(repo, "config", "user.name", "No Candidate")
    _ = run_git(repo, "config", "user.email", "synthetic@x.io")
    _ = run_git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = run_git(repo, "add", "base.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Base Bau",
        "-c",
        "user.email=base@x.io",
        "commit",
        "-m",
        "chore: trunk base",
    )
    _ = run_git(repo, "checkout", "-b", "feature")
    _ = (repo / "solo.txt").write_text("solo\n", encoding="utf-8")
    _ = run_git(repo, "add", "solo.txt")
    _ = run_git(
        repo,
        "-c",
        "user.name=Solo",
        "-c",
        "user.email=solo@x.io",
        "commit",
        "-m",
        "feat: solo work",
    )


def test_resolve_base_prefers_origin_head_over_literal_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """resolve_base follows origin/HEAD first (pre-existing behaviour, not the guard)."""
    repo = tmp_path / "trunk-repo"
    _make_trunk_repo(repo)
    _no_main_refs(repo)
    bindir = _make_gh_mock(tmp_path / "bin")
    log = tmp_path / "gh.log"
    _ = log.write_text("", encoding="utf-8")
    monkeypatch.setenv("GH_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    assert resolve_base(None, "test/repo", cwd=repo) == "trunk"


def test_check_dry_run_trailers_equal_digest_commit_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--check trailers on a trunk repo equal the digest's commit set.

    The digest (``resolve_range("feature", "..")``) sees both feature
    commits; the old ``-1`` fallback would attribute only the head commit,
    so the trailer set must hold two authors, matching the digest exactly.
    """
    repo = tmp_path / "trunk-repo"
    _make_trunk_repo(repo)
    _no_main_refs(repo)
    bindir = _make_gh_mock(tmp_path / "bin")
    log = tmp_path / "gh.log"
    _ = log.write_text("", encoding="utf-8")
    git_log = tmp_path / "git.log"
    _ = git_log.write_text("", encoding="utf-8")
    _wraprun_git(bindir, git_log)

    monkeypatch.chdir(repo)
    resolution = resolve_range("feature", "..")
    assert resolution.base_ref == "origin/HEAD"
    assert len(resolution.commits) == 2
    expected: set[str] = set()
    for sha in resolution.commits:
        out = run_git(repo, "show", "-s", "--format=%an%x00%ae", sha).strip()
        name, email = out.split("\x00")
        expected.add(f"Co-authored-by: {name} <{email}>")
    assert expected == {
        "Co-authored-by: Ada <ada@x.io>",
        "Co-authored-by: Bo <bo@x.io>",
    }

    env = {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
        "GH_LOG": str(log),
    }
    res = subprocess.run(
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
    assert res.returncode == 0, res.stderr
    assert "trailers: 2" in res.stdout, res.stdout
    # Trailer identity, not just the count: the same digest rows rendered through
    # the real trailer builder must equal the digest commit set exactly (the gh
    # login column is a gh-only datum and plays no part in the trailer text).
    rows = []
    for line in sorted(expected):
        name_email = line.split(": ", 1)[1]
        name, _, email = name_email.rpartition(" <")
        rows.append(f"\t{name}\t{email.rstrip('>')}")
    digest_tsv = "\n".join(rows)
    assert set(pr_co_author_trailers(digest_tsv).splitlines()) == expected
    # CLI-level tie: the subprocess itself must have asked git log for a range
    # headed by the feature branch. A `-1`-fallback CLI (or one deriving trailers
    # from a rangeless query) logs no such argv, so this fails without the tie.
    logged = git_log.read_text(encoding="utf-8").splitlines()
    assert any(
        "log" in line.split()
        and any(".." in token and token.endswith("feature") for token in line.split())
        for line in logged
    ), "\n".join(logged)
    # stdout stays small: the trailer lines live behind the gate, never on the console.
    assert "Co-authored-by" not in res.stdout


def _mocked_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, repo: Path) -> dict[str, str]:
    bindir = _make_gh_mock(tmp_path / "bin")
    log = tmp_path / "gh.log"
    _ = log.write_text("", encoding="utf-8")
    monkeypatch.setenv("GH_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    return {
        **os.environ,
        "PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}",
        "GH_LOG": str(log),
    }


def test_resolve_base_prefers_origin_master_without_origin_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No origin/HEAD + origin/master only resolves to master, never literal main."""
    repo = tmp_path / "master-repo"
    _make_master_only_repo(repo)
    _ = _mocked_env(tmp_path, monkeypatch, repo)
    assert resolve_base(None, "test/repo", cwd=repo) == "master"


def test_resolve_base_refuses_with_no_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No origin/HEAD/main/master raises naming the range authority."""
    repo = tmp_path / "no-candidate-repo"
    _make_no_candidate_repo(repo)
    _ = _mocked_env(tmp_path, monkeypatch, repo)
    with pytest.raises(RefusalError, match="git-diff-digest range authority"):
        _ = resolve_base(None, "test/repo", cwd=repo)


def test_check_dry_run_refuses_loudly_with_no_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--check with no resolvable base exits 1 with the refusal, not a lone author."""
    repo = tmp_path / "no-candidate-repo"
    _make_no_candidate_repo(repo)
    env = _mocked_env(tmp_path, monkeypatch, repo)
    res = subprocess.run(
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
    assert res.returncode == 1, res.stdout
    assert "cannot resolve PR base" in res.stderr
    assert "Co-authored-by" not in res.stdout


def test_dangling_origin_head_falls_through_to_origin_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """origin/HEAD naming a missing branch is treated as absent."""
    repo = tmp_path / "dangling-repo"
    _make_trunk_repo(repo)
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/gone")
    _ = _mocked_env(tmp_path, monkeypatch, repo)
    assert resolve_base(None, "test/repo", cwd=repo) == "main"
