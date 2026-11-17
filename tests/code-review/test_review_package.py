"""Tests for review_package.py bundle generation and range validation."""

import sys
from pathlib import Path

import pytest

# Module-level sys.path insert per LSZ convention
SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "code-review"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from review_package import (
    build_review_package,
    find_repo_root,
    main,
    resolve_default_base,
)


def test_find_repo_root():
    root = find_repo_root()
    assert root.exists()
    assert (root / ".git").exists() or (root / "pyproject.toml").exists()


def test_resolve_default_base():
    root = find_repo_root()
    base = resolve_default_base(root, "HEAD")
    assert isinstance(base, str)
    assert len(base) > 0


def test_build_review_package_valid_range(tmp_path: Path):
    out_file = tmp_path / "test-bundle.diff"
    result_path = build_review_package(
        base="HEAD~1",
        head="HEAD",
        out_path=out_file,
    )
    assert result_path == out_file
    assert out_file.exists()

    content = out_file.read_text(encoding="utf-8")
    assert "REVIEW PACKAGE: HEAD~1..HEAD" in content
    assert "Base SHA:" in content
    assert "Head SHA:" in content
    assert "Diff Digest (SHA256):" in content
    assert "COMMIT LOG" in content
    assert "CHANGED FILES SUMMARY" in content
    assert "EXTENDED CONTEXT DIFF (-U10)" in content


def test_build_review_package_with_spec(tmp_path: Path):
    spec_file = tmp_path / "intent-spec.md"
    _ = spec_file.write_text("# Intent Contract\nMust support 3 subagents.", encoding="utf-8")

    out_file = tmp_path / "spec-bundle.diff"
    build_review_package(
        base="HEAD~1",
        head="HEAD",
        spec_path=spec_file,
        out_path=out_file,
    )
    content = out_file.read_text(encoding="utf-8")
    assert "SPECIFICATION / INTENT CONTRACT" in content
    assert "Must support 3 subagents." in content


def test_build_review_package_invalid_head():
    with pytest.raises(ValueError, match="Invalid head revision"):
        build_review_package(
            base="HEAD",
            head="nonexistent-ref-12345",
        )


def test_build_review_package_invalid_base():
    with pytest.raises(ValueError, match="Invalid base revision"):
        build_review_package(
            base="nonexistent-ref-67890",
            head="HEAD",
        )


def test_main_cli_success(monkeypatch, tmp_path: Path, capsys):
    out_file = tmp_path / "cli-bundle.diff"
    monkeypatch.setattr(
        sys,
        "argv",
        ["review_package.py", "HEAD~1", "HEAD", "--out", str(out_file)],
    )
    exit_code = main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Review bundle written to:" in captured.out
    assert out_file.exists()


def test_main_cli_stdout(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        ["review_package.py", "HEAD~1", "HEAD", "--stdout"],
    )
    exit_code = main()
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "REVIEW PACKAGE: HEAD~1..HEAD" in captured.out
