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

import herdr_cli
import herdr_worktree as hw
import pytest

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


def test_allocate_with_wt_reads_path_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps(
        [{"branch": "main", "path": "/repo"}, {"branch": "feat/184", "path": "/repo.feat-184"}]
    )

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
        if argv[1:] == ["list", "--format=json"]:
            return completed(argv, stdout=list_json)
        return completed(argv)

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert capsys.readouterr().out == "/repo.feat-184\n"
    assert calls[0][0][1:] == ["switch", "--create", "feat/184"]
    assert calls[0][1]["CI"] == "1"


def test_allocate_with_wt_passes_base_and_emits_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps({"items": [{"branch": "feat/184", "path": "/wt"}]})

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
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
    assert calls[0][0][1:] == ["switch", "--create", "feat/184", "--base", "main"]


def test_allocate_with_wt_recovers_existing_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    env = env_with_wt(tmp_path)
    list_json = json.dumps([{"branch": "feat/184", "path": "/wt"}])

    def handler(argv: list[str], _env: dict[str, str]) -> subprocess.CompletedProcess[str]:
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
        if argv[:3] == ["git", "rev-parse", "--git-common-dir"]:
            return completed(argv, stdout=f"{root / '.git'}\n")
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
        if argv[:3] == ["git", "rev-parse", "--git-common-dir"]:
            return completed(argv, stdout=f"{root / '.git'}\n")
        if argv[:3] == ["git", "worktree", "add"] and "-b" in argv:
            return completed(argv, returncode=1, stderr="branch already exists")
        if argv[:3] == ["git", "worktree", "add"]:
            worktree.mkdir(parents=True, exist_ok=True)
            return completed(argv)
        raise AssertionError(f"unexpected command: {argv}")

    calls = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_OK
    assert calls[-1][0] == ["git", "worktree", "add", str(worktree), "feat/184"]
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
        if argv[:3] == ["git", "rev-parse", "--git-common-dir"]:
            return completed(argv, stdout=f"{root / '.git'}\n")
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
        if argv[:3] == ["git", "rev-parse", "--git-common-dir"]:
            return completed(argv, stdout=f"{root / '.git'}\n")
        return completed(argv, returncode=1, stderr="no space left")

    _ = patch_runner(monkeypatch, handler)
    assert hw.main(["allocate", "feat/184"], env) == herdr_cli.EXIT_HERDR
    assert "no space left" in capsys.readouterr().err


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


def test_empty_branch_is_usage_error(tmp_path: Path) -> None:
    assert hw.main(["allocate", "   "], env_without_wt(tmp_path)) == herdr_cli.EXIT_USAGE


def test_missing_command_is_usage_error() -> None:
    with pytest.raises(SystemExit) as exc:
        _ = hw.main([], {"PATH": ""})
    assert exc.value.code == herdr_cli.EXIT_USAGE
