"""Unit tests for the git-diff-digest range surface (scripts/brief.py).

Synthetic repos only: no network, no gh auth. The brief consumes
``skills/gh-router/lib/range_authority.py`` for base/range resolution and adds
the versioned brief payload (commits, files, areas, signals) on top.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = (
    REPO_ROOT / "skills" / "gh-router" / "subskills" / "git-diff-digest" / "scripts" / "brief.py"
)

_BANNED_RE = re.compile(r"\b(title|squash|risk)\b", re.IGNORECASE)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _seed_repo(repo: Path) -> dict[str, str]:
    """Build a diverged feature branch with conventional commits."""
    _ = _git(repo, "init")
    _ = _git(repo, "config", "user.name", "Tester Author")
    _ = _git(repo, "config", "user.email", "tester@example.com")
    _ = _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "src").mkdir()
    _ = (repo / "src" / "app.py").write_text("print('v1')\n", encoding="utf-8")
    _ = (repo / "src" / "parser.py").write_text("def parse(x):\n    return x\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "chore: base commit")
    base = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _ = _git(repo, "checkout", "-b", "feature")
    _ = (repo / "src" / "app.py").write_text("print('v1')\nprint('v2')\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "feat: add parser")
    first = _git(repo, "rev-parse", "HEAD")
    _ = (repo / "tests").mkdir()
    _ = (repo / "tests" / "test_app.py").write_text(
        "def test_v2():\n    assert True\n", encoding="utf-8"
    )
    _ = _git(repo, "add", ".")
    _ = _git(
        repo,
        "commit",
        "-m",
        f"fix: handle empty input\n\nCovers the empty case.\n\nRefs #12, follow-up to {first[:7]}.",
    )
    _ = (repo / "package.json").write_text('{"name": "demo"}\n', encoding="utf-8")
    _ = (repo / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "feat(api)!: drop legacy field\n\nBREAKING CHANGE: legacy gone.")
    _ = _git(repo, "mv", "src/parser.py", "src/scanner.py")
    _ = _git(repo, "commit", "-m", "refactor: rename parser module")
    _ = _git(repo, "checkout", base)
    _ = (repo / "docs").mkdir()
    _ = (repo / "docs" / "guide.md").write_text("# Guide\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "docs: tweak guide")
    return {"base": base, "first": first}


def _run_brief(repo: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd if cwd is not None else repo,
    )


def _payload(repo: Path, *args: str) -> Any:
    result = _run_brief(repo, *args)
    assert result.returncode == 0, f"brief failed: {result.stderr}"
    return json.loads(result.stdout)


def test_yaml_json_round_trip_equal(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    as_yaml = _run_brief(tmp_path, spec, "--yaml")
    as_json = _run_brief(tmp_path, spec, "--json")
    assert as_yaml.returncode == 0, as_yaml.stderr
    assert as_json.returncode == 0, as_json.stderr
    assert yaml.safe_load(as_yaml.stdout) == json.loads(as_json.stdout)


def test_payload_exact_keys(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    payload = _payload(tmp_path, f"{seeds['base']}...feature", "--json")
    assert set(payload) == {"schema", "range", "commits", "areas", "files", "signals", "truncated"}
    assert payload["schema"] == 1
    range_block = payload["range"]
    assert isinstance(range_block, dict)
    assert set(range_block) == {
        "spec_in",
        "mode",
        "merge_base",
        "only_in_base",
        "resolved_from",
        "counts",
        "fingerprint",
    }
    assert set(range_block["counts"]) == {
        "commits",
        "files",
        "insertions",
        "deletions",
        "added",
        "modified",
        "renamed",
        "deleted",
    }
    assert range_block["only_in_base"] == 1
    assert range_block["counts"]["commits"] == 4
    commit = next(c for c in payload["commits"] if c["scope"] == "api")
    assert set(commit) == {
        "sha",
        "short",
        "subject",
        "type",
        "scope",
        "breaking",
        "refs",
        "author",
        "date",
        "body",
        "counts",
        "files",
    }
    assert commit["type"] == "feat"
    assert commit["breaking"] is True
    assert set(commit["refs"]) == {"numbers", "shas"}
    assert set(commit["author"]) == {"name", "email"}
    assert set(commit["counts"]) == {"files", "insertions", "deletions"}
    assert set(payload["signals"]) == {
        "breaking",
        "deps",
        "changelog",
        "renames",
        "evidence_candidates",
    }
    assert set(payload["truncated"]) == {"files", "commits"}
    assert payload["signals"]["changelog"] is True
    assert "package.json" in payload["signals"]["deps"]
    assert "src/scanner.py" in payload["signals"]["renames"]
    assert "tests/test_app.py" in payload["signals"]["evidence_candidates"]
    assert payload["signals"]["breaking"] == [commit["short"]]
    fix = next(c for c in payload["commits"] if c["type"] == "fix")
    assert 12 in fix["refs"]["numbers"]
    assert seeds["first"][:7] in fix["refs"]["shas"]
    assert "BREAKING CHANGE" in commit["body"]
    renamed = next(f for f in payload["files"] if f["path"] == "src/scanner.py")
    assert set(renamed) == {
        "path",
        "status",
        "insertions",
        "deletions",
        "commits",
        "category",
        "binary",
        "renamed_from",
    }
    assert renamed["status"] == "renamed"
    assert renamed["renamed_from"] == "src/parser.py"
    assert all(set(a) == {"path", "files", "insertions", "deletions"} for a in payload["areas"])


def test_drill_down_commit_file_hunks_group_by(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    single = _payload(tmp_path, spec, "--json", "--commit", seeds["first"][:7])
    assert len(single["commits"]) == 1
    assert single["commits"][0]["sha"] == seeds["first"]
    assert single["commits"][0]["subject"] == "feat: add parser"
    narrowed = _payload(tmp_path, spec, "--json", "--file", "tests/test_app.py")
    assert {f["path"] for f in narrowed["files"]} == {"tests/test_app.py"}
    grouped = _payload(tmp_path, spec, "--json", "--group-by", "category")
    assert {a["path"] for a in grouped["areas"]} >= {"source", "test"}
    by_status = _payload(tmp_path, spec, "--json", "--group-by", "status")
    assert {a["path"] for a in by_status["areas"]} >= {"added", "modified"}
    positional = _payload(tmp_path, spec, "--json", "tests")
    assert positional["files"] and all(f["path"].startswith("tests/") for f in positional["files"])
    text = _run_brief(tmp_path, spec, "--commit", seeds["first"][:7], "--hunks", "--context", "1")
    assert text.returncode == 0, text.stderr
    assert "@@" in text.stdout
    assert "print('v2')" in text.stdout


def test_sha_pair_spec_with_mode(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    base_sha = _git(tmp_path, "rev-parse", seeds["base"])
    head_sha = _git(tmp_path, "rev-parse", "feature")
    payload = _payload(tmp_path, f"{base_sha} {head_sha}", "--mode", "..", "--json")
    assert payload["range"]["mode"] == ".."
    assert payload["range"]["counts"]["commits"] == 4


def test_help_contract_outside_repo(tmp_path: Path) -> None:
    result = _run_brief(tmp_path, "--help", cwd=Path("/tmp"))
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert len(result.stdout.splitlines()) <= 14
    assert result.stderr == ""


def test_honest_caps_true_totals_and_remainder(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    full = _payload(tmp_path, spec, "--json")
    capped_result = _run_brief(tmp_path, spec, "--json", "--max-lines", "2")
    assert capped_result.returncode == 0, capped_result.stderr
    capped = json.loads(capped_result.stdout)
    assert capped["truncated"]["commits"] == full["range"]["counts"]["commits"] - 2
    assert capped["truncated"]["files"] == full["range"]["counts"]["files"] - 2
    assert capped["range"]["counts"] == full["range"]["counts"]
    assert capped["range"]["fingerprint"] == full["range"]["fingerprint"]
    text = _run_brief(tmp_path, spec, "--max-lines", "2")
    assert text.returncode == 0, text.stderr
    assert f"'{spec}'" in text.stdout
    assert "omitted" in text.stdout
    assert text.stdout.count("brief.py") >= 2


def _rerun_line(output: str, kind: str) -> tuple[str, int]:
    """Split the printed rerun command for KIND off its line; return it and its cap."""
    line = next(line for line in output.splitlines() if f"more {kind} omitted; rerun:" in line)
    command = line.split("rerun: ", 1)[1].rstrip()
    assert command.endswith(")"), f"rerun line is not closed: {line}"
    command = command[:-1]
    found = re.search(r"--max-lines (\d+)", command)
    assert found is not None, f"no --max-lines in rerun: {command}"
    cap = int(found.group(1))
    return command, cap


def test_rerun_commands_close_the_loop(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    text = _run_brief(tmp_path, spec, "--max-lines", "2")
    assert text.returncode == 0, text.stderr
    commits_command, commits_cap = _rerun_line(text.stdout, "commits")
    capped = json.loads(_run_brief(tmp_path, spec, "--json", "--max-lines", "2").stdout)
    assert commits_cap == 2 + capped["truncated"]["commits"]
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    rerun = subprocess.run(
        shlex.split(commits_command), capture_output=True, text=True, cwd=elsewhere
    )
    assert rerun.returncode == 0, rerun.stderr
    assert "more commits omitted" not in rerun.stdout

    files_text = _run_brief(tmp_path, spec, "--max-lines", "4")
    assert files_text.returncode == 0, files_text.stderr
    assert "more commits omitted" not in files_text.stdout
    files_command, files_cap = _rerun_line(files_text.stdout, "files")
    capped_files = json.loads(_run_brief(tmp_path, spec, "--json", "--max-lines", "4").stdout)
    assert capped_files["truncated"]["commits"] == 0
    assert files_cap == 4 + capped_files["truncated"]["files"]
    lookalike = tmp_path / "lookalike"
    lookalike.mkdir()
    _ = _git(lookalike, "init")
    _ = _git(lookalike, "config", "user.name", "Other")
    _ = _git(lookalike, "config", "user.email", "other@x.io")
    _ = _git(lookalike, "config", "commit.gpgsign", "false")
    _ = (lookalike / "other.txt").write_text("other\n", encoding="utf-8")
    _ = _git(lookalike, "add", ".")
    _ = _git(lookalike, "commit", "-m", "chore: unrelated")
    _ = _git(lookalike, "checkout", "-b", "feature")
    files_rerun = subprocess.run(
        shlex.split(files_command), capture_output=True, text=True, cwd=lookalike
    )
    assert files_rerun.returncode == 0, files_rerun.stderr
    assert capped_files["range"]["fingerprint"][:12] in files_rerun.stdout
    assert "omitted" not in files_rerun.stdout


def test_fingerprint_identifies_the_range(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    first = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    again = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert first == again

    _ = _git(tmp_path, "checkout", "-q", "feature")
    _ = (tmp_path / "extra.txt").write_text("extra\n", encoding="utf-8")
    _ = _git(tmp_path, "add", ".")
    _ = _git(tmp_path, "commit", "-m", "docs: extra line")
    moved = _payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert moved != first

    narrow = _payload(tmp_path, spec, "--json", "--max-lines", "1")["range"]["fingerprint"]
    wide = _payload(tmp_path, spec, "--json", "--max-lines", "40")["range"]["fingerprint"]
    assert narrow == wide == moved


def test_commit_filter_refusals_are_truthful(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    members = _payload(tmp_path, spec, "--json")["commits"]
    assert len(members) == 4

    revspec = _run_brief(tmp_path, spec, "--commit", "HEAD")
    assert revspec.returncode == 3
    assert "not a revspec" in revspec.stderr
    assert "4-40 hex chars" in revspec.stderr
    for short_token in ("a", "84", "abc"):
        short = _run_brief(tmp_path, spec, "--commit", short_token)
        assert short.returncode == 3
        assert f"commit prefix too short (min 4 hex chars): {short_token}" in short.stderr

    head_sha = _git(tmp_path, "rev-parse", "feature")
    inside = _payload(tmp_path, spec, "--json", "--commit", head_sha)
    assert len(inside["commits"]) == 1
    assert inside["commits"][0]["sha"] == head_sha

    base_sha = _git(tmp_path, "rev-parse", seeds["base"])
    outside = _run_brief(tmp_path, spec, "--commit", base_sha)
    assert outside.returncode == 3
    assert f"commit not in range: {base_sha}" in outside.stderr

    _ = _git(tmp_path, "checkout", "-q", "feature")
    tree = _git(tmp_path, "write-tree")
    parent = _git(tmp_path, "rev-parse", "HEAD")
    collisions: dict[str, list[str]] = {}
    for _ in range(20):
        for _ in range(100):
            parent = _git(tmp_path, "commit-tree", tree, "-p", parent, "-m", "chore: pad")
        _ = _git(tmp_path, "update-ref", "refs/heads/feature", parent)
        padded = _payload(tmp_path, spec, "--json", "--max-lines", "5000")["commits"]
        prefixes: dict[str, list[str]] = {}
        for entry in padded:
            prefixes.setdefault(entry["sha"][:4], []).append(entry["short"])
        collisions = {prefix: shorts for prefix, shorts in prefixes.items() if len(shorts) > 1}
        if collisions:
            break
    assert collisions, "no ambiguous 4-char prefix after padding"
    prefix, shorts = sorted(collisions.items())[0]
    ambiguous = _run_brief(tmp_path, spec, "--commit", prefix)
    assert ambiguous.returncode == 3
    assert prefix in ambiguous.stderr
    for short in shorts:
        assert short in ambiguous.stderr


def test_exit_two_malformed_and_exit_three_unknown_ref(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    malformed = _run_brief(tmp_path, "...")
    assert malformed.returncode == 2
    unknown = _run_brief(tmp_path, f"{seeds['base']}...no-such-branch-xyz")
    assert unknown.returncode == 3
    missing_spec = _run_brief(tmp_path)
    assert missing_spec.returncode == 2
    both_structured = _run_brief(tmp_path, f"{seeds['base']}...feature", "--yaml", "--json")
    assert both_structured.returncode == 2


def test_no_recommendations_in_outputs(tmp_path: Path) -> None:
    seeds = _seed_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    for args in ((), ("--yaml",), ("--json",)):
        result = _run_brief(tmp_path, spec, *args)
        assert result.returncode == 0, result.stderr
        assert _BANNED_RE.search(result.stdout) is None, f"banned term in {args or 'text'} output"
