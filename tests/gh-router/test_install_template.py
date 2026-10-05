"""Tests for skills/gh-router/scripts/install-template.sh — canonical PR template installer.

The installer's contract is its exit codes and the no-clobber guarantee: it may only ever
write $TARGET/.github/pull_request_template.md, atomically, and refuses to overwrite an
existing template unless --force. No network, no gh.
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALLER = REPO_ROOT / "skills/gh-router/scripts/install-template.sh"
CANONICAL = REPO_ROOT / "skills/gh-router/references/pull_request_template.md"


def run_installer(*args: str, template_src: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if template_src is not None:
        env["GH_ROUTER_TEMPLATE_SRC"] = template_src
    return subprocess.run(["bash", str(INSTALLER), *args], capture_output=True, text=True, env=env)


def dest_of(target: Path) -> Path:
    return target / ".github" / "pull_request_template.md"


def test_canonical_template_section_order() -> None:
    text = CANONICAL.read_text()
    headings = [line for line in text.splitlines() if line.startswith("## ")]
    assert headings == [
        "## Summary",
        "## What Changed",
        "## Blast Radius & Safety",
        "## Evidence",
        "## Architecture",
        "## Landing",
        "## Checklist",
    ], f"unexpected section order: {headings}"
    assert text.startswith("<!-- markdownlint-disable MD041 -->")
    assert "Verification Evidence" not in text
    assert "**Impact**" not in text and "**Risk**" not in text
    for label in (
        "**Downstream consumers:**",
        "**Breaking changes:**",
        "**Data / state invariants:**",
        "**Rollback / containment:**",
    ):
        assert label in text
    assert "CODE_AUTHORS" in text


def test_fresh_install_creates_github_and_matches_canonical(tmp_path: Path) -> None:
    r = run_installer("--target", str(tmp_path))
    assert r.returncode == 0, r.stderr
    dest = dest_of(tmp_path)
    assert dest.is_file()
    assert dest.read_bytes() == CANONICAL.read_bytes()
    # mktemp's 0600 must not survive into the installed file — other users must read it.
    assert stat.S_IMODE(dest.stat().st_mode) == 0o644


def test_no_clobber_refusal_keeps_existing_bytes(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    original = b"hand-written template\n"
    _ = dest.write_bytes(original)
    r = run_installer("--target", str(tmp_path))
    assert r.returncode == 1
    assert "refused" in r.stderr
    assert "--force" in r.stderr
    assert dest.read_bytes() == original
    assert sorted(p.name for p in dest.parent.iterdir()) == ["pull_request_template.md"]


def test_force_overwrites_existing(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    _ = dest.write_text("stale\n")
    r = run_installer("--target", str(tmp_path), "--force")
    assert r.returncode == 0, r.stderr
    assert dest.read_bytes() == CANONICAL.read_bytes()


def test_check_clean_exits_zero_and_writes_nothing(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    _ = dest.write_bytes(CANONICAL.read_bytes())
    before = dest.stat().st_mtime_ns
    r = run_installer("--target", str(tmp_path), "--check")
    assert r.returncode == 0
    assert "clean" in r.stdout
    assert dest.stat().st_mtime_ns == before


def test_check_drifted_exits_one_naming_drift(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    _ = dest.write_bytes(CANONICAL.read_bytes())
    with dest.open("ab") as fh:
        _ = fh.write(b"\nextra\n")
    r = run_installer("--target", str(tmp_path), "--check")
    assert r.returncode == 1
    assert "drift" in r.stdout
    assert dest.read_bytes().endswith(b"\nextra\n")


def test_check_missing_exits_one_without_writing(tmp_path: Path) -> None:
    r = run_installer("--target", str(tmp_path), "--check")
    assert r.returncode == 1
    assert "missing" in r.stdout
    assert not (tmp_path / ".github").exists()
    assert list(tmp_path.iterdir()) == []


def test_check_does_not_require_force(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    _ = dest.write_bytes(CANONICAL.read_bytes())
    r = run_installer("--target", str(tmp_path), "--check")
    assert r.returncode == 0, f"--check on an existing file must not demand --force: {r.stderr}"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    r = run_installer("--target", str(tmp_path), "--dry-run")
    assert r.returncode == 0
    assert "dry-run" in r.stdout and "would install" in r.stdout
    assert not (tmp_path / ".github").exists()


def test_dry_run_overwrite_is_announced_not_applied(tmp_path: Path) -> None:
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    original = b"keep me\n"
    _ = dest.write_bytes(original)
    r = run_installer("--target", str(tmp_path), "--dry-run", "--force")
    assert r.returncode == 0
    assert "would overwrite" in r.stdout
    assert dest.read_bytes() == original


def test_unknown_flag_exits_two(tmp_path: Path) -> None:
    r = run_installer("--frobnicate")
    assert r.returncode == 2
    assert "unknown option" in r.stderr


def test_empty_target_exits_two_without_touching_the_filesystem(tmp_path: Path) -> None:
    """An empty/whitespace/non-directory --target is a usage error (2), never a root install."""
    bogus = tmp_path / "no-such-repo"
    for bad in ("", "   ", str(bogus)):
        r = run_installer("--target", bad)
        assert r.returncode == 2, bad
        assert "--target requires a non-empty directory" in r.stderr, bad
    assert not Path("/.github").exists()
    assert not (bogus / ".github").exists()
    # --check with an invalid target is the same usage error, not a "missing" report
    r = run_installer("--target", "", "--check")
    assert r.returncode == 2
    assert "missing" not in r.stdout


def test_target_without_value_exits_two() -> None:
    r = run_installer("--target")
    assert r.returncode == 2
    assert "--target requires a value" in r.stderr


def test_missing_source_exits_three(tmp_path: Path) -> None:
    r = run_installer("--target", str(tmp_path), template_src="/nonexistent/template.md")
    assert r.returncode == 3
    assert "source template" in r.stderr
    assert not (tmp_path / ".github").exists()


def test_installer_touches_no_second_file(tmp_path: Path) -> None:
    """Whole-tree snapshot: a regression writing anywhere outside $TARGET/.github/ fails here."""
    dest = dest_of(tmp_path)
    dest.parent.mkdir(parents=True)
    _ = dest.write_text("stale\n")
    _ = (dest.parent / "notes.md").write_bytes(b"inside\n")
    _ = (tmp_path / "README.md").write_bytes(b"outside\n")
    (tmp_path / "src").mkdir()
    _ = (tmp_path / "src" / "main.py").write_bytes(b"print(1)\n")

    before = _snapshot(tmp_path)
    r = run_installer("--target", str(tmp_path), "--force")
    assert r.returncode == 0, r.stderr
    after = _snapshot(tmp_path)
    assert after == before | {".github/pull_request_template.md": CANONICAL.read_bytes()}, (
        "installer changed more than the template it was asked to write"
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_source_that_is_a_directory_exits_three(tmp_path: Path) -> None:
    """An unusable source is exit 3 even when the path is a readable directory, not a file."""
    r = run_installer("--target", str(tmp_path), template_src=str(tmp_path))
    assert r.returncode == 3
    assert "source template" in r.stderr


def test_root_target_exits_two() -> None:
    """`--target /` must be a usage error, never a root-filesystem install attempt."""
    for args in (("--target", "/"), ("--target", "/", "--check")):
        r = run_installer(*args)
        assert r.returncode == 2, args
        assert "--target requires a non-empty directory" in r.stderr, args
    assert not Path("/.github").exists()


def test_check_refuses_non_regular_destination(tmp_path: Path) -> None:
    """--check on a non-regular-file destination says refused/not-a-regular-file, not missing."""
    (tmp_path / ".github" / "pull_request_template.md").mkdir(parents=True)
    r = run_installer("--target", str(tmp_path), "--check")
    assert r.returncode == 1
    assert "refused" in r.stdout and "not a regular file" in r.stdout
    assert "missing" not in r.stdout


def test_help_answers_without_side_effects(tmp_path: Path) -> None:
    r = run_installer("--help", "--target", str(tmp_path))
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert not (tmp_path / ".github").exists()
