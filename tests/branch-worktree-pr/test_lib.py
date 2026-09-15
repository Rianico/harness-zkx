"""Tests for `skills/branch-worktree-pr/scripts/_lib.py`.

Covers the three worktree-lifecycle defects a convergence run hit:
- `wt list --format=json` schema drift (issue #44),
- ambient `__pycache__` failing admission (issue #40),
- skeletonized `node_modules` handed to the developer (issue #43).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import _lib


def _completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["wt"], returncode=returncode, stdout=stdout, stderr="")


# --- issue #44: both `wt list --format=json` schemas -----------------------------------------

SCHEMA_1 = json.dumps(
    [
        {"branch": "main", "path": "/repo", "is_current": True},
        {"branch": "task/1-x", "path": "/repo.task-1-x", "is_current": False},
    ]
)

SCHEMA_2 = json.dumps(
    {
        "schema": 2,
        "repo": {"default_branch": "main"},
        "collected": {"ci": False},
        "items": [
            {"branch": "main", "worktree": {"path": "/repo", "current": True}},
            {"branch": "task/1-x", "worktree": {"path": "/repo.task-1-x", "current": False}},
            {"branch": "remote-only"},  # branch-only row: no worktree, must be skipped
        ],
    }
)


def test_wt_list_reads_schema_1_bare_array(monkeypatch) -> None:
    monkeypatch.setattr(_lib, "run", lambda cmd, cwd=None: _completed(SCHEMA_1))
    trees = _lib.wt_list()
    assert [(t.branch, t.path, t.is_current) for t in trees] == [
        ("main", "/repo", True),
        ("task/1-x", "/repo.task-1-x", False),
    ]


def test_wt_list_reads_schema_2_envelope(monkeypatch) -> None:
    """Schema 2 nests path/current under `worktree`.

    Unpinned `[list] json-schema` emits schema 1 with a stderr warning and a future wt flips the
    default to schema 2, so both shapes must parse to the same `Worktree` list.
    """
    monkeypatch.setattr(_lib, "run", lambda cmd, cwd=None: _completed(SCHEMA_2))
    trees = _lib.wt_list()
    assert [(t.branch, t.path, t.is_current) for t in trees] == [
        ("main", "/repo", True),
        ("task/1-x", "/repo.task-1-x", False),
    ]


# --- issue #40: ambient bytecode must not fail admission -------------------------------------

PORCELAIN_EPHEMERAL = "?? scripts/__pycache__/\n?? .DS_Store\n?? src/foo.pyc\n"
PORCELAIN_REAL = "?? scripts/__pycache__/\n M src/app.py\n"


def test_git_status_clean_ignores_ephemeral_caches(monkeypatch) -> None:
    """A stray interpreter run without PYTHONDONTWRITEBYTECODE=1 must not halt a run."""
    monkeypatch.setattr(_lib, "run", lambda cmd, cwd=None: _completed(PORCELAIN_EPHEMERAL))
    clean, bad = _lib.git_status_clean()
    assert clean, bad


def test_git_status_clean_still_flags_real_changes(monkeypatch) -> None:
    monkeypatch.setattr(_lib, "run", lambda cmd, cwd=None: _completed(PORCELAIN_REAL))
    clean, bad = _lib.git_status_clean()
    assert not clean
    assert bad == [" M src/app.py"]


def test_is_ephemeral_path_nested_and_root() -> None:
    assert _lib.is_ephemeral_path("scripts/__pycache__")
    assert _lib.is_ephemeral_path("a/b/__pycache__")
    assert _lib.is_ephemeral_path("src/foo.pyc")
    assert _lib.is_ephemeral_path(".DS_Store")
    assert not _lib.is_ephemeral_path("src/app.py")


# --- issue #43: skeletonized dependency tree repair ------------------------------------------


def test_dependency_tree_healthy_flags_dangling_symlinks(tmp_path: Path) -> None:
    """`wt step copy-ignored` can leave every top-level store symlink dangling."""
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    for name in ("oxlint", "vitest"):
        (node_modules / name).symlink_to(tmp_path / "missing" / name)

    healthy, detail = _lib.dependency_tree_healthy(tmp_path)
    assert not healthy
    assert "dangle" in detail


def test_dependency_tree_healthy_flags_missing_node_modules(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    healthy, detail = _lib.dependency_tree_healthy(tmp_path)
    assert not healthy
    assert "missing" in detail


def test_dependency_tree_healthy_accepts_resolving_symlinks(tmp_path: Path) -> None:
    node_modules = tmp_path / "node_modules"
    store = tmp_path / "store" / "vitest"
    store.mkdir(parents=True)
    node_modules.mkdir()
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (node_modules / "vitest").symlink_to(store)

    healthy, _ = _lib.dependency_tree_healthy(tmp_path)
    assert healthy


def test_detect_install_command_prefers_pnpm_lockfile(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: 9\n", encoding="utf-8")
    assert _lib.detect_install_command(tmp_path) == ["pnpm", "install", "--frozen-lockfile"]


def test_detect_install_command_none_without_a_lockfile(tmp_path: Path) -> None:
    assert _lib.detect_install_command(tmp_path) is None


def test_ensure_dependencies_is_a_noop_without_a_lockfile(tmp_path: Path) -> None:
    ok, detail = _lib.ensure_dependencies(tmp_path)
    assert ok
    assert "no lockfile" in detail
