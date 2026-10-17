"""Push precondition and stamp recovery for pr-land (#266-t1).

Two defects break a re-run from a partially-completed state: `create_or_reuse_pr`
queries the PR API before anything pushes the branch (so creating a PR on an
unpushed branch fails), and `stamp_changelog` returns early when `(#N)` is
already present even though the stamp commit never reached the remote. These
tests pin the repair: the creation path pushes first, and a re-run after a
failed stamp push repairs the remote instead of returning early.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _github as github_mod  # noqa: E402
import pr as pr_mod  # noqa: E402
from pr import PrError, RefusalError, create_or_reuse_pr, stamp_changelog  # noqa: E402


class _PushFake:
    """Stub `_github.run_command` for the creation push precondition.

    Serves the config/remote/rev-parse/rev-list reads the precondition makes,
    records every argv, and answers the PR list/create calls with a fresh PR #7.
    `remote_exists` controls `refs/remotes/origin/feat-x`; `ahead`/`behind` are
    the rev-list counts; `push_rc` makes `git push` fail when non-zero.
    """

    def __init__(
        self,
        *,
        remote_exists: bool = True,
        ahead: int = 0,
        behind: int = 0,
        push_rc: int = 0,
    ) -> None:
        self.calls: list[list[str]] = []
        self.remote_exists = remote_exists
        self.ahead = ahead
        self.behind = behind
        self.push_rc = push_rc

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        joined = " ".join(cmd)
        out, err, rc = "", "", 0
        if cmd[:2] == ["git", "push"]:
            rc = self.push_rc
            err = "rejected: fetch first\n" if rc != 0 else ""
        elif "config --get branch." in joined:
            rc = 1
        elif "remote get-url" in joined:
            out = "https://github.com/test/repo.git\n"
        elif "rev-parse --verify" in joined:
            if self.remote_exists:
                out = "0123456789abcdef\n"
            else:
                rc = 1
                err = "unknown revision\n"
        elif "rev-list --left-right --count" in joined:
            out = f"{self.behind}\t{self.ahead}\n"
        elif "pulls?head=" in joined:
            out = "null\n"
        elif "pulls -X POST" in joined:
            out = "7\n"
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _create_kwargs() -> dict[str, object]:
    return {
        "repo": "test/repo",
        "head_ref": "feat-x",
        "base": "main",
        "title": "feat: x",
        "body": "## Summary\nReal.\n",
        "title_supplied": True,
        "body_supplied": True,
    }


def _push_calls(fake: _PushFake) -> list[list[str]]:
    return [c for c in fake.calls if c[:2] == ["git", "push"]]


def _post_calls(fake: _PushFake) -> list[list[str]]:
    return [c for c in fake.calls if "pulls -X POST" in " ".join(c)]


def test_creation_pushes_when_remote_ref_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A missing remote ref pushes before the PR create, so the API sees the head."""
    monkeypatch.chdir(tmp_path)
    fake = _PushFake(remote_exists=False)
    monkeypatch.setattr(github_mod, "run_command", fake)

    num, _, _, created = create_or_reuse_pr(**_create_kwargs())  # type: ignore[arg-type]

    assert (num, created) == ("7", True)
    pushes = _push_calls(fake)
    posts = _post_calls(fake)
    assert pushes == [["git", "push", "origin", "feat-x"]]
    assert len(posts) == 1
    push_idx = fake.calls.index(pushes[0])
    post_idx = fake.calls.index(posts[0])
    assert push_idx < post_idx


def test_creation_pushes_when_remote_behind_and_skips_when_in_sync(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Local-only commits push; an in-sync branch creates the PR with no push."""
    monkeypatch.chdir(tmp_path)

    behind_fake = _PushFake(remote_exists=True, ahead=3, behind=0)
    monkeypatch.setattr(github_mod, "run_command", behind_fake)
    num, _, _, created = create_or_reuse_pr(**_create_kwargs())  # type: ignore[arg-type]
    assert (num, created) == ("7", True)
    assert _push_calls(behind_fake) == [["git", "push", "origin", "feat-x"]]
    assert len(_post_calls(behind_fake)) == 1

    sync_fake = _PushFake(remote_exists=True, ahead=0, behind=0)
    monkeypatch.setattr(github_mod, "run_command", sync_fake)
    num, _, _, created = create_or_reuse_pr(**_create_kwargs())  # type: ignore[arg-type]
    assert (num, created) == ("7", True)
    assert _push_calls(sync_fake) == []
    assert len(_post_calls(sync_fake)) == 1


def test_creation_refuses_on_divergence_without_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Remote-ahead history refuses with the remediation and runs no push and no create."""
    monkeypatch.chdir(tmp_path)
    fake = _PushFake(remote_exists=True, ahead=1, behind=2)
    monkeypatch.setattr(github_mod, "run_command", fake)

    with pytest.raises(RefusalError):
        create_or_reuse_pr(**_create_kwargs())  # type: ignore[arg-type]

    assert _push_calls(fake) == []
    assert _post_calls(fake) == []
    err = capsys.readouterr().err
    assert "remediation:" in err
    assert "force" in err.lower()


def test_creation_refuses_when_push_fails_before_create(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failed precondition push is non-zero with no mutation: no PR is created."""
    monkeypatch.chdir(tmp_path)
    fake = _PushFake(remote_exists=False, push_rc=1)
    monkeypatch.setattr(github_mod, "run_command", fake)

    with pytest.raises(PrError):
        create_or_reuse_pr(**_create_kwargs())  # type: ignore[arg-type]
    assert _push_calls(fake) == [["git", "push", "origin", "feat-x"]]
    assert _post_calls(fake) == []


def _make_check_repo(base: Path) -> Path:
    """Synthetic repo: main + origin/main + feat-x with one commit (no remotes)."""
    repo = base / "repo"
    _ = repo.mkdir(parents=True)

    def git(*args: str) -> None:
        _ = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            check=True,
            env=git_env(),
        )

    _ = subprocess.run(
        ["git", "init", "-b", "main", str(repo)], capture_output=True, check=True, env=git_env()
    )
    git("config", "user.name", "Push Stamp Synthetic")
    git("config", "user.email", "synthetic@x.io")
    git("config", "commit.gpgsign", "false")
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    git("add", "base.txt")
    git("commit", "-m", "chore: base")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git("checkout", "-b", "feat-x")
    _ = (repo / "work.txt").write_text("work\n", encoding="utf-8")
    git("add", "work.txt")
    git("commit", "-m", "feat: work")
    return repo


def test_check_path_never_pushes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--check performs no push: the push helper is never invoked and no push runs."""
    repo = _make_check_repo(tmp_path)
    push_helper_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    calls: list[list[str]] = []
    real_run = github_mod.run_command

    def _spy_push(*args: object, **kwargs: object) -> None:
        push_helper_calls.append((args, kwargs))
        raise AssertionError("read-only --check must never invoke the push helper")

    def _fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        if cmd[:2] == ["git", "push"]:
            raise AssertionError("read-only --check must never push")
        joined = " ".join(cmd)
        if joined.startswith("git config --get branch."):
            return subprocess.CompletedProcess(cmd, 1, "", "")
        if joined.startswith("git remote get-url"):
            return subprocess.CompletedProcess(cmd, 0, "https://github.com/test/repo.git\n", "")
        if cmd[0] == "git":
            return real_run(cmd, **kwargs)
        out, err, rc = "", "", 0
        if "config --get branch." in joined:
            rc = 1
        elif "remote get-url" in joined:
            out = "https://github.com/test/repo.git\n"
        elif "default_branch" in joined:
            out = "main\n"
        elif "pulls?head=" in joined:
            out = "null\n"
        elif "api user" in joined:
            out = "merger-user\n"
        return subprocess.CompletedProcess(cmd, rc, out, err)

    monkeypatch.setattr(github_mod, "ensure_branch_pushed", _spy_push)
    monkeypatch.setattr(github_mod, "run_command", _fake)
    monkeypatch.chdir(repo)

    rc = pr_mod.main(
        ["--head", "feat-x", "--title", "feat: x", "--body", "## Summary\nReal.\n", "--check"]
    )

    _ = capsys.readouterr()
    assert rc == 0, calls
    assert push_helper_calls == []
    assert [c for c in calls if c[:2] == ["git", "push"]] == []


def test_remote_branch_exists_honours_non_origin_remote(tmp_path: Path) -> None:
    """_remote_branch_exists resolves a non-origin remote instead of hardcoding origin."""
    upstream = tmp_path / "upstream.git"
    _ = subprocess.run(
        ["git", "init", "--bare", str(upstream)], check=True, capture_output=True, env=git_env()
    )
    repo = tmp_path / "repo"
    _ = subprocess.run(
        ["git", "init", "-b", "main", str(repo)],
        check=True,
        capture_output=True,
        env=git_env(),
    )
    env = git_env()
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Tester"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "tester@example.com"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    _ = subprocess.run(
        ["git", "-C", str(repo), "add", "README.md"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "chore: initial"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "upstream", str(upstream)],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "checkout", "-b", "feat-x"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "push", "-u", "upstream", "feat-x"],
        check=True,
        capture_output=True,
        env=env,
    )

    remote = github_mod.repo_remote_for_ref("feat-x", cwd=repo)
    assert remote == "upstream"
    assert github_mod._remote_branch_exists("feat-x", cwd=repo, remote=remote) is True
    assert github_mod._remote_branch_exists("feat-x", cwd=repo) is False


def _make_stamp_repo(base: Path) -> tuple[Path, Path]:
    """Bare remote + repo with feat-x pushed; CHANGELOG carries an attributed entry."""
    remote = base / "remote.git"
    _ = subprocess.run(
        ["git", "init", "--bare", str(remote)], check=True, capture_output=True, env=git_env()
    )
    repo = base / "repo"
    _ = repo.mkdir()
    env = git_env()

    def git(*args: str) -> None:
        _ = subprocess.run(
            ["git", "-C", str(repo), *args], check=True, capture_output=True, env=env
        )

    _ = subprocess.run(
        ["git", "init", "-b", "main", str(repo)], check=True, capture_output=True, env=env
    )
    git("config", "user.name", "Tester")
    git("config", "user.email", "tester@example.com")
    git("config", "commit.gpgsign", "false")
    _ = (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    git("add", "README.md")
    git("commit", "-m", "chore: initial")
    git("remote", "add", "origin", str(remote))
    git("push", "-u", "origin", "main")
    git("checkout", "-b", "feat-x")
    git("push", "-u", "origin", "feat-x")
    return repo, remote


def test_stamp_recovery_pushes_stranded_commit(tmp_path: Path) -> None:
    """An attributed entry with a stranded local commit pushes on re-run, then is a no-op."""
    repo, _ = _make_stamp_repo(tmp_path)
    env = git_env()
    changelog = repo / "CHANGELOG.md"
    _ = changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** entry (#7)\n",
        encoding="utf-8",
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "add", "CHANGELOG.md"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "chore(changelog): attribute #7"],
        check=True,
        capture_output=True,
        env=env,
    )

    assert stamp_changelog("feat-x", "7", cwd=repo) is True

    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    tracked = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "refs/remotes/origin/feat-x"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    assert tracked == head
    assert changelog.read_text(encoding="utf-8").count("(#7)") == 1


def test_stamp_recovery_stays_noop_when_in_sync(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An attributed entry on an in-sync branch stays a no-op with no push."""
    repo, _ = _make_stamp_repo(tmp_path)
    env = git_env()
    changelog = repo / "CHANGELOG.md"
    _ = changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** entry (#7)\n",
        encoding="utf-8",
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "add", "CHANGELOG.md"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "chore(changelog): attribute #7"],
        check=True,
        capture_output=True,
        env=env,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "push", "origin", "feat-x"],
        check=True,
        capture_output=True,
        env=env,
    )

    calls: list[list[str]] = []
    real_run = github_mod.run_command

    def _recording(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(github_mod, "run_command", _recording)

    assert stamp_changelog("feat-x", "7", cwd=repo) is False
    assert [c for c in calls if c[:2] == ["git", "push"]] == []
