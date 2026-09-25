"""Tests for `skills/eval-gate/scripts/artifact_paths.py` (issue #6, narrowed scope).

The point of the module is that artifact layout has ONE source of truth. These tests pin the
three properties that makes it load-bearing: the documented defaults apply when no config
exists, the config wins when it does, and `{kind}`/`{topic}`/run expansion is deterministic.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import artifact_paths

SCRIPT = Path(artifact_paths.__file__)
WHEN = datetime(2026, 1, 2, 3, 4, 5)


def _repo_without_config(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    return repo


def _repo_with_config(tmp_path: Path, body: str) -> Path:
    repo = _repo_without_config(tmp_path)
    (repo / ".lsz").mkdir()
    _ = (repo / ".lsz" / "config.yaml").write_text(body, encoding="utf-8")
    return repo


def test_defaults_apply_without_a_config_file(tmp_path: Path) -> None:
    """A repo that never adopted the config must still resolve the documented layout."""
    repo = _repo_without_config(tmp_path)

    config = artifact_paths.load_config(repo)

    assert "defaults" in config.source
    assert config.base == repo / ".lsz"
    assert config.pattern == "{date}/{time}_{topic}/{kind}"
    assert config.kinds["tasks"] == "tmp/tasks"


def test_run_dir_expands_the_configured_pattern(tmp_path: Path) -> None:
    repo = _repo_without_config(tmp_path)

    resolved = artifact_paths.run_dir("auth", "eval", repo, WHEN, 2)

    assert resolved == repo / ".lsz" / "2026-01-02" / "030405_auth" / "eval" / "run-2"


def test_kind_dir_returns_the_flat_kind_directory(tmp_path: Path) -> None:
    repo = _repo_without_config(tmp_path)

    assert artifact_paths.kind_dir("tasks", repo) == repo / ".lsz" / "tmp" / "tasks"
    assert artifact_paths.kind_dir("pr", repo) == repo / ".lsz" / "tmp"


def test_config_overrides_base_pattern_and_kinds(tmp_path: Path) -> None:
    """The config file, not the code, decides the layout."""
    repo = _repo_with_config(
        tmp_path,
        """
storage:
  base: artifacts
  pattern: "{topic}/{kind}/{date}"
  kinds:
    eval: checks
  gate_store: /tmp/gates
""",
    )

    config = artifact_paths.load_config(repo)

    assert config.base == repo / "artifacts"
    assert config.pattern == "{topic}/{kind}/{date}"
    assert config.kinds["eval"] == "checks"
    # unset kinds keep their defaults rather than disappearing
    assert config.kinds["tasks"] == "tmp/tasks"
    assert config.gate_store == Path("/tmp/gates")
    assert artifact_paths.run_dir("auth", "eval", repo, WHEN) == (
        repo / "artifacts" / "auth" / "checks" / "2026-01-02"
    )


def test_gate_store_defaults_and_honours_a_tilde_path(tmp_path: Path) -> None:
    repo = _repo_without_config(tmp_path)
    assert (
        artifact_paths.load_config(repo).gate_store
        == Path.home() / ".pi" / "workflows" / "projects"
    )

    repo2 = _repo_with_config(tmp_path / "second", "storage:\n  gate_store: ~/gates\n")
    assert artifact_paths.load_config(repo2).gate_store == Path.home() / "gates"


def test_malformed_config_fails_loud(tmp_path: Path) -> None:
    """Silently ignoring a broken config would resolve paths the operator never asked for."""
    repo = _repo_with_config(tmp_path, "storage:\n  - not-a-mapping\n")

    try:
        artifact_paths.load_config(repo)
    except ValueError as exc:
        assert "storage" in str(exc)
    else:  # pragma: no cover - the assertion below is the test
        raise AssertionError("a malformed storage block must raise")


def test_cli_resolve_prints_the_path(tmp_path: Path) -> None:
    """Agents call the CLI; the workflow VM cannot read files, so the CLI is the interface."""
    repo = _repo_with_config(tmp_path, "storage:\n  base: .lsz\n  kinds:\n    tasks: tmp/tasks\n")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "resolve", "--kind", "tasks", "--repo-root", str(repo)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(repo / ".lsz" / "tmp" / "tasks")


def test_cli_show_reports_provenance(tmp_path: Path) -> None:
    repo = _repo_with_config(tmp_path, "storage:\n  base: .lsz\n")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "show", "--repo-root", str(repo)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    shown = json.loads(result.stdout)
    assert shown["source"] == str(repo / ".lsz" / "config.yaml")
    assert shown["base"] == str(repo / ".lsz")
    assert "example" in shown["examples"]["eval"]
