"""Unit tests for the git-diff-digest range surface (scripts/brief.py).

Synthetic repos only: no network, no gh auth. The brief consumes
``skills/gh-router/lib/range_authority.py`` for base/range resolution and adds
the versioned brief payload (commits, files, areas, signals) on top.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path

import yaml

from tests.gh_router_repos import brief_payload, git, run_brief, seed_diverged_repo

_BANNED_RE = re.compile(r"\b(title|squash|risk)\b", re.IGNORECASE)


def test_yaml_json_round_trip_equal(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    as_yaml = run_brief(tmp_path, spec, "--yaml")
    as_json = run_brief(tmp_path, spec, "--json")
    assert as_yaml.returncode == 0, as_yaml.stderr
    assert as_json.returncode == 0, as_json.stderr
    assert yaml.safe_load(as_yaml.stdout) == json.loads(as_json.stdout)


def test_payload_exact_keys(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    payload = brief_payload(tmp_path, f"{seeds['base']}...feature", "--json")
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
        "fingerprint_staleness",
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
    assert range_block["fingerprint_staleness"] == "stale-when-dirty"
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
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    single = brief_payload(tmp_path, spec, "--json", "--commit", seeds["first"][:7])
    assert len(single["commits"]) == 1
    assert single["commits"][0]["sha"] == seeds["first"]
    assert single["commits"][0]["subject"] == "feat: add parser"
    narrowed = brief_payload(tmp_path, spec, "--json", "--file", "tests/test_app.py")
    assert {f["path"] for f in narrowed["files"]} == {"tests/test_app.py"}
    grouped = brief_payload(tmp_path, spec, "--json", "--group-by", "category")
    assert {a["path"] for a in grouped["areas"]} >= {"source", "test"}
    by_status = brief_payload(tmp_path, spec, "--json", "--group-by", "status")
    assert {a["path"] for a in by_status["areas"]} >= {"added", "modified"}
    positional = brief_payload(tmp_path, spec, "--json", "tests")
    assert positional["files"] and all(f["path"].startswith("tests/") for f in positional["files"])
    text = run_brief(tmp_path, spec, "--commit", seeds["first"][:7], "--hunks", "--context", "1")
    assert text.returncode == 0, text.stderr
    assert "@@" in text.stdout
    assert "print('v2')" in text.stdout


def test_sha_pair_spec_with_mode(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    base_sha = git(tmp_path, "rev-parse", seeds["base"])
    head_sha = git(tmp_path, "rev-parse", "feature")
    payload = brief_payload(tmp_path, f"{base_sha} {head_sha}", "--mode", "..", "--json")
    assert payload["range"]["mode"] == ".."
    assert payload["range"]["counts"]["commits"] == 4


def test_help_contract_outside_repo(tmp_path: Path) -> None:
    result = run_brief(tmp_path, "--help", cwd=Path("/tmp"))
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert len(result.stdout.splitlines()) <= 14
    assert result.stderr == ""


def test_honest_caps_true_totals_and_remainder(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    full = brief_payload(tmp_path, spec, "--json")
    capped_result = run_brief(tmp_path, spec, "--json", "--max-lines", "2")
    assert capped_result.returncode == 0, capped_result.stderr
    capped = json.loads(capped_result.stdout)
    assert capped["truncated"]["commits"] == full["range"]["counts"]["commits"] - 2
    assert capped["truncated"]["files"] == full["range"]["counts"]["files"] - 2
    assert capped["range"]["counts"] == full["range"]["counts"]
    assert capped["range"]["fingerprint"] == full["range"]["fingerprint"]
    text = run_brief(tmp_path, spec, "--max-lines", "2")
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
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    text = run_brief(tmp_path, spec, "--max-lines", "2")
    assert text.returncode == 0, text.stderr
    commits_command, commits_cap = _rerun_line(text.stdout, "commits")
    capped = json.loads(run_brief(tmp_path, spec, "--json", "--max-lines", "2").stdout)
    assert commits_cap == 2 + capped["truncated"]["commits"]
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    rerun = subprocess.run(
        shlex.split(commits_command), capture_output=True, text=True, cwd=elsewhere
    )
    assert rerun.returncode == 0, rerun.stderr
    assert "more commits omitted" not in rerun.stdout

    files_text = run_brief(tmp_path, spec, "--max-lines", "4")
    assert files_text.returncode == 0, files_text.stderr
    assert "more commits omitted" not in files_text.stdout
    files_command, files_cap = _rerun_line(files_text.stdout, "files")
    capped_files = json.loads(run_brief(tmp_path, spec, "--json", "--max-lines", "4").stdout)
    assert capped_files["truncated"]["commits"] == 0
    assert files_cap == 4 + capped_files["truncated"]["files"]
    lookalike = tmp_path / "lookalike"
    lookalike.mkdir()
    _ = git(lookalike, "init")
    _ = git(lookalike, "config", "user.name", "Other")
    _ = git(lookalike, "config", "user.email", "other@x.io")
    _ = git(lookalike, "config", "commit.gpgsign", "false")
    _ = (lookalike / "other.txt").write_text("other\n", encoding="utf-8")
    _ = git(lookalike, "add", ".")
    _ = git(lookalike, "commit", "-m", "chore: unrelated")
    _ = git(lookalike, "checkout", "-b", "feature")
    files_rerun = subprocess.run(
        shlex.split(files_command), capture_output=True, text=True, cwd=lookalike
    )
    assert files_rerun.returncode == 0, files_rerun.stderr
    assert capped_files["range"]["fingerprint"][:12] in files_rerun.stdout
    assert "omitted" not in files_rerun.stdout


def test_fingerprint_identifies_the_range(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    first = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    again = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert first == again

    _ = git(tmp_path, "checkout", "-q", "feature")
    _ = (tmp_path / "extra.txt").write_text("extra\n", encoding="utf-8")
    _ = git(tmp_path, "add", ".")
    _ = git(tmp_path, "commit", "-m", "docs: extra line")
    moved = brief_payload(tmp_path, spec, "--json")["range"]["fingerprint"]
    assert moved != first

    narrow = brief_payload(tmp_path, spec, "--json", "--max-lines", "1")["range"]["fingerprint"]
    wide = brief_payload(tmp_path, spec, "--json", "--max-lines", "40")["range"]["fingerprint"]
    assert narrow == wide == moved


def _commit_object(tree: str, parent: str, message: str) -> bytes:
    """Raw commit-object content, byte-identical to what `git commit-tree` writes."""
    ident = "Tester Author <tester@example.com> 1700000000 +0000"
    return (
        f"tree {tree}\nparent {parent}\nauthor {ident}\ncommitter {ident}\n\n{message}\n".encode()
    )


def _git_object_name(obj: bytes) -> str:
    """The SHA-1 git gives an object: the type/size header prefixes the hash."""
    header = f"commit {len(obj)}\0".encode(encoding="ascii")
    return hashlib.sha1(header + obj).hexdigest()


def _write_commit_object(repo: Path, obj: bytes) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "-t", "commit", "-w", "--stdin"],
        input=obj,
        capture_output=True,
        check=True,
    )
    return done.stdout.decode(encoding="utf-8").strip()


def _colliding_children(repo: Path, head: str, tree: str) -> None:
    """Pad `feature` with two chained children whose SHAs share a 4-hex prefix.

    The refusal under test fires only when two in-range commits collide on the
    minimum prefix. Brute-forcing that with real `git commit-tree` spawns cost
    ~13s per run; searching the object-name space in-process is deterministic
    (~65k expected hashlib calls, no git spawn) and materializes just the two.
    """
    first_bytes = _commit_object(tree, head, "chore: pad 0")
    first_sha = _git_object_name(first_bytes)
    second_bytes: bytes | None = None
    second_sha = ""
    for n in range(1_000_000):
        candidate = _commit_object(tree, first_sha, f"chore: pad 1:{n}")
        digest = _git_object_name(candidate)
        if digest[:4] == first_sha[:4]:
            second_bytes = candidate
            second_sha = digest
            break
    assert second_bytes is not None, "no colliding 4-char prefix within 1e6 candidates"
    assert _write_commit_object(repo, first_bytes) == first_sha
    assert _write_commit_object(repo, second_bytes) == second_sha
    _ = git(repo, "update-ref", "refs/heads/feature", second_sha)


_DIRTY_WARNING = (
    "brief: warning: dirty working tree; the range fingerprint reads stale-when-dirty "
    "(uncommitted edits do not move it)"
)


def _leave_uncommitted_edits(repo: Path) -> None:
    """Leave one modified tracked file plus one untracked file behind."""
    _ = (repo / "src" / "app.py").write_text(
        "print('v1')\nprint('v2')\nprint('v3')\n", encoding="utf-8"
    )
    _ = (repo / "scratch.txt").write_text("scratch\n", encoding="utf-8")


def test_clean_tree_emits_no_dirty_block(tmp_path: Path) -> None:
    """Pin the absence contract: a clean tree carries no `dirty` key at all.

    Mutation that flips this test: return an empty `dirty` block instead of
    None from `_read_brief_dirty` when porcelain is empty.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    payload = brief_payload(tmp_path, spec, "--json")
    assert "dirty" not in payload
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "dirty: " not in text.stdout
    assert text.stderr == ""


def test_dirty_tree_block_carries_porcelain_and_diff_stat(tmp_path: Path) -> None:
    """A dirty tree adds both listings, in the payload and in the text brief.

    Mutation that flips this test: read the stat with `git diff --stat`
    (index vs worktree) instead of `git diff HEAD --stat`.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _leave_uncommitted_edits(tmp_path)
    dirty = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert set(dirty) == {"head", "branch", "porcelain", "diff_stat"}
    assert dirty["head"] == git(tmp_path, "rev-parse", "--short", "HEAD")
    assert dirty["branch"] == seeds["base"]
    raw = subprocess.run(
        ["git", "-C", str(tmp_path), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert dirty["porcelain"] == raw.splitlines()
    assert " M src/app.py" in dirty["porcelain"]
    assert "?? scratch.txt" in dirty["porcelain"]
    assert any("src/app.py" in line for line in dirty["diff_stat"])
    assert dirty["diff_stat"][-1].strip() == "1 file changed, 2 insertions(+)"
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "dirty: working tree has uncommitted changes" in text.stdout
    assert "?? scratch.txt" in text.stdout
    assert "src/app.py |" in text.stdout


def test_staged_only_dirt_appears_in_diff_stat(tmp_path: Path) -> None:
    """A staged-only change still shows in `diff_stat` (staged and unstaged).

    Mutation that flips this test: read the stat with `git diff --stat`
    (index vs worktree) instead of `git diff HEAD --stat`.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _ = (tmp_path / "staged.txt").write_text("staged\n", encoding="utf-8")
    _ = git(tmp_path, "add", "staged.txt")
    dirty = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert "A  staged.txt" in dirty["porcelain"]
    assert any("staged.txt" in row for row in dirty["diff_stat"])
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "staged.txt |" in text.stdout


def test_untracked_only_dirt_prints_no_text_diff_marker(tmp_path: Path) -> None:
    """An untracked-only tree carries no text diff, so the header says so.

    Mutation that flips this test: drop the empty `diff_stat` branch in
    `render_brief_text`, leaving a bare `  diff stat:` header.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _ = (tmp_path / "scratch.txt").write_text("scratch\n", encoding="utf-8")
    dirty = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert dirty["porcelain"] == ["?? scratch.txt"]
    assert dirty["diff_stat"] == []
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "?? scratch.txt" in text.stdout
    assert "  diff stat:" in text.stdout
    assert "    (no text diff)" in text.stdout


def test_deleted_file_dirt_appears_in_diff_stat(tmp_path: Path) -> None:
    """A staged deletion still shows in `diff_stat`.

    Mutation that flips this test: read the stat with `git diff --stat`
    (index vs worktree) instead of `git diff HEAD --stat`.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _ = git(tmp_path, "checkout", "-q", "feature")
    _ = git(tmp_path, "rm", "-q", "src/scanner.py")
    dirty = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert "D  src/scanner.py" in dirty["porcelain"]
    assert any("src/scanner.py" in row for row in dirty["diff_stat"])
    assert any("deletion" in row for row in dirty["diff_stat"])


def test_dirty_header_names_the_worktree_head(tmp_path: Path) -> None:
    """The dirty block names the worktree HEAD, not the range head.

    Mutation that flips this test: drop `head`/`branch` from
    `_read_brief_dirty` (or the text dirty header).
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _leave_uncommitted_edits(tmp_path)
    short = git(tmp_path, "rev-parse", "--short", "HEAD")
    dirty = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert dirty["head"] == short
    assert dirty["branch"] == seeds["base"]
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    expected = f"dirty: working tree has uncommitted changes at {short} ({seeds['base']})"
    assert expected in text.stdout


def test_dirty_rows_cap_with_remainder_marker(tmp_path: Path) -> None:
    """Both dirty listings cap at `--max-lines` with the remainder marker.

    Mutation that flips this test: return the raw porcelain/diff_stat lists
    from `_read_brief_dirty` without `truncate_lines`.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _ = (tmp_path / "src" / "app.py").write_text(
        "print('v1')\nprint('v2')\nprint('v3')\n", encoding="utf-8"
    )
    for index in range(5):
        _ = (tmp_path / f"dirt{index}.txt").write_text(f"{index}\n", encoding="utf-8")
    full = brief_payload(tmp_path, spec, "--json")["dirty"]
    assert len(full["porcelain"]) == 6
    capped = brief_payload(tmp_path, spec, "--json", "--max-lines", "2")["dirty"]
    assert capped["porcelain"][:2] == full["porcelain"][:2]
    assert capped["porcelain"][2] == "... (4 more lines omitted)"
    text = run_brief(tmp_path, spec, "--max-lines", "2")
    assert text.returncode == 0, text.stderr
    assert "more lines omitted" in text.stdout


def test_unreadable_dirty_state_is_advisory(tmp_path: Path) -> None:
    """A failing dirty read skips the block and keeps exit 0.

    Mutation that flips this test: let the `RuntimeError` from `run_git`
    escape `_read_brief_dirty` (no try/except).
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _leave_uncommitted_edits(tmp_path)
    _ = (tmp_path / ".git" / "index").write_bytes(b"garbage-not-an-index")
    result = run_brief(tmp_path, spec, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "dirty" not in payload
    assert "dirty state unavailable" in result.stderr
    assert payload["range"]["counts"]["commits"] == 4
    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    assert "dirty: " not in text.stdout


def test_fingerprint_reads_stale_when_dirty_and_the_tree_warns(tmp_path: Path) -> None:
    """Staleness sits beside the fingerprint; a dirty tree warns, never fails.

    Mutations that flip this test: (a) drop `fingerprint_staleness` from the
    range block, (b) drop the stderr warning in `_warn_brief_dirty`, (c) drop
    `stale-when-dirty` from the text fingerprint line.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    _leave_uncommitted_edits(tmp_path)
    result = run_brief(tmp_path, spec, "--json")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    fingerprint = payload["range"]["fingerprint"]
    assert payload["range"]["fingerprint_staleness"] == "stale-when-dirty"
    assert result.stderr.strip() == _DIRTY_WARNING

    text = run_brief(tmp_path, spec)
    assert text.returncode == 0, text.stderr
    fingerprint_line = text.stdout.splitlines()[1]
    assert fingerprint_line.rsplit(" ", 1)[-1] == "stale-when-dirty"
    assert text.stderr.strip() == _DIRTY_WARNING

    pr_text = run_brief(tmp_path, "--pr", spec)
    assert pr_text.returncode == 0, pr_text.stderr
    assert "stale-when-dirty" in pr_text.stdout

    hit = run_brief(tmp_path, spec, "--verify", fingerprint)
    assert hit.returncode == 0, hit.stderr
    assert "stale-when-dirty" in hit.stdout
    assert hit.stderr.strip() == _DIRTY_WARNING
    verified = run_brief(tmp_path, spec, "--verify", fingerprint, "--json")
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["verification"]["ok"] is True


def test_dirty_tree_never_moves_the_committed_range_facts(tmp_path: Path) -> None:
    """The authority stays commit-only: uncommitted edits move nothing.

    Mutation that flips this test: mix working-tree state into the fingerprint
    material, e.g. append `run_git(repo_root, "status", "--porcelain")` inside
    `_fingerprint_brief_payload`.
    """
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    clean = brief_payload(tmp_path, spec, "--json")
    _leave_uncommitted_edits(tmp_path)
    dirty = brief_payload(tmp_path, spec, "--json")
    assert dirty["range"] == clean["range"]
    assert "dirty" in dirty
    assert "dirty" not in clean
    capped = brief_payload(tmp_path, spec, "--json", "--max-lines", "1")
    assert capped["dirty"]["porcelain"][0] == dirty["dirty"]["porcelain"][0]
    assert "omitted" in capped["dirty"]["porcelain"][-1]
    assert "omitted" in capped["dirty"]["diff_stat"][-1]
    assert capped["range"] == clean["range"]


def test_commit_filter_refusals_are_truthful(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    members = brief_payload(tmp_path, spec, "--json")["commits"]
    assert len(members) == 4

    revspec = run_brief(tmp_path, spec, "--commit", "HEAD")
    assert revspec.returncode == 3
    assert "not a revspec" in revspec.stderr
    assert "4-40 hex chars" in revspec.stderr
    for short_token in ("a", "84", "abc"):
        short = run_brief(tmp_path, spec, "--commit", short_token)
        assert short.returncode == 3
        assert f"commit prefix too short (min 4 hex chars): {short_token}" in short.stderr

    head_sha = git(tmp_path, "rev-parse", "feature")
    inside = brief_payload(tmp_path, spec, "--json", "--commit", head_sha)
    assert len(inside["commits"]) == 1
    assert inside["commits"][0]["sha"] == head_sha

    base_sha = git(tmp_path, "rev-parse", seeds["base"])
    outside = run_brief(tmp_path, spec, "--commit", base_sha)
    assert outside.returncode == 3
    assert f"commit not in range: {base_sha}" in outside.stderr

    _ = git(tmp_path, "checkout", "-q", "feature")
    tree = git(tmp_path, "rev-parse", "feature^{tree}")
    head = git(tmp_path, "rev-parse", "HEAD")
    _colliding_children(tmp_path, head, tree)
    padded = brief_payload(tmp_path, spec, "--json", "--max-lines", "5000")["commits"]
    prefixes: dict[str, list[str]] = {}
    for entry in padded:
        prefixes.setdefault(entry["sha"][:4], []).append(entry["short"])
    collisions = {prefix: shorts for prefix, shorts in prefixes.items() if len(shorts) > 1}
    assert collisions, "padding produced no ambiguous 4-char prefix"
    prefix, shorts = sorted(collisions.items())[0]
    ambiguous = run_brief(tmp_path, spec, "--commit", prefix)
    assert ambiguous.returncode == 3
    assert prefix in ambiguous.stderr
    for short in shorts:
        assert short in ambiguous.stderr


def test_exit_two_malformed_and_exit_three_unknown_ref(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    malformed = run_brief(tmp_path, "...")
    assert malformed.returncode == 2
    unknown = run_brief(tmp_path, f"{seeds['base']}...no-such-branch-xyz")
    assert unknown.returncode == 3
    missing_spec = run_brief(tmp_path)
    assert missing_spec.returncode == 2
    both_structured = run_brief(tmp_path, f"{seeds['base']}...feature", "--yaml", "--json")
    assert both_structured.returncode == 2


def test_no_recommendations_in_outputs(tmp_path: Path) -> None:
    seeds = seed_diverged_repo(tmp_path)
    spec = f"{seeds['base']}...feature"
    for args in ((), ("--yaml",), ("--json",)):
        result = run_brief(tmp_path, spec, *args)
        assert result.returncode == 0, result.stderr
        assert _BANNED_RE.search(result.stdout) is None, f"banned term in {args or 'text'} output"
