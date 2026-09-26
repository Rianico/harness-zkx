"""Tests for the adr fail-loudly shim (issue #79).

The shim must refuse directory-touching adr-tools subcommands when no
`.adr-dir` is resolvable, instead of letting adr-tools mint a silent parallel
`doc/adr` tree with exit 0.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
SHIM = REPO_ROOT / "skills" / "adr" / "bin" / "adr"

STUB = """#!/usr/bin/env bash
echo "real-adr $*"
"""


def _exec(path: Path) -> None:
    _ = path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture
def stub_adr(tmp_path: Path) -> Path:
    real = tmp_path / "real-adr"
    _ = real.write_text(STUB)
    _exec(real)
    return real


def _base_env(real: Path | None, extra: dict[str, str] | None) -> dict[str, str]:
    env = dict(os.environ)
    env["ADR_REAL"] = str(real) if real is not None else "/nonexistent/adr"
    _ = env.pop("ADR_ALLOW_DEFAULT", None)
    _ = env.pop("ADR_SHIM_ACTIVE", None)
    env.update(extra or {})
    return env


def run_shim(
    args: list[str], cwd: Path, real: Path | None = None, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SHIM), *args],
        cwd=cwd,
        env=_base_env(real, extra_env),
        capture_output=True,
        text=True,
        check=False,
    )


def test_new_without_adr_dir_fails_loudly(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".git").mkdir()
    result = run_shim(["new", "probe"], tmp_path, stub_adr)
    assert result.returncode == 2
    assert "no `.adr-dir`" in result.stderr
    assert "adr init docs/adr" in result.stderr
    assert "real-adr" not in result.stdout


@pytest.mark.parametrize("subcommand", ["link", "list", "generate", "upgrade-repository"])
def test_guarded_subcommands_all_refuse(tmp_path: Path, stub_adr: Path, subcommand: str) -> None:
    _ = (tmp_path / ".git").mkdir()
    result = run_shim([subcommand], tmp_path, stub_adr)
    assert result.returncode == 2


def test_help_and_init_pass_through(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".git").mkdir()
    for args in (["help"], ["init", "docs/adr"], []):
        result = run_shim(args, tmp_path, stub_adr)
        assert result.returncode == 0, args
        assert result.stdout.startswith("real-adr")


def test_adr_dir_present_passes_through(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    result = run_shim(["new", "probe"], tmp_path, stub_adr)
    assert result.returncode == 0
    assert "real-adr new probe" in result.stdout


def test_walks_up_to_ancestor_adr_dir(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    nested = tmp_path / "a" / "b"
    _ = nested.mkdir(parents=True)
    result = run_shim(["list"], nested, stub_adr)
    assert result.returncode == 0
    assert "real-adr list" in result.stdout


def test_doc_adr_tree_is_accepted_as_configured(tmp_path: Path, stub_adr: Path) -> None:
    (tmp_path / "doc" / "adr").mkdir(parents=True)
    result = run_shim(["new", "probe"], tmp_path, stub_adr)
    assert result.returncode == 0


def test_walk_stops_at_repo_root(tmp_path: Path, stub_adr: Path) -> None:
    # .adr-dir above the repository root must not bless the worktree.
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    result = run_shim(["new", "probe"], repo, stub_adr)
    assert result.returncode == 2


def test_walk_terminates_at_filesystem_root(tmp_path: Path, stub_adr: Path) -> None:
    # No .git boundary anywhere: the walk must still terminate and refuse.
    top = Path(os.path.realpath(tmp_path))
    work = top / "a" / "b"
    _ = work.mkdir(parents=True)
    result = run_shim(["new", "probe"], work, stub_adr)
    assert result.returncode == 2


def test_escape_hatch_skips_guard(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".git").mkdir()
    result = run_shim(["new", "probe"], tmp_path, stub_adr, {"ADR_ALLOW_DEFAULT": "1"})
    assert result.returncode == 0
    assert "real-adr new probe" in result.stdout


def test_escape_hatch_requires_exactly_one(tmp_path: Path, stub_adr: Path) -> None:
    _ = (tmp_path / ".git").mkdir()
    for value in ("0", "false", "yes"):
        result = run_shim(["new", "probe"], tmp_path, stub_adr, {"ADR_ALLOW_DEFAULT": value})
        assert result.returncode == 2, value


def test_configured_repo_root_passes_through(tmp_path: Path, stub_adr: Path) -> None:
    # Mirrors the harness layout: .adr-dir at the root, calls from a subdir.
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    (tmp_path / ".git").mkdir()
    sub = tmp_path / "skills" / "x"
    _ = sub.mkdir(parents=True)
    result = run_shim(["list"], sub, stub_adr)
    assert result.returncode == 0
    assert "real-adr list" in result.stdout


def test_path_resolution_skips_self(tmp_path: Path, stub_adr: Path) -> None:
    # Primary install mode: a copy of the shim precedes the real adr on PATH,
    # with no ADR_REAL. Self-skip must land on the stub, not re-exec itself.
    shim_dir = tmp_path / "shim" / "bin"
    _ = shim_dir.mkdir(parents=True)
    _ = shutil.copy2(SHIM, shim_dir / "adr")
    _exec(shim_dir / "adr")
    stub_dir = tmp_path / "stub" / "bin"
    _ = stub_dir.mkdir(parents=True)
    _ = (stub_dir / "adr").write_text(STUB)
    _exec(stub_dir / "adr")
    env = _base_env(None, None)
    _ = env.pop("ADR_REAL", None)
    env["PATH"] = os.pathsep.join([str(shim_dir), str(stub_dir), env["PATH"]])
    marker = tmp_path / "cfg"
    _ = marker.mkdir()
    _ = (marker / ".adr-dir").write_text("docs/adr\n")
    result = subprocess.run(
        [str(shim_dir / "adr"), "list"],
        cwd=marker,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("real-adr list")


def test_recursion_guard_breaks_copy_loops(tmp_path: Path, stub_adr: Path) -> None:
    # Two real copies ahead of the binary: the inner one must refuse via
    # ADR_SHIM_ACTIVE instead of exec-looping forever.
    first = tmp_path / "p1"
    second = tmp_path / "p2"
    for d in (first, second):
        _ = d.mkdir()
        _ = shutil.copy2(SHIM, d / "adr")
        _exec(d / "adr")
    env = _base_env(None, None)
    _ = env.pop("ADR_REAL", None)
    env["PATH"] = os.pathsep.join([str(first), str(second), str(tmp_path), env["PATH"]])
    result = subprocess.run(
        [str(first / "adr"), "help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 64
    assert "recursion" in result.stderr


def test_missing_real_adr_is_fatal(tmp_path: Path) -> None:
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    result = run_shim(["list"], tmp_path, None)
    assert result.returncode == 64
    assert "ADR_REAL" in result.stderr or "no real adr" in result.stderr
