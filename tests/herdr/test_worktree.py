"""Tests for skills/herdr/scripts/herdr_worktree.py (herdr-worktree helper).

The helper shells out to `wt` and `git`; every test replaces the module-level `run`
seam so no process is spawned. Worktrunk presence is controlled through `PATH`.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import herdr_cli
import herdr_worktree as hw
import pytest
import yaml

Handler = Callable[[list[str], dict[str, str]], subprocess.CompletedProcess[str]]
Calls = list[tuple[list[str], dict[str, str]]]


def completed(
    argv: Sequence[str], returncode: int = 0, stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(list(argv), returncode, stdout, stderr)


def env_with_wt(tmp_path: Path) -> dict[str, str]:
    """A PATH that resolves a (never executed) `wt` binary."""
    bin_dir = tmp_path / "bin-wt"
    bin_dir.mkdir(exist_ok=True)
    wt = bin_dir / "wt"
    _ = wt.write_text("#!/bin/sh\nexit 0\n")
    wt.chmod(wt.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return {"PATH": str(bin_dir)}


def env_without_wt(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin-empty"
    bin_dir.mkdir(exist_ok=True)
    return {"PATH": str(bin_dir)}


def patch_runner(monkeypatch: pytest.MonkeyPatch, handler: Handler) -> Calls:
    """Replace the module `run` seam and record every (argv, env) pair."""
    calls: Calls = []

    def run(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
        argv_list = [str(arg) for arg in argv]
        env_map = dict(env)
        calls.append((argv_list, env_map))
        return handler(argv_list, env_map)

    monkeypatch.setattr(hw, "run", run)
    return calls


def test_parse_wt_list_schema1_bare_array() -> None:
    raw = json.dumps(
        [{"branch": "main", "path": "/repo"}, {"branch": "feat/x", "path": "/repo.feat-x"}]
    )
    assert hw.parse_wt_list(raw) == [
        hw.Worktree(branch="main", path="/repo"),
        hw.Worktree(branch="feat/x", path="/repo.feat-x"),
    ]


def test_parse_wt_list_schema2_items_object() -> None:
    raw = json.dumps({"schema": 2, "items": [{"branch": "feat/y", "path": "/w"}]})
    assert hw.parse_wt_list(raw) == [hw.Worktree(branch="feat/y", path="/w")]


def test_parse_wt_list_skips_entries_without_branch() -> None:
    raw = json.dumps([{"path": "/detached"}, {"branch": "main", "path": "/repo"}])
    assert hw.parse_wt_list(raw) == [hw.Worktree(branch="main", path="/repo")]


def test_parse_wt_list_rejects_non_json() -> None:
    with pytest.raises(hw.WorktreeError):
        _ = hw.parse_wt_list("not json")


def test_parse_wt_list_rejects_unknown_schema() -> None:
    with pytest.raises(hw.WorktreeError):
        _ = hw.parse_wt_list(json.dumps({"schema": 2}))


def test_parse_git_worktree_list_porcelain() -> None:
    raw = (
        "worktree /repo\nHEAD abc\nbranch refs/heads/main\n\n"
        "worktree /repo.feat\nHEAD def\nbranch refs/heads/feat/x\n"
    )
    assert hw.parse_git_worktree_list(raw) == [
        hw.Worktree(branch="main", path="/repo"),
        hw.Worktree(branch="feat/x", path="/repo.feat"),
    ]


def test_parse_git_worktree_list_compact_skips_detached() -> None:
    raw = "/repo 0e57943 [main]\n/repo.detached 1234567 (detached HEAD)\n/repo.feat 89abcde [feat/z]\n"
    assert hw.parse_git_worktree_list(raw) == [
        hw.Worktree(branch="main", path="/repo"),
        hw.Worktree(branch="feat/z", path="/repo.feat"),
    ]


def test_parse_git_worktree_list_skips_detached_porcelain() -> None:
    raw = "worktree /repo\nHEAD abc\ndetached\n\nworktree /repo.main\nHEAD def\nbranch refs/heads/main\n"
    assert hw.parse_git_worktree_list(raw) == [hw.Worktree(branch="main", path="/repo.main")]


def test_wt_binary_absent_when_path_has_no_wt(tmp_path: Path) -> None:
    assert hw.wt_binary(env_without_wt(tmp_path)) is None


def test_wt_binary_found_on_path(tmp_path: Path) -> None:
    assert hw.wt_binary(env_with_wt(tmp_path)) is not None


def git_facts(
    argv: Sequence[str], root: Path, *, bare: bool = False
) -> subprocess.CompletedProcess[str] | None:
    """Answer the `git rev-parse` probes one allocation makes, or None to pass."""
    if argv[:2] != ["git", "rev-parse"]:
        return None
    if "--is-bare-repository" in argv:
        return completed(argv, stdout="true\n" if bare else "false\n")
    if "--git-common-dir" in argv:
        return completed(argv, stdout=f"{root / '.git'}\n")
    if "--verify" in argv:
        rev = argv[-1]
        sha = (
            "1111111111111111111111111111111111111111"
            if rev == "HEAD"
            else "2222222222222222222222222222222222222222"
        )
        return completed(argv, stdout=f"{sha}\n")
    raise AssertionError(f"unexpected rev-parse probe: {argv}")


def test_allocate_with_wt_reads_path_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps(
        [{"branch": "main", "path": "/repo"}, {"branch": "feat/184", "path": "/repo.feat-184"}]
    )

    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[1:] == ["list", "--format=json"]:
            return completed(argv, stdout=list_json)
        return completed(argv)

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out == "/repo.feat-184\n"
    (switch_call,) = [call for call in calls if call[0][1] == "switch"]
    assert switch_call[0][1:] == [
        "switch",
        "--create",
        "feat/184",
        "--base",
        "1111111111111111111111111111111111111111",
    ]
    assert switch_call[1]["CI"] == "1"


def test_allocate_with_wt_passes_base_and_emits_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps({"items": [{"branch": "feat/184", "path": "/wt"}]})

    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[1] == "list":
            return completed(argv, stdout=list_json)
        return completed(argv)

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184", "--base", "main", "--json"], env) == herdr_cli.EXIT_OK
    assert json.loads(capsys.readouterr().out) == {
        "branch": "feat/184",
        "cwd": "/wt",
        "engine": "worktrunk",
        "status": "allocated",
    }
    (switch_call,) = [call for call in calls if call[0][1] == "switch"]
    assert switch_call[0][1:] == ["switch", "--create", "feat/184", "--base", "main"]


def test_allocate_with_wt_recovers_existing_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/184", "path": "/wt"}])

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return completed(argv, stdout="1111111111111111111111111111111111111111\n")
        if argv[:2] == ["git", "rev-parse"]:
            return completed(argv, stdout="false\n")
        if argv[1] == "switch":
            return completed(argv, returncode=1, stderr="branch exists")
        return completed(argv, stdout=list_json)

    _ = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == "/wt"


def test_allocate_with_wt_failure_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return completed(argv, stdout="1111111111111111111111111111111111111111\n")
        if argv[:2] == ["git", "rev-parse"]:
            return completed(argv, stdout="false\n")
        if argv[1] == "switch":
            return completed(argv, returncode=1, stderr="boom")
        return completed(argv, stdout=json.dumps([]))

    _ = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_HERDR
    assert "boom" in capsys.readouterr().err


def test_allocate_git_fallback_uses_sibling_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    root = tmp_path / "work" / "repo"
    resolved_root = Path(os.path.realpath(root))
    worktree = resolved_root.parent / f"{resolved_root.name}.feat-184"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[:3] == ["git", "worktree", "add"]:
            worktree.mkdir(parents=True, exist_ok=True)
            return completed(argv)
        raise AssertionError(f"unexpected command: {argv}")

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184", "--base", "main"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == str(worktree)
    assert calls[-1][0] == ["git", "worktree", "add", "-b", "feat/184", str(worktree), "main"]


def test_allocate_git_fallback_retries_existing_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    root = tmp_path / "work" / "repo"
    resolved_root = Path(os.path.realpath(root))
    worktree = resolved_root.parent / f"{resolved_root.name}.feat-184"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[:3] == ["git", "worktree", "add"] and "-b" in argv:
            return completed(argv, returncode=1, stderr="branch already exists")
        if argv[:3] == ["git", "worktree", "add"]:
            worktree.mkdir(parents=True, exist_ok=True)
            return completed(argv)
        raise AssertionError(f"unexpected command: {argv}")

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert calls[-1][0] == ["git", "worktree", "add", str(worktree), "feat/184"]
    add_calls = [call for call in calls if call[0][:3] == ["git", "worktree", "add"]]
    assert add_calls[0][0][-1] == "1111111111111111111111111111111111111111"
    assert capsys.readouterr().out.strip() == str(worktree)


def test_allocate_git_fallback_recovers_existing_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    root = tmp_path / "work" / "repo"
    resolved_root = Path(os.path.realpath(root))
    existing = resolved_root.parent / f"{resolved_root.name}.feat-184"
    existing.mkdir(parents=True, exist_ok=True)
    porcelain = (
        "worktree /repo\nHEAD abc\nbranch refs/heads/main\n\n"
        f"worktree {existing}\nHEAD def\nbranch refs/heads/feat/184\n"
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[:3] == ["git", "worktree", "add"]:
            return completed(argv, returncode=128, stderr="already exists")
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=porcelain)
        raise AssertionError(f"unexpected command: {argv}")

    _ = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == str(existing)


def test_allocate_git_fallback_failure_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        return completed(argv, returncode=1, stderr="no space left")

    _ = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_HERDR
    assert "no space left" in capsys.readouterr().err


def test_git_repo_root_unwraps_a_bare_dot_git_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #207: the git probes answer in a bare repo, where `--show-toplevel` refuses."""
    root = tmp_path / "work" / "everything-claude-code"

    def probe(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root, bare=True)
        return facts if facts is not None else completed(argv)

    calls = patch_runner(monkeypatch, probe)
    assert hw.git_repo_root({}) == Path(os.path.realpath(root))
    assert hw.is_bare_repository({}) is True
    assert "--path-format=absolute" in calls[0][0]


def test_allocate_bare_repository_derives_the_sibling_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #207: a bare repo named `.git` must not yield `<repo>/.git.<branch>`."""
    env = env_with_wt(tmp_path)
    root = Path(os.path.realpath(tmp_path / "work" / "everything-claude-code"))
    worktree = root.parent / f"{root.name}.fix-pr-land-changelog-warning"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root, bare=True)
        if facts is not None:
            return facts
        if argv[:3] == ["git", "worktree", "add"]:
            worktree.mkdir(parents=True, exist_ok=True)
            return completed(argv)
        raise AssertionError(f"unexpected command: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["allocate", "fix/pr-land-changelog-warning", "--base", "main"], env)
    assert code == herdr_cli.EXIT_OK
    captured = capsys.readouterr()
    assert captured.out.strip() == str(worktree)
    assert "bare repository" in captured.err
    assert [call for call in calls if call[0][1] == "switch"] == []


def test_guard_refuses_a_worktree_path_inside_the_git_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #207: a path inside the git directory fails loudly instead of being emitted."""
    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        facts = git_facts(argv, root)
        return facts if facts is not None else completed(argv)

    _ = patch_runner(monkeypatch, handler)
    placements = (
        # the git directory itself, a path inside it, and the incident's hidden sibling
        root / ".git",
        root / ".git" / "worktrees" / "feat-184",
        root / ".git.feat-184",
    )
    for placement in placements:
        with pytest.raises(hw.WorktreeError, match="git directory"):
            hw.guard_not_in_git_dir(placement, {})
    # A bare repo named `repo.git` keeps its documented `<git-dir>.<slug>` sibling.
    assert hw.path_is_within(root / "repo.feat-184", root / ".git") is False


def test_resolve_with_wt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/184", "path": "/wt"}])
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=list_json))
    assert hw.main(["resolve", "feat/184"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == "/wt"


def test_resolve_git_porcelain_emits_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    raw = (
        "worktree /repo\nHEAD abc\nbranch refs/heads/main\n\n"
        "worktree /repo.feat\nHEAD def\nbranch refs/heads/feat/184\n"
    )
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=raw))
    assert hw.main(["resolve", "feat/184", "--json"], env) == herdr_cli.EXIT_OK
    assert json.loads(capsys.readouterr().out) == {
        "branch": "feat/184",
        "cwd": "/repo.feat",
        "engine": "git",
        "status": "resolved",
    }


def test_resolve_missing_branch_exits_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=""))
    assert hw.main(["resolve", "nope"], env) == herdr_cli.EXIT_HERDR
    assert "no worktree found" in capsys.readouterr().err


def test_list_with_wt_emits_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "main", "path": "/repo"}])
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=list_json))
    assert hw.main(["list", "--json"], env) == herdr_cli.EXIT_OK
    assert json.loads(capsys.readouterr().out) == {
        "engine": "worktrunk",
        "worktrees": [{"branch": "main", "path": "/repo"}],
    }


def test_list_git_fallback_prints_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_without_wt(tmp_path)
    raw = "worktree /repo\nHEAD abc\nbranch refs/heads/main\n"
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=raw))
    assert hw.main(["list"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out == "main  /repo\n"


def test_list_with_wt_plain_prints_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/184", "path": "/wt"}])
    _ = patch_runner(monkeypatch, lambda argv, _env: completed(argv, stdout=list_json))
    assert hw.main(["list"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out == "feat/184  /wt\n"


CALLER_HEAD_SHA = "1111111111111111111111111111111111111111"
EXPLICIT_BASE_SHA = "2222222222222222222222222222222222222222"


def test_allocate_without_base_targets_caller_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pin herdr228-reconcile#item-0: allocate without --base branches from the caller HEAD."""
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/228", "path": "/wt-feat-228"}])
    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            assert argv[3] == "HEAD"
            return completed(argv, stdout=f"{CALLER_HEAD_SHA}\n")
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[1] == "list":
            return completed(argv, stdout=list_json)
        return completed(argv)

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/228"], env) == herdr_cli.EXIT_OK
    captured = capsys.readouterr()
    assert captured.out.strip() == "/wt-feat-228"
    assert CALLER_HEAD_SHA in captured.err
    (switch_call,) = [call for call in calls if call[0][1] == "switch"]
    assert switch_call[0][1:] == ["switch", "--create", "feat/228", "--base", CALLER_HEAD_SHA]


def test_allocate_reports_resolved_base_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pin herdr228-reconcile#item-0: the resolved base SHA is reported on stderr."""
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/228", "path": "/wt-feat-228"}])
    root = tmp_path / "work" / "repo"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            assert argv[3] == "main"
            return completed(argv, stdout=f"{EXPLICIT_BASE_SHA}\n")
        facts = git_facts(argv, root)
        if facts is not None:
            return facts
        if argv[1] == "list":
            return completed(argv, stdout=list_json)
        return completed(argv)

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/228", "--base", "main"], env) == herdr_cli.EXIT_OK
    (switch_call,) = [call for call in calls if call[0][1] == "switch"]
    assert switch_call[0][1:] == ["switch", "--create", "feat/228", "--base", "main"]
    assert EXPLICIT_BASE_SHA in capsys.readouterr().err


def test_empty_branch_is_usage_error(tmp_path: Path) -> None:
    assert hw.main(["allocate", "   "], env_without_wt(tmp_path)) == herdr_cli.EXIT_USAGE


def test_missing_command_is_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        _ = hw.main([], {"PATH": ""})
    assert exc.value.code == herdr_cli.EXIT_USAGE


BRANCH = "lane/w11-t7/impl/265-agent-worktree-cwd"
OTHER_BRANCH = "lane/w11-t7/impl/265-agent-worktree-other"
BASE_SHA = "2222222222222222222222222222222222222222"


def lane_env(tmp_path: Path) -> dict[str, str]:
    """PATH without wt plus an explicit lane anchor for the shared store."""
    return {**env_without_wt(tmp_path), "HERDR_LANE_DIR": str(tmp_path / "lane")}


def tasks_file(tmp_path: Path) -> Path:
    """The store the lifecycle verbs write under the explicit lane anchor."""
    return tmp_path / "lane" / ".lane" / "tasks.yaml"


def worktree_row(path: Path | str, branch: str | None) -> str:
    """One `git worktree list --porcelain` record, detached when branch is None."""
    lines = [f"worktree {path}", "HEAD 0000000000000000000000000000000000000000"]
    lines.append(f"branch refs/heads/{branch}" if branch else "detached")
    return "\n".join(lines) + "\n"


def porcelain(*rows: str) -> str:
    """Concatenate porcelain records into one `git worktree list` answer."""
    return "".join(rows)


def seed_worktrees(tmp_path: Path, entries: Mapping[str, object]) -> Path:
    """Write a store with existing top-level keys plus a worktrees map."""
    path = tasks_file(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(
        yaml.safe_dump({"active_leases": {"keep": {}}, "worktrees": dict(entries)}),
        encoding="utf-8",
    )
    return path


def test_claim_transitions_clean_worktree_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
    )
    head = {"branch": "lane/w11-t7/impl/old"}

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:2] == ["git", "show-ref"]:
            return completed(argv, returncode=1)
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return completed(argv, stdout=f"{BASE_SHA}\n")
        if argv[:3] == ["git", "-C", str(worktree)]:
            if argv[3] == "status":
                return completed(argv)
            if argv[3] == "rev-parse":
                return completed(argv, stdout=f"{head['branch']}\n")
            if argv[3] == "switch":
                head["branch"] = argv[5]
                return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "origin/main"], env)
    assert code == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == str(worktree)
    (switch_argv, _switch_env) = next(call for call in calls if "switch" in call[0])
    assert switch_argv == [
        "git",
        "-C",
        str(worktree),
        "switch",
        "--create",
        BRANCH,
        BASE_SHA,
    ]
    for argv, _env in calls:
        assert not {"-B", "-f", "--force"} & set(argv)
        assert "stash" not in argv
    stored = yaml.safe_load(tasks_file(tmp_path).read_text(encoding="utf-8"))
    entry = stored["worktrees"][os.path.realpath(str(worktree))]
    assert entry["branch"] == BRANCH
    assert entry["path"] == os.path.realpath(str(worktree))
    assert entry["base_sha"] == BASE_SHA
    assert entry["role"] == "impl"
    assert entry["task_group"] == "w11-t7"
    assert entry["ticket"] == "265-agent-worktree-cwd"
    assert entry["claimed_at"].endswith("Z")


def test_claim_is_idempotent_when_branch_is_already_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"), worktree_row(worktree, BRANCH))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "rev-parse", "--verify"]:
            return completed(argv, stdout=f"{BASE_SHA}\n")
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "origin/main"], env)
    assert code == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == str(worktree)
    assert not any("switch" in argv for argv, _env in calls)
    stored = yaml.safe_load(tasks_file(tmp_path).read_text(encoding="utf-8"))
    assert stored["worktrees"][os.path.realpath(str(worktree))]["branch"] == BRANCH


def test_claim_refuses_dirty_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv, stdout=" M src/app.py\n")
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "origin/main"], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "clean tree" in capsys.readouterr().err
    assert not any("switch" in argv for argv, _env in calls)
    assert not tasks_file(tmp_path).exists()


def test_claim_refuses_branch_outside_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    worktree = tmp_path / "repo.w11-t7.impl"
    worktree.mkdir()
    calls = patch_runner(monkeypatch, lambda argv, _env: completed(argv))
    code = hw.main(["claim", str(worktree), "feat/184", "--base", "main"], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "namespace" in capsys.readouterr().err
    assert calls == []


def test_claim_requires_explicit_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    worktree = tmp_path / "repo.w11-t7.impl"
    worktree.mkdir()
    calls = patch_runner(monkeypatch, lambda argv, _env: completed(argv))
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "   "], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "explicit --base" in capsys.readouterr().err
    assert calls == []


def test_claim_refuses_branch_checked_out_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    other = root.parent / "repo.w11-t7.other"
    other.mkdir()
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
        worktree_row(other, BRANCH),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "main"], env)
    assert code == herdr_cli.EXIT_HERDR
    assert "already checked out" in capsys.readouterr().err
    assert not any("switch" in argv for argv, _env in calls)


def test_claim_refuses_unregistered_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "main"], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "not a registered git worktree" in capsys.readouterr().err
    assert not any("switch" in argv for argv, _env in calls)


def test_claim_refuses_existing_branch_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv)
        if argv[:2] == ["git", "show-ref"]:
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "main"], env)
    assert code == herdr_cli.EXIT_HERDR
    assert "already exists" in capsys.readouterr().err
    assert not any("switch" in argv for argv, _env in calls)


def test_status_reports_clean_conforming_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        assert argv[:3] == ["git", "-C", str(worktree)]
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout=f"{BRANCH}\n")
        if argv[3] == "status":
            return completed(argv)
        if argv[3] == "rev-parse":
            return completed(argv, stdout=f"{root / '.git'}\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["branch"] == BRANCH
    assert payload["path"] == os.path.realpath(str(worktree))
    assert payload["clean"] is True
    assert payload["dirty"] is False
    assert payload["detached"] is False
    assert payload["flags"] == []


def test_status_flags_dirty_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout=f"{BRANCH}\n")
        if argv[3] == "status":
            return completed(argv, stdout="?? scratch.txt\n")
        if argv[3] == "rev-parse":
            return completed(argv, stdout=f"{root / '.git'}\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is False
    assert payload["dirty"] is True
    assert payload["flags"] == ["dirty"]


def test_status_flags_detached_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    worktree = tmp_path / "repo.w11-t7.impl"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout="HEAD\n")
        if argv[3] == "status":
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["branch"] is None
    assert payload["detached"] is True
    assert payload["flags"] == ["detached"]


def test_status_flags_namespace_violation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    worktree = tmp_path / "repo.feat-184"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout="feat/184\n")
        if argv[3] == "status":
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["flags"] == ["namespace"]


def test_status_flags_layout_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.feat-184"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout=f"{BRANCH}\n")
        if argv[3] == "status":
            return completed(argv)
        if argv[3] == "rev-parse":
            return completed(argv, stdout=f"{root / '.git'}\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["flags"] == ["layout"]


def test_status_plain_output_names_the_flags(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    worktree = tmp_path / "repo.w11-t7.impl"

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout="HEAD\n")
        if argv[3] == "status":
            return completed(argv, stdout=" M x\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree)], env)
    assert code == herdr_cli.EXIT_OK
    out = capsys.readouterr().out
    assert hw.DETACHED_MARKER in out
    assert "dirty" in out
    assert "detached,dirty" in out


def test_retire_removes_clean_worktree_and_merged_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"), worktree_row(worktree, BRANCH))
    store = seed_worktrees(tmp_path, {os.path.realpath(str(worktree)): {"branch": BRANCH}})

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv)
        if argv[:3] == ["git", "worktree", "remove"]:
            return completed(argv)
        if argv[:2] == ["git", "branch"]:
            return completed(argv)
        if argv[:3] == ["git", "worktree", "prune"]:
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["retire", str(worktree)], env)
    assert code == herdr_cli.EXIT_OK
    assert capsys.readouterr().out.strip() == str(worktree)
    argvs = [argv for argv, _env in calls]
    assert ["git", "worktree", "remove", str(worktree)] in argvs
    assert ["git", "branch", "-d", BRANCH] in argvs
    assert ["git", "worktree", "prune"] in argvs
    assert not any("-D" in argv for argv in argvs)
    stored = yaml.safe_load(store.read_text(encoding="utf-8"))
    assert "worktrees" not in stored
    assert stored["active_leases"] == {"keep": {}}


def test_retire_refuses_dirty_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"), worktree_row(worktree, BRANCH))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv, stdout=" M src/app.py\n")
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["retire", str(worktree)], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "clean tree" in capsys.readouterr().err
    assert not any("remove" in argv for argv, _env in calls)


def test_retire_keeps_unmerged_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"), worktree_row(worktree, BRANCH))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv)
        if argv[:3] == ["git", "worktree", "remove"]:
            return completed(argv)
        if argv[:2] == ["git", "branch"]:
            return completed(argv, returncode=1, stderr="error: not fully merged\n")
        if argv[:3] == ["git", "worktree", "prune"]:
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["retire", str(worktree), "--json"], env)
    assert code == herdr_cli.EXIT_OK
    captured = capsys.readouterr()
    assert json.loads(captured.out)["branch_deleted"] is False
    assert "kept branch" in captured.err
    assert not any("-D" in argv for argv, _env in calls)


def test_retire_refuses_branch_checked_out_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    other = root.parent / "repo.w11-t7.other"
    other.mkdir()
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, BRANCH),
        worktree_row(other, BRANCH),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["retire", str(worktree)], env)
    assert code == herdr_cli.EXIT_HERDR
    assert "still checked out" in capsys.readouterr().err
    assert not any("remove" in argv for argv, _env in calls)


def test_retire_refuses_primary_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    root.mkdir(parents=True)
    listing = porcelain(worktree_row(root, "main"))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["retire", str(root)], env)
    assert code == herdr_cli.EXIT_USAGE
    assert "primary worktree" in capsys.readouterr().err


def test_doctor_reports_unlinked_orphan_and_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    root.mkdir(parents=True)
    missing = root.parent / "repo.gone"
    detached = root.parent / "repo.detached"
    detached.mkdir()
    stray = root.parent / "repo.feat-x"
    stray.mkdir()
    live = root.parent / "repo.w11-t7.impl"
    live.mkdir()
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(missing, BRANCH),
        worktree_row(detached, None),
        worktree_row(stray, "feat/x"),
        worktree_row(live, BRANCH),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["doctor", "--json"], env)
    assert code == herdr_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    flags = {row["path"]: row["flags"] for row in payload["worktrees"]}
    assert flags[str(missing)] == ["unlinked"]
    assert flags[str(detached)] == ["orphan"]
    assert flags[str(stray)] == ["namespace"]
    assert flags[str(live)] == []
    assert payload["issues"] == 3
    assert payload["pruned"] is False
    assert not any("prune" in argv for argv, _env in calls)


def test_doctor_prune_removes_only_admin_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    root.mkdir(parents=True)
    missing = root.parent / "repo.gone"
    listing = porcelain(worktree_row(root, "main"), worktree_row(missing, BRANCH))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "worktree", "prune"]:
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    calls = patch_runner(monkeypatch, handler)
    code = hw.main(["doctor", "--prune", "--json"], env)
    assert code == herdr_cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["pruned"] is True
    argvs = [argv for argv, _env in calls]
    assert ["git", "worktree", "prune"] in argvs
    assert not any("remove" in argv for argv in argvs)
    assert not any("--force" in argv for argv in argvs)


# ── the runner seam is shared with herdr_cli (#266 T2a P3) ─────────────────────────


def test_run_delegates_to_the_shared_subprocess_seam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: Calls = []

    def fake(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        seen.append((list(argv), dict(env)))
        return completed(list(argv), stdout="ok\n")

    monkeypatch.setattr(herdr_cli, "run_herdr", fake)

    assert hw.run(["git", "status"], {"A": "1"}).stdout == "ok\n"
    assert seen == [(["git", "status"], {"A": "1"})]


def test_run_wraps_shared_failures_as_worktree_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        raise herdr_cli.HerdrError("cannot run git: missing")

    monkeypatch.setattr(herdr_cli, "run_herdr", fake)

    with pytest.raises(hw.WorktreeError, match="cannot run git: missing"):
        _ = hw.run(["git", "status"], {})


def test_run_checked_reports_the_shared_failure_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(argv: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        return completed(list(argv), returncode=1, stderr="fatal: boom\n")

    monkeypatch.setattr(herdr_cli, "run_herdr", fake)

    with pytest.raises(hw.WorktreeError, match="failed: fatal: boom"):
        _ = hw.run_checked(["git", "status"], {})


def test_failure_detail_is_the_shared_helper() -> None:
    assert hw.failure_detail is herdr_cli.failure_detail


def test_write_tasks_uses_the_shared_atomic_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[Path, dict[str, Any]]] = []

    def fake(path: Path, data: Mapping[str, Any], **_kwargs: object) -> None:
        calls.append((path, dict(data)))

    monkeypatch.setattr(herdr_cli, "atomic_write_yaml", fake)

    hw.write_tasks(tmp_path / "tasks.yaml", {"b": 1, "a": 2})

    assert calls == [(tmp_path / "tasks.yaml", {"b": 1, "a": 2})]


def test_write_tasks_reports_the_shared_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(_path: Path, _data: Mapping[str, Any], **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(herdr_cli, "atomic_write_yaml", explode)

    with pytest.raises(hw.WorktreeError, match="cannot write .*disk full"):
        hw.write_tasks(tmp_path / "tasks.yaml", {})


# ── one JSON/text emit seam (#266 T2b P7) ──────────────────────────────────────────


def test_emitters_share_one_json_seam(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    seen: list[tuple[dict[str, Any], bool]] = []

    def fake(payload: Mapping[str, Any], as_json: bool, _render: Callable[[], None]) -> None:
        seen.append((dict(payload), as_json))

    monkeypatch.setattr(hw, "emit", fake)

    hw.emit_allocation(
        hw.Allocation(branch="b", path="/p", engine=hw.ENGINE_GIT), "allocated", True
    )
    hw.emit_list(hw.ENGINE_GIT, [hw.Worktree(branch="b", path="/p")], True)
    hw.emit_status(
        hw.BindingStatus(path="/p", branch="b", clean=True, detached=False, flags=()), True
    )
    hw.emit_retire(hw.RetireResult(path="/p", branch="b", branch_deleted=True), True)
    hw.emit_doctor([], False, True)

    assert seen == [
        (
            {"branch": "b", "cwd": "/p", "engine": hw.ENGINE_GIT, "status": "allocated"},
            True,
        ),
        ({"engine": hw.ENGINE_GIT, "worktrees": [{"branch": "b", "path": "/p"}]}, True),
        (
            {
                "branch": "b",
                "path": "/p",
                "clean": True,
                "dirty": False,
                "detached": False,
                "flags": [],
                "hint": None,
            },
            True,
        ),
        (
            {
                "path": "/p",
                "branch": "b",
                "removed": True,
                "branch_deleted": True,
                "pruned": True,
            },
            True,
        ),
        ({"engine": hw.ENGINE_GIT, "pruned": False, "issues": 0, "worktrees": []}, True),
    ]
    assert capsys.readouterr().out == ""


# ── residuals: claim diagnostics (#268 R2) ────────────────────────────────────────


def test_claim_names_the_worktree_holding_an_existing_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    other = root.parent / "repo.w11-t7.other"
    other.mkdir()
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
        worktree_row(other, BRANCH),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "main"], env)
    err = capsys.readouterr().err
    assert code == herdr_cli.EXIT_HERDR
    assert "already checked out at" in err
    assert str(other) in err
    assert "retire" in err


def test_claim_says_an_existing_branch_is_checked_out_nowhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.w11-t7.impl"
    worktree.mkdir(parents=True)
    listing = porcelain(
        worktree_row(root, "main"),
        worktree_row(worktree, "lane/w11-t7/impl/old"),
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        if argv[:3] == ["git", "-C", str(worktree)] and argv[3] == "status":
            return completed(argv)
        if argv[:2] == ["git", "show-ref"]:
            return completed(argv)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["claim", str(worktree), BRANCH, "--base", "main"], env)
    err = capsys.readouterr().err
    assert code == herdr_cli.EXIT_HERDR
    assert "not checked out anywhere" in err
    assert "fresh ticket branch" in err


BRANCH_268 = "lane/w11-t7/impl/268-residuals"


# ── residuals: legacy layout migration hint (#268 R4) ─────────────────────────────


def test_status_layout_flag_reports_the_migration_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.legacy-name"
    worktree.mkdir(parents=True)

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout=f"{BRANCH_268}\n")
        if argv[3] == "status":
            return completed(argv)
        if argv[3] == "rev-parse":
            return completed(argv, stdout=f"{root / '.git'}\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree)], env)
    out = capsys.readouterr().out
    assert code == herdr_cli.EXIT_OK
    assert "layout" in out
    assert "retire" in out
    assert "claim" in out
    assert "repo.w11-t7.impl" in out


def test_status_layout_hint_appears_in_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    worktree = root.parent / "repo.legacy-name"
    worktree.mkdir(parents=True)

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[3] == "rev-parse" and "--abbrev-ref" in argv:
            return completed(argv, stdout=f"{BRANCH_268}\n")
        if argv[3] == "status":
            return completed(argv)
        if argv[3] == "rev-parse":
            return completed(argv, stdout=f"{root / '.git'}\n")
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["status", "--worktree", str(worktree), "--json"], env)
    payload = json.loads(capsys.readouterr().out)
    assert code == herdr_cli.EXIT_OK
    assert payload["flags"] == ["layout"]
    assert "retire" in payload["hint"]


# ── residuals: stale lane dir (#268 R1) ───────────────────────────────────────────


def test_doctor_flags_a_worktree_holding_a_stale_lane_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    root.mkdir(parents=True)
    stale = root.parent / "repo.w11-t7.impl"
    stale.mkdir()
    (stale / ".lane").mkdir()
    listing = porcelain(worktree_row(root, "main"), worktree_row(stale, BRANCH_268))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["doctor", "--json"], env)
    payload = json.loads(capsys.readouterr().out)
    assert code == herdr_cli.EXIT_OK
    assert payload["worktrees"] == [
        {"path": str(stale), "branch": BRANCH_268, "flags": ["stale-lane"]}
    ]


def test_doctor_does_not_flag_the_store_base_itself(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = lane_env(tmp_path)
    root = tmp_path / "work" / "repo"
    root.mkdir(parents=True)
    store = root.parent / "repo.w11-t7.impl"
    store.mkdir()
    (store / ".lane").mkdir()
    env = {**env, herdr_cli.LANE_DIR_ENV: str(store)}
    listing = porcelain(worktree_row(root, "main"), worktree_row(store, BRANCH_268))

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[:3] == ["git", "worktree", "list"]:
            return completed(argv, stdout=listing)
        raise AssertionError(f"unexpected call: {argv}")

    _ = patch_runner(monkeypatch, handler)
    code = hw.main(["doctor", "--json"], env)
    payload = json.loads(capsys.readouterr().out)
    assert code == herdr_cli.EXIT_OK
    assert payload["worktrees"] == [{"path": str(store), "branch": BRANCH_268, "flags": []}]
