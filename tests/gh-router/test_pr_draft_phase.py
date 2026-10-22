"""`pr.py --check`: gates plus facts on stdout, scaffold leaf only when apt.

State is derived, never stored: a with-body `--check` writes nothing and
reports counts, title facts, and the squash preview; a body-less `--check`
writes the scaffold leaf under `.lsz/gh-router/` only when absent (present
means write nothing and report path + `stale`; `--force-scaffold` overwrites;
`--out` names another leaf). `draft.json` is never written on any path.
"""

from __future__ import annotations

import functools
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from _squash import (  # noqa: E402
    SQUASH_BODY_MAX_BULLETS,
    SQUASH_MESSAGE_MAX_LINES,
)

from tests.gh_helpers import make_repo, run_git
from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_PY = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts/pr.py"

LONG_BODY_LINES = 20

GH_STUB = """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
for arg in "$@"; do
  if [[ "$arg" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi
  if [[ "$arg" == "user" ]]; then echo "merger-user"; exit 0; fi
done
exit 0
"""


_DRAFT_LONG_BODY = "\n".join(f"body-line-{i}" for i in range(1, LONG_BODY_LINES + 1))
_make_repo = functools.partial(
    make_repo,
    slug="draft",
    branch="feat-draft",
    user_name="Draft Synthetic",
    user_email="draft@x.io",
    extra_commits=(("two.txt", "two\n", "feat: two", _DRAFT_LONG_BODY),),
)


def _gh_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    return git_env(
        PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}",
        GH_LOG=str(tmp_path / "gh.log"),
    )


def _run_check(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--head", "feat-draft", *extra],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def _leaf(repo: Path) -> Path:
    return repo / ".lsz" / "gh-router" / "feat-draft.md"


def test_check_with_body_reports_facts_and_writes_nothing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert not (repo / ".lsz").exists(), "a with-body --check persists nothing"
    assert "commits: 2" in r.stdout
    assert "trailers: 1" in r.stdout
    assert "title (derived): 'feat: two' 9/100 chars" in r.stdout
    assert "squash_body_preview:" in r.stdout
    assert "curated landing body" in r.stdout
    assert "hint:" in r.stdout


def test_check_refuses_title_whose_worst_case_exceeds_budget(tmp_path: Path) -> None:
    """A 93-char bare title refuses pre-PR: worst case is 102 chars."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")
    title_93 = "feat: " + "x" * 87
    assert len(title_93) == 93

    r = _run_check(repo, env, "--body-file", str(body_file), "--title", title_93)

    assert r.returncode == 1, r.stdout
    assert "exceeds the 100-char budget in the worst case" in r.stderr
    assert "(93 chars bare, 102 chars as" in r.stderr
    assert '"code": "gate_refused"' in r.stderr


def test_check_preview_strips_mermaid_and_details(tmp_path: Path) -> None:
    """The stdout preview is the cleaned squash text, not the authored rendering."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "authored.md"
    _ = body_file.write_text(
        "## Summary\nreal change\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "<details><summary>trace</summary>\nlog\n</details>\n",
        encoding="utf-8",
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert not (repo / ".lsz").exists()
    assert "```mermaid" not in r.stdout
    assert "flowchart LR" not in r.stdout
    assert "<details>" not in r.stdout
    assert "real change" in r.stdout


def test_body_less_check_writes_scaffold_leaf_when_absent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = _run_check(repo, env)

    assert r.returncode == 2
    leaf = _leaf(repo)
    assert leaf.is_file(), "the default leaf is branch-scoped under .lsz/gh-router/"
    assert not (repo / ".lsz" / "gh-router" / "draft.json").exists()
    assert list((repo / ".lsz").rglob("draft.json")) == []
    text = leaf.read_text(encoding="utf-8")
    assert text.startswith("<!-- pr-land scaffold: head=")
    assert "<FILL:" in text
    # Facts on stdout: counts, the path, the hint, and the scaffold payload.
    assert "commits: 2" in r.stdout
    assert f"body: {leaf.relative_to(repo)}" in r.stdout
    assert "hint:" in r.stdout
    assert "<FILL:" in r.stdout


def test_body_less_check_present_leaf_writes_nothing_and_reports_stale(
    tmp_path: Path,
) -> None:
    """Absent leaf writes; present leaf is untouched with `stale` reported."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    first = _run_check(repo, env)
    assert first.returncode == 2
    leaf = _leaf(repo)
    written = leaf.read_text(encoding="utf-8")

    second = _run_check(repo, env)

    assert second.returncode == 2
    assert leaf.read_text(encoding="utf-8") == written, "a present leaf is never rewritten"
    assert "stale: false" in second.stdout, "marker matches HEAD, so the leaf is fresh"
    assert f"body: {leaf.relative_to(repo)}" in second.stdout

    _ = leaf.write_text("## Summary\nhand-authored, no marker\n", encoding="utf-8")
    third = _run_check(repo, env)

    assert third.returncode == 2
    assert leaf.read_text(encoding="utf-8") == "## Summary\nhand-authored, no marker\n"
    assert "stale: true" in third.stdout


def test_force_scaffold_overwrites_present_leaf(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    leaf = _leaf(repo)
    _ = leaf.parent.mkdir(parents=True, exist_ok=True)
    _ = leaf.write_text("## Summary\nhand-authored\n", encoding="utf-8")

    r = _run_check(repo, env, "--force-scaffold")

    assert r.returncode == 2
    text = leaf.read_text(encoding="utf-8")
    assert text.startswith("<!-- pr-land scaffold: head=")
    assert "<FILL:" in text


def test_out_names_leaf_under_tool_prefix(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = _run_check(repo, env, "--out", "custom/leaf.md")

    assert r.returncode == 2
    target = repo / ".lsz" / "gh-router" / "custom" / "leaf.md"
    assert target.is_file(), "missing parents are created under the prefix"
    assert not _leaf(repo).exists(), "the default leaf stays untouched"
    assert f"body: {target.relative_to(repo)}" in r.stdout


def test_missing_out_argument_is_a_usage_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--out"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 2
    assert "missing argument for --out" in r.stderr


def test_out_dir_flag_is_rejected(tmp_path: Path) -> None:
    """`--out-dir` died with `draft.json`: the CLI refuses it as unknown."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--out-dir", "tmp/drafts"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 2
    assert "unknown arg: --out-dir" in r.stderr


def test_title_follows_head_not_cwd(tmp_path: Path) -> None:
    """The default title derives from --head, never from the caller's checkout."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    run_git(repo, "checkout", "main")
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file), "--json")

    assert r.returncode == 0, r.stderr
    payload: dict[str, Any] = json.loads(r.stdout)
    assert payload["title"]["text"] == "feat: two"
    assert payload["title"]["derived"] is True
    assert payload["title"]["worst_case_chars"] == 18
    assert payload["title"]["budget"] == 100


def test_empty_range_warns_the_title_is_a_guess(tmp_path: Path) -> None:
    """No unique commits means the title cannot describe the change; say so."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    run_git(repo, "branch", "empty", "main")
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file), "--head", "empty")
    assert "no unique commits" in r.stderr
    assert "--title" in r.stderr


def test_hint_carries_the_curation_spec(tmp_path: Path) -> None:
    """The single stdout hint names the bullet order, the strip rules, and the spec."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert r.stdout.count("hint:") == 1
    assert "Core" in r.stdout
    assert "Mermaid" in r.stdout
    assert 'GLOSSARY.md "Curated Squash Message"' in r.stdout
    assert "pr-land SKILL.md Squash Shape" in r.stdout


def test_hint_splits_body_template_duty_from_squash_overview(tmp_path: Path) -> None:
    """The hint routes the PR body to the installed template (pr-enhance) and confines the
    <=5-bullet strip rules to the squash overview carried by --squash-message-file.

    Mutation: restore the conflated hint (curate pr_body.md to <=5 bullets, no template
    clause, no --squash-message-file) -> the template and squash-file assertions fail.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert "PR template" in r.stdout
    assert "pr-enhance" in r.stdout
    assert "--squash-message-file" in r.stdout
    assert "curate pr_body.md to <=5 bullets" not in r.stdout


def test_hint_states_both_shape_caps_from_the_gate_constants(tmp_path: Path) -> None:
    """The hint names both caps, sourced from `_squash` so a retune cannot drift (#287).

    Mutation: drop the line cap, or hardcode 15 -> the constant-driven line assertion fails.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert f"<={SQUASH_BODY_MAX_BULLETS} bullets" in r.stdout
    assert f"<={SQUASH_MESSAGE_MAX_LINES} lines" in r.stdout


def test_check_merge_keeps_read_only_preflight(tmp_path: Path) -> None:
    """`--check --merge` keeps the read-only preflight: nothing lands and it exits 0
    without requiring --squash-message (the `--check` gate wins over the merge-only gate).

    Mutation: restore the guard `options.merge and not squash_supplied` (drop `not options.check`)
    -> exit 1 (asserts fail).
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file), "--merge")

    assert r.returncode == 0, r.stderr
    assert not (repo / ".lsz").exists(), "--check persists nothing, even with --merge"
    assert "hint:" in r.stdout
    assert "requires an explicit squash commit message" not in r.stderr


def test_check_json_carries_refusals_and_title_facts(tmp_path: Path) -> None:
    """Body-less `--check --json`: exit 2 with the `body_missing` refusal as data."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = _run_check(repo, env, "--json")

    assert r.returncode == 2
    payload: dict[str, Any] = json.loads(r.stdout)
    assert payload["schema"] == "gh-router/pr-land/check@1"
    assert payload["exit_code"] == 2
    assert payload["title"]["derived"] is True
    assert payload["artifact"]["path"] == ".lsz/gh-router/feat-draft.md"
    assert payload["refusals"][0]["code"] == "body_missing"
    assert payload["refusals"][0]["site"] == ".lsz/gh-router/feat-draft.md"
    assert payload["scaffold_written"] is True
    assert "<FILL:" in payload["scaffold"]


def test_no_draft_json_on_any_path(tmp_path: Path) -> None:
    """Deletion proof at the CLI surface: neither gate outcome writes `draft.json`."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    assert _run_check(repo, env, "--body-file", str(body_file)).returncode == 0
    assert _run_check(repo, env).returncode == 2
    assert list((repo).rglob("draft.json")) == []


def test_merge_empty_squash_message_file_exits_2_before_any_gh_call(tmp_path: Path) -> None:
    """An empty --squash-message-file is a usage error (exit 2) raised in the main guard,
    before create_or_reuse_pr: zero gh calls, no PR, no ready flip.

    Mutation: move the emptiness check back into resolve_squash_message (drop it from the main
    guard) -> the PR is created and `gh pr ready` runs first, so gh.log is non-empty (assert fails).
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    empty = tmp_path / "empty.md"
    _ = empty.write_text("", encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--merge",
            "--no-stamp",
            "--head",
            "feat-draft",
            "--title",
            "feat: x",
            "--body",
            "## Summary\nReal.\n",
            "--squash-message-file",
            str(empty),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 2, r.stderr
    assert "--squash-message is empty" in r.stderr
    gh_log = Path(env["GH_LOG"])
    assert not gh_log.exists() or gh_log.read_text(encoding="utf-8") == "", gh_log


def _merge_main_into_branch(repo: Path) -> None:
    """Move main, then merge it into the branch so HEAD is an ordinary merge commit."""
    run_git(repo, "checkout", "main")
    _ = (repo / "main-only.txt").write_text("main\n", encoding="utf-8")
    run_git(repo, "add", "main-only.txt")
    run_git(repo, "commit", "-m", "chore: main moved")
    run_git(repo, "checkout", "feat-draft")
    run_git(repo, "merge", "--no-ff", "-m", "Merge branch 'main' into feat-draft", "main")


def _merge_only_branch(repo: Path) -> None:
    """A branch at the base whose only commit is a merge of the advanced base."""
    run_git(repo, "branch", "merge-only", "main")
    run_git(repo, "checkout", "main")
    _ = (repo / "main-only.txt").write_text("main\n", encoding="utf-8")
    run_git(repo, "add", "main-only.txt")
    run_git(repo, "commit", "-m", "chore: main moved")
    run_git(repo, "update-ref", "refs/remotes/origin/main", "main")
    run_git(repo, "checkout", "merge-only")
    run_git(repo, "merge", "--no-ff", "-m", "Merge branch 'main' into merge-only", "main")


def test_merge_commit_at_head_derives_the_branch_commit_title(tmp_path: Path) -> None:
    """A base merged into the branch must not donate its merge subject as the title (#298).

    Mutation: derive from HEAD -> `title (derived)` becomes the merge subject and --check
    refuses a non-conventional title instead of using the branch's own `feat: two`.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    _merge_main_into_branch(repo)

    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert "title (derived): 'feat: two'" in r.stdout


def test_explicit_title_still_wins_over_merge_commit_derivation(tmp_path: Path) -> None:
    """`--title` keeps precedence even when HEAD is a merge commit (#298)."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    _merge_main_into_branch(repo)

    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file), "--title", "feat: explicit")

    assert r.returncode == 0, r.stderr
    assert "title (from --title): 'feat: explicit'" in r.stdout


def test_merge_only_history_refuses_with_the_explicit_title_form(tmp_path: Path) -> None:
    """A branch whose only reachable commit is a merge has no subject to derive (#298).

    A branch at the base whose only commit is a merge of the advanced base reproduces that
    history; the refusal must print the exact `--title "type(scope): subject"` form and
    precede any gh mutation.
    """
    repo = tmp_path / "repo"
    _make_repo(repo)
    _merge_only_branch(repo)

    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text("## Summary\n- Core: x\n", encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--merge",
            "--no-stamp",
            "--head",
            "merge-only",
            "--body-file",
            str(body_file),
            "--squash-message-file",
            str(msg_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 1, r.stderr
    assert '--title "type(scope): subject"' in r.stderr
    gh_log = Path(env["GH_LOG"])
    assert not gh_log.exists() or gh_log.read_text(encoding="utf-8") == "", gh_log
