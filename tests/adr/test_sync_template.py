"""Tests for bin/sync-template: the installed template is generated, never hand-edited."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
SYNC = REPO_ROOT / "skills" / "adr" / "bin" / "sync-template"
INSTALLED = REPO_ROOT / "docs" / "adr" / "templates" / "template.md"


def run_sync(
    args: list[str], cwd: Path, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(extra_env or {})
    return subprocess.run(
        [str(SYNC), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_sync_writes_template(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "adr"
    result = run_sync([str(target)], tmp_path)
    assert result.returncode == 0, result.stderr
    out = target / "templates" / "template.md"
    text = out.read_text()
    assert text.startswith("# NUMBER. TITLE\n")
    assert "### Considered Options" in text
    assert "TEMPLATE-START" not in text
    assert "TEMPLATE-END" not in text


def test_sync_matches_installed_copy(tmp_path: Path) -> None:
    # The installed copy must always equal fresh script output (single source).
    target = tmp_path / "docs" / "adr"
    result = run_sync([str(target)], tmp_path)
    assert result.returncode == 0, result.stderr
    fresh = (target / "templates" / "template.md").read_bytes()
    assert fresh == INSTALLED.read_bytes()


def test_sync_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "adr"
    assert run_sync([str(target)], tmp_path).returncode == 0
    first = (target / "templates" / "template.md").read_bytes()
    assert run_sync([str(target)], tmp_path).returncode == 0
    assert (target / "templates" / "template.md").read_bytes() == first


def test_sync_rejects_unmarked_ref(tmp_path: Path) -> None:
    bad_ref = tmp_path / "adr-template.md"
    _ = bad_ref.write_text("# no markers here\n")
    result = run_sync(
        [str(tmp_path / "docs" / "adr")], tmp_path, {"ADR_TEMPLATE_REF": str(bad_ref)}
    )
    assert result.returncode != 0
    assert "TEMPLATE-START" in result.stderr


def test_sync_resolves_adr_dir_from_walk(tmp_path: Path) -> None:
    # No explicit arg: nearest .adr-dir wins, mirroring the shim's walk.
    _ = (tmp_path / ".adr-dir").write_text("docs/adr\n")
    nested = tmp_path / "a" / "b"
    _ = nested.mkdir(parents=True)
    result = run_sync([], nested)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "docs" / "adr" / "templates" / "template.md").is_file()


def test_sync_refuses_without_adr_dir(tmp_path: Path) -> None:
    _ = (tmp_path / ".git").mkdir()
    result = run_sync([], tmp_path)
    assert result.returncode != 0
    assert ".adr-dir" in result.stderr
