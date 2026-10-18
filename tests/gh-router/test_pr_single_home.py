"""Each shared reader lives in exactly one module; every consumer calls through it.

A test per merged reader from T3b/B4. The AST tests fail if a duplicate
implementation is reintroduced; the behavioral tests fail if a consumer stops
calling through the shared home.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _changelog as changelog_mod  # noqa: E402
import _github as github_mod  # noqa: E402
import _options as options_mod  # noqa: E402


def _sources() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in PR_SCRIPTS.glob("*.py")}


def _defs_of(sources: dict[str, str], name: str) -> list[str]:
    found = []
    for fname, text in sources.items():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                found.append(fname)
    return found


def test_lookup_pr_single_home() -> None:
    """One `lookup_pr`: _check/pr/_status must not re-implement the gh query."""
    sources = _sources()
    assert _defs_of(sources, "lookup_pr") == ["_github.py"]
    for consumer in ("_check.py", "pr.py"):
        assert "pulls?head=" not in sources[consumer], consumer
    assert "lookup_pr" in sources["_check.py"]
    assert "lookup_pr" in sources["pr.py"]
    assert "lookup_pr" in sources["_status.py"]


def test_lookup_pr_parses_unified_tsv(monkeypatch: pytest.MonkeyPatch) -> None:
    """The single reader parses the 4-field shape every caller relies on."""

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert any("pulls?head=" in part for part in cmd)
        return subprocess.CompletedProcess(cmd, 0, "7\topen\tfalse\tfalse\n", "")

    monkeypatch.setattr(github_mod, "run_command", fake_run)
    ref = github_mod.lookup_pr("test/repo", "feat-x", state="all", cwd=None)
    assert ref is not None
    assert (ref.number, ref.state, ref.is_draft, ref.merged) == ("7", "open", False, False)
    assert github_mod.lookup_pr("test/repo", "feat-x", state="open", cwd=None) is not None


def test_lookup_pr_empty_means_no_pr(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, "null\n", "")

    monkeypatch.setattr(github_mod, "run_command", fake_run)
    assert github_mod.lookup_pr("test/repo", "feat-x", cwd=None) is None


def test_head_sha_single_home() -> None:
    """One `head_sha`: _draft/_status must call `_github.head_sha`, not re-implement."""
    sources = _sources()
    assert _defs_of(sources, "head_sha") == ["_github.py"]
    assert "_github.head_sha" in sources["_draft.py"]
    assert "_github.head_sha" in sources["_status.py"]


def test_display_path_single_home(tmp_path: Path) -> None:
    """One `display_path`: _status owns it, _draft calls through."""
    sources = _sources()
    assert _defs_of(sources, "display_path") == ["_status.py"]
    assert "def display_path" not in sources["_draft.py"]
    from _status import display_path

    root = tmp_path / "repo"
    sub = root / "sub"
    _ = sub.mkdir(parents=True)
    _ = subprocess.run(["git", "init", "-q", str(root)], capture_output=True, check=True)
    leaf = root / ".lsz" / "gh-router" / "x.md"
    assert display_path(leaf, sub) == ".lsz/gh-router/x.md"
    assert display_path(Path("/elsewhere/x.md"), Path("/repo")) == "/elsewhere/x.md"


def test_read_user_file_single_home(tmp_path: Path) -> None:
    """One `read_user_file`: _options owns it, _github calls through."""
    sources = _sources()
    assert _defs_of(sources, "read_user_file") == ["_options.py"]
    assert "read_user_file" in sources["_github.py"]
    leaf = tmp_path / "body.md"
    _ = leaf.write_text("hello\n", encoding="utf-8")
    assert options_mod.read_user_file(leaf, kind="body", display=str(leaf)) == "hello\n"
    with pytest.raises(options_mod.UsageError, match="body"):
        options_mod.read_user_file(tmp_path / "missing.md", kind="body", display="body.md")


def test_parse_checks_single_home() -> None:
    """One checks-TSV parser: _github.parse_checks; _status must not re-implement it."""
    sources = _sources()
    assert _defs_of(sources, "parse_checks") == ["_github.py"]
    assert "def parse_checks" not in sources["_status.py"]
    state, ok, total = github_mod.parse_checks("a\tpass\nb\tfail\nc\tpass\n")
    assert (state, ok, total) == ("red", 2, 3)
    state, ok, total = github_mod.parse_checks("a\tpass\n")
    assert (state, ok, total) == ("green", 1, 1)
    assert github_mod.parse_checks("") == ("none", 0, 0)


def test_warn_ledger_gap_single_home(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """One ledger advisory: pr.py carries no Ledger wording; _changelog owns it."""
    sources = _sources()
    assert "Ledger floor gate" not in sources["pr.py"]
    assert "warn_ledger_gap" in sources["pr.py"]
    monkeypatch_chdir = pytest.MonkeyPatch()
    monkeypatch_chdir.chdir(tmp_path)
    try:
        changelog_mod.warn_ledger_gap("7", draft=False, no_stamp=False)
    finally:
        monkeypatch_chdir.undo()
    assert "no ## [Unreleased] section" in capsys.readouterr().err


def test_iter_ledger_entries_single_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All three ledger readers route through `_iter_ledger_entries`."""
    changelog = tmp_path / "CHANGELOG.md"
    _ = changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n* something (#7)\n* plain\n",
        encoding="utf-8",
    )
    calls = []
    real_iter = changelog_mod._iter_ledger_entries

    def counting(block: str) -> object:
        calls.append(block)
        return real_iter(block)

    monkeypatch.setattr(changelog_mod, "_iter_ledger_entries", counting)
    assert changelog_mod.unreleased_attributes_pr("7", cwd=tmp_path) is True
    assert changelog_mod.stamp_needed("8", cwd=tmp_path) is True

    def fake_ok(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(github_mod, "run_command", fake_ok)
    assert changelog_mod.stamp_changelog("feat-x", "9", cwd=tmp_path) is True
    assert len(calls) >= 3


def test_build_squash_message_returns_pair() -> None:
    """The squash builder returns `(message, trailers)`; _check uses both halves."""
    sources = _sources()
    assert "pr_co_author_trailers(" not in sources["_check.py"]
    from _squash import build_squash_message

    msg, trailers = build_squash_message("## Summary\nReal.\n", "me", "a\tA Name\ta@x.io\n")
    assert isinstance(msg, str) and isinstance(trailers, str)
    assert "Co-authored-by" in trailers


def test_title_gate_single_home() -> None:
    """One title gate: _check funnels through `title_gate`, no inline re-checks."""
    sources = _sources()
    assert "check_squash_title(" not in sources["_check.py"]
    assert "check_title_length(" not in sources["_check.py"]
    assert sources["_check.py"].count("title_gate(") >= 2


def test_merge_state_verdict_delegates_nothing() -> None:
    """Documents the intentional keep: pr_conflict_verdict ≠ merge_state_verdict."""
    assert github_mod.pr_conflict_verdict("true", "blocked") == "clean"
    assert github_mod.merge_state_verdict("blocked") == "unknown"
