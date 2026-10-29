"""`pr.py --sync`: merge the base into the head, hand a stopped merge to pr-conflict.

The session defect these pin: a hand `git merge` plus a hand conflict resolution was
cheaper than the governed path. One command now merges, pushes a clean result, and on
a stop prints the dual-intent report before any file is edited.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"


import _github as github_mod  # noqa: E402
import _status as status_mod  # noqa: E402
import _sync as sync_mod  # noqa: E402
import pr as pr_mod  # noqa: E402
from _errors import RefusalError  # noqa: E402
from _sync import run_sync  # noqa: E402


class _SyncFake:
    """Stub `_github.run_command` for the sync flow: canonical order, recorded argv.

    `behind` is the base-vs-head count, `merge_rc` decides clean versus stopped,
    `unmerged` is the conflicted path list the stopped merge leaves behind, and
    `in_progress` names a stopped operation ref (`MERGE_HEAD`, …) that holds the tree.
    """

    def __init__(
        self,
        *,
        behind: int = 3,
        merge_rc: int = 0,
        unmerged: tuple[str, ...] = (),
        in_progress: tuple[str, ...] = (),
        ahead: int = 1,
        push_rc: int = 0,
    ) -> None:
        self.calls: list[list[str]] = []
        self.behind = behind
        self.merge_rc = merge_rc
        self.unmerged = unmerged
        self.in_progress = in_progress
        self.ahead = ahead
        self.push_rc = push_rc

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        joined = " ".join(cmd)
        out, err, rc = "", "", 0
        if cmd[0] == sys.executable or "extract_conflict_context.py" in joined:
            out = "conflicted files: 2\nCHANGELOG.md  marker  3 hunks\n"
        elif "--show-toplevel" in joined:
            out = "/tmp/repo\n"
        elif "rev-parse -q --verify" in joined:
            rc = 0 if cmd[-1] in self.in_progress else 1
        elif "--git-path" in joined:
            out = f".git/{cmd[-1]}\n"
        elif "config --get branch." in joined:
            rc = 1
        elif "rev-parse --verify" in joined:
            out = "0123456789abcdef\n"
        elif cmd[:2] == ["git", "fetch"]:
            out = ""
        elif "rev-list --count HEAD.." in joined:
            out = f"{self.behind}\n"
        elif cmd[:2] == ["git", "merge"]:
            rc = self.merge_rc
            err = "CONFLICT (content): Merge conflict in CHANGELOG.md\n" if rc else ""
        elif "diff --name-only --diff-filter=U" in joined:
            out = "".join(f"{path}\n" for path in self.unmerged)
        elif "rev-list --left-right --count" in joined:
            out = f"0\t{self.ahead}\n"
        elif cmd[:2] == ["git", "push"]:
            rc = self.push_rc
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _commands(fake: _SyncFake) -> list[str]:
    return [" ".join(call) for call in fake.calls]


def test_sync_merges_the_base_and_pushes_the_head(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = _SyncFake(behind=3, ahead=1)
    monkeypatch.setattr(github_mod, "run_command", fake)

    assert run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo")) == 0

    commands = _commands(fake)
    assert "git merge --no-edit origin/main" in commands
    assert "git push origin feat-x" in commands
    assert "synced feat-x with origin/main (3 commit(s))" in capsys.readouterr().err


def test_a_stopped_merge_prints_the_dual_intent_report_before_any_edit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = _SyncFake(behind=2, merge_rc=1, unmerged=("CHANGELOG.md", "AGENTS.md"))
    monkeypatch.setattr(github_mod, "run_command", fake)

    with pytest.raises(RefusalError) as excinfo:
        run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo"))

    assert excinfo.value.refusals[0]["code"] == "sync_conflict"
    assert excinfo.value.transitions[0]["command"] == "pr.py --sync"
    commands = _commands(fake)
    helper = [call for call in fake.calls if "extract_conflict_context.py" in " ".join(call)]
    assert helper and helper[0][-1] == "--all"
    assert "git push origin feat-x" not in commands
    captured = capsys.readouterr()
    assert "conflicted files: 2" in captured.out, "the report must be printed, not summarized"
    assert "sync stopped on conflicts in 2 path(s)" in captured.err


def test_an_already_current_head_runs_no_merge(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = _SyncFake(behind=0, ahead=0)
    monkeypatch.setattr(github_mod, "run_command", fake)

    assert run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo")) == 0

    commands = _commands(fake)
    assert not any(command.startswith("git merge") for command in commands)
    assert "git push origin feat-x" not in commands
    assert "already current with origin/main" in capsys.readouterr().err


def test_a_stopped_operation_refuses_before_any_fetch(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = _SyncFake(in_progress=("MERGE_HEAD",))
    monkeypatch.setattr(github_mod, "run_command", fake)

    with pytest.raises(RefusalError) as excinfo:
        run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo"))

    assert excinfo.value.refusals[0]["code"] == "sync_in_progress"
    assert not any(call[:2] == ["git", "fetch"] for call in fake.calls)
    captured = capsys.readouterr()
    assert "refusing to sync: a merge is already in progress" in captured.err
    assert "extract_conflict_context.py" in captured.err


def test_missing_helper_still_refuses_with_the_pointer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = _SyncFake(behind=1, merge_rc=1, unmerged=("CHANGELOG.md",))
    monkeypatch.setattr(github_mod, "run_command", fake)
    monkeypatch.setattr(sync_mod, "HELPER_SCRIPT", Path("/nonexistent/extract_conflict_context.py"))

    with pytest.raises(RefusalError):
        run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo"))

    err = capsys.readouterr().err
    assert "conflict helper missing" in err
    assert github_mod.CONFLICT_HELPER in err


def test_a_failed_merge_without_conflicts_is_an_error_not_a_refusal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _SyncFake(behind=1, merge_rc=1, unmerged=())
    monkeypatch.setattr(github_mod, "run_command", fake)

    with pytest.raises(Exception) as excinfo:
        run_sync(head_ref="feat-x", base="main", cwd=Path("/tmp/repo"))

    assert not isinstance(excinfo.value, RefusalError)
    assert "CONFLICT (content)" in str(excinfo.value)


def test_sync_is_its_own_phase() -> None:
    assert pr_mod.parse_args(["--sync"]).sync is True
    assert pr_mod.main(["--sync", "--merge"]) == 2
    assert pr_mod.main(["--sync", "--watch"]) == 2
    assert pr_mod.main(["--sync", "--status"]) == 2


def test_status_offers_the_sync_transition_when_the_head_is_behind() -> None:
    transitions = status_mod.build_transitions(
        head_ref="feat-x",
        remote="origin",
        repo="test/repo",
        pr_number="7",
        pr_state="open",
        pr_draft=False,
        body_state="ready",
        body_path=".lsz/gh-router/feat-x.md",
        branch_pushed=True,
        failure_states=[],
        worktree_clean=True,
        merge_verdict="behind",
    )

    sync = [entry for entry in transitions if entry.command == "pr.py --sync"]
    assert len(sync) == 1, "a behind head has exactly one sync transition"
    assert sync[0].mutation == "local"
    assert sync[0].preconditions == ["worktree_clean"]
