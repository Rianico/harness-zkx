"""`pr.py --check` guards the squash subject where the token can read it.

`squash_merge_commit_title` is permission-gated: CI's `contents: read` token, and a
contributor's token, see the field absent — the same reduced object an anonymous read
gets. A workflow step cannot fix that without a new credential, so the guard moved into
`--check`, where the operator's token runs. A readable value that is not `PR_TITLE`
refuses; an unreadable one prints one advisory line and continues; `PR_TITLE` is silent.

Every case patches `_github.run_command` (the single seam) and drives `pr.py --check`
in process: nothing shells out to `gh`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import _github as github_mod  # noqa: E402
import pr as pr_mod  # noqa: E402
import pytest

WANTED = "PR_TITLE"
WRONG = "COMMIT_OR_PR_TITLE"
BODY = "## Summary\ncurated landing body\n\nCloses #7\n"
ADVISORY = (
    "squash_merge_commit_title unreadable (token lacks repository settings); "
    "the PR title is graded as the squash subject"
)
REMEDY = "gh api -X PATCH repos/test/repo -f squash_merge_commit_title=PR_TITLE"


class _FakeRun:
    """Stub `_github.run_command`: the squash-setting read plus the minimum a with-body
    `--check` needs.

    `squash_setting` is what the read returns; `squash_rc` models a token that cannot
    read repository settings at all (a non-zero `gh api`).
    """

    def __init__(self, *, squash_setting: str = WANTED, squash_rc: int = 0) -> None:
        self.calls: list[list[str]] = []
        self.squash_setting = squash_setting
        self.squash_rc = squash_rc

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        joined = " ".join(cmd)
        out, err, rc = "", "", 0
        if "rev-parse --abbrev-ref" in joined:
            out = "feat-x\n"
        elif ".squash_merge_commit_title" in joined:
            rc = self.squash_rc
            out = f"{self.squash_setting}\n" if self.squash_setting else ""
            err = "gh: Not Found (HTTP 404)\n" if rc else ""
        elif "pulls?head=" in joined:
            out = "null\n"
        elif "remote get-url" in joined:
            out = "https://github.com/test/repo.git\n"
        elif "default_branch" in joined:
            out = "main\n"
        elif "rev-parse HEAD" in joined:
            out = "abc123\n"
        elif "git log" in joined:
            out = "\tAuthor\tauthor@x.io\n"
        elif "api user" in joined:
            out = "merger\n"
        elif "config user.email" in joined:
            out = "merger@x.io\n"
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _run_check(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fake: _FakeRun) -> int:
    monkeypatch.setattr(github_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)
    return pr_mod.main(["--check", "--head", "feat-x", "--title", "feat: x", "--body", BODY])


def test_check_refuses_a_readable_wrong_squash_setting(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A readable setting that is not `PR_TITLE` refuses (exit 1) with the exact remedy.

    Mutation: drop the `_github.check_squash_setting(repo)` call from the `--check` path
    -> the run reaches the draft phase, so the exit code is 0, no `squash_setting`
    refusal is printed, and `commits:` appears on stdout.
    """
    fake = _FakeRun(squash_setting=WRONG)

    rc = _run_check(monkeypatch, tmp_path, fake)

    captured = capsys.readouterr()
    assert rc == 1, (captured.out, captured.err)
    assert '"code": "squash_setting"' in captured.out
    assert '"site": "test/repo"' in captured.out
    assert "squash_merge_commit_title" in captured.out
    assert WRONG in captured.out, "the refusal must name the actual value"
    assert REMEDY in captured.out
    assert "commits:" not in captured.out, "the guard runs before the draft phase"


def _unreadable_fake(shape: str) -> _FakeRun:
    """A fake whose squash-setting read is unreadable in one of three shapes.

    `empty` is the permission-gated reduced object (a successful read that prints
    nothing), `null` is a literal JSON `null` on stdout, and `failed` is a non-zero
    `gh api`.
    """
    if shape == "failed":
        return _FakeRun(squash_rc=1)
    return _FakeRun(squash_setting="" if shape == "empty" else "null")


@pytest.mark.parametrize("unreadable", ["empty", "null", "failed"])
def test_check_advises_and_proceeds_when_the_setting_is_unreadable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    unreadable: str,
) -> None:
    """An unreadable setting prints one advisory line and `--check` continues (exit 0).

    Covers all three unreadable shapes: a successful read that returns nothing (the
    permission-gated reduced object), a successful read of a literal JSON `null`, and a
    failed read.

    Mutation: make the advisory a refusal -> a contributor's token, or CI's
    `contents: read` token, blocks every run instead of printing one line. Reading a
    literal `null` as a value instead of as unreadable fires the refusal path, so this
    case's exit code turns 1 and the advisory disappears.
    """
    fake = _unreadable_fake(unreadable)

    rc = _run_check(monkeypatch, tmp_path, fake)

    captured = capsys.readouterr()
    assert rc == 0, (captured.out, captured.err)
    assert ADVISORY in captured.err
    assert "commits:" in captured.out, "the draft phase still runs"
    assert github_mod.read_squash_setting("test/repo") is None, "null reads as unreadable too"
    assert '"code": "squash_setting"' not in captured.out


def test_check_is_silent_when_the_setting_is_the_pr_title(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`PR_TITLE` produces no advisory and no refusal.

    Mutation: print the advisory unconditionally -> the correct setting still speaks on
    every run.
    """
    fake = _FakeRun(squash_setting=WANTED)

    rc = _run_check(monkeypatch, tmp_path, fake)

    captured = capsys.readouterr()
    assert rc == 0, (captured.out, captured.err)
    assert "squash_merge_commit_title" not in captured.err
    assert "unreadable" not in captured.err
    reads = [c for c in fake.calls if ".squash_merge_commit_title" in " ".join(c)]
    assert len(reads) == 1, "the guard reads the setting exactly once"

    assert "commits:" in captured.out


def test_reader_returns_none_on_a_failed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """`read_squash_setting` answers None for a failed read, not a stale value."""
    fake = _FakeRun(squash_rc=1)
    monkeypatch.setattr(github_mod, "run_command", fake)
    assert github_mod.read_squash_setting("test/repo") is None
