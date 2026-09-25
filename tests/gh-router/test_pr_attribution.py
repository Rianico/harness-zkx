"""Squash-merge attribution: co-author trailers, gates, --check, and pr-refine routing.

Same mock-gh pattern as test_pr_land.py: a stub `gh` on PATH dispatches on argv and
answers from env (COMMITS_TSV, MERGER_LOGIN, PR_BODY, OBSERVE_TSV), capturing the merge
PUT's commit_message to $CAPTURE. Pure functions are driven via pr.py directly.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
PR_SH = PR_SCRIPTS / "pr.sh"
REFINE_SH = REPO_ROOT / "skills/gh-router/subskills/pr-refine/scripts/refine.sh"
NUM = "7"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

from pr import (  # noqa: E402
    RefusalError,
    build_squash_message,
    check_raw_token,
    check_title_length,
    insert_trailers,
    is_closing_line,
    pr_co_author_trailers,
    refuse_raw_token,
)


def run_bash(
    script: str, env_extra: dict[str, str] | None = None, cwd: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=env, cwd=cwd)


def make_gh_mock(tmp_path: Path, **env_extra: str) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(
        """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
if [[ "${1:-}" == "pr" ]]; then
  case "${2:-}" in
    view) printf '%s' "$OBSERVE_TSV"; exit 0 ;;
    checkout) exit 0 ;;
  esac
fi
for arg in "$@"; do
  case "$arg" in
    user) printf '%s\\n' "$MERGER_LOGIN"; exit 0 ;;
    *pulls/7/commits*)
      if [[ "$COMMITS_FAIL" == "1" ]]; then echo "api error: rate limited" >&2; exit 1; fi
      printf '%s' "$COMMITS_TSV"; exit 0 ;;
    .mergeable_state) printf 'clean\\n'; exit 0 ;;
    '[.maintainer_can_modify,'*) printf '%s' "$OBSERVE_TSV"; exit 0 ;;
    *pulls/7/merge*)
      for a in "$@"; do
        case "$a" in
          commit_message=*) printf '%s' "${a#commit_message=}" > "$CAPTURE" ;;
        esac
      done
      printf '{"merged":true}\\n'; exit 0 ;;
    *'pulls?head='*) printf '%s\\n' "$PR_NUMBER"; exit 0 ;;
    '.body // ""') printf '%s' "$PR_BODY"; exit 0 ;;
  esac
done
echo "unexpected gh call: $*" >&2
exit 3
"""
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    env = {
        "PATH": f"{bindir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(tmp_path / "gh.log"),
        "CAPTURE": str(tmp_path / "commit_message.txt"),
        "MERGER_LOGIN": "me",
        "COMMITS_TSV": "",
        "COMMITS_FAIL": "0",
        "PR_BODY": "",
        "PR_NUMBER": NUM,
        "OBSERVE_TSV": "",
        **env_extra,
    }
    return env


# --- pr_co_author_trailers: credit-all-except-merger, dedupe, skips ---


def test_merger_skipped_contributor_credited() -> None:
    tsv = "ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io"
    trailers = pr_co_author_trailers(tsv, merger="me", body="notes")
    assert trailers == "Co-authored-by: Wf Zyx <wf@x.io>\n"


def test_unlinked_author_with_empty_login_still_credited() -> None:
    tsv = "\tGhost\tg@x.io\nme\tMe\tme@x.io"
    trailers = pr_co_author_trailers(tsv, merger="me", body="notes")
    assert trailers == "Co-authored-by: Ghost <g@x.io>\n"


def test_empty_name_email_skipped() -> None:
    tsv = "\tGhost\tg@x.io\nx\t\te@x.io\ny\tWhy\t\nme\tMe\tme@x.io"
    trailers = pr_co_author_trailers(tsv, merger="me", body="notes")
    assert trailers == "Co-authored-by: Ghost <g@x.io>\n"


def test_duplicate_commit_emails_yield_one_trailer() -> None:
    tsv = "a\tWf Zyx\twf@x.io\nb\tDouble U\tWF@X.IO"
    trailers = pr_co_author_trailers(tsv, merger="me", body="notes")
    assert trailers == "Co-authored-by: Wf Zyx <wf@x.io>\n"


def test_existing_trailer_skipped_case_insensitively() -> None:
    tsv = "ghuser\tWf Zyx\twf@x.io"
    body = "notes\n\nco-authored-by: Wf Zyx <WF@X.IO>\n"
    trailers = pr_co_author_trailers(tsv, merger="me", body=body)
    assert trailers == ""


# --- insert_trailers: splice position, byte-identical fast path, normalization ---


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Closes #12", True),
        ("Closes #160", True),
        ("Closes: #12", True),
        ("Closes GH-12", True),
        ("Fixes owner/repo#3", True),
        ("Fixes the parser edge case", False),
        ("Fixed the cache bug", False),
        ("Refs the design doc", False),
        ("resolves ambiguity here", False),
        ("Resolves the ambiguity noted in #88.", False),
        ("Fixes the cache (#42) by keying per root.", False),
        ("- Closes #9", False),
    ],
)
def test_is_closing_line_requires_issue_reference(line: str, expected: bool) -> None:
    assert is_closing_line(line) is expected


def test_issue_citing_prose_does_not_attract_trailers() -> None:
    body = "Summary cites #88 in passing.\n\nFixes the cache (#42) by keying.\n\nCloses #160\n"
    res = insert_trailers(body, "Co-authored-by: W <w@x>")
    assert res == (
        "Summary cites #88 in passing.\n\n"
        "Fixes the cache (#42) by keying.\n\nCo-authored-by: W <w@x>\n\nCloses #160\n"
    )


def test_prose_verbs_do_not_attract_trailers() -> None:
    body = (
        "## Summary\n\nCloses the attribution gap.\n\nFixes the parser edge case.\n\nCloses #160\n"
    )
    res = insert_trailers(body, "Co-authored-by: W <w@x>")
    assert res == (
        "## Summary\n\nCloses the attribution gap.\n\n"
        "Fixes the parser edge case.\n\nCo-authored-by: W <w@x>\n\nCloses #160\n"
    )


def test_trailers_spliced_above_closes() -> None:
    res = insert_trailers("Summary.\n\nCloses #12\n", "Co-authored-by: Wf Zyx <wf@x.io>")
    assert res == "Summary.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12\n"


def test_trailers_appended_at_end_without_closing_line() -> None:
    res = insert_trailers("Just text.\n", "Co-authored-by: Wf Zyx <wf@x.io>")
    assert res == "Just text.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n"


def test_noop_is_byte_identical() -> None:
    for body in (
        "Notes.\n\nCo-authored-by: A <a@x>\n\nCloses #1\n",
        "Just text, no trailers, no closing.\n",
        "",
    ):
        assert insert_trailers(body, "") == body


def test_pasted_duplicate_trailers_normalized_above_closes() -> None:
    body = "Intro.\n\nCo-authored-by: Wf Zyx <wf@x.io>\nCO-AUTHORED-BY: Wf Zyx <WF@X.IO>\n\nCloses #12\n"
    assert insert_trailers(body, "") == "Intro.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12\n"


def test_trailer_below_closes_moved_up() -> None:
    body = "Intro.\n\nCloses #12\nCo-authored-by: W <w@x>\n"
    assert insert_trailers(body, "") == "Intro.\n\nCo-authored-by: W <w@x>\n\nCloses #12\n"


# --- gates: raw-token refusal and title/body length handling (commit #135) ---


def test_raw_token_gate_ignores_prose_mentions() -> None:
    assert not check_raw_token("raw CODE_AUTHORS template tokens are refused")


def test_raw_token_gate_catches_later_line_of_comment_block() -> None:
    assert check_raw_token("<!-- authorship\nCODE_AUTHORS left here\n-->")


def test_raw_token_refused_with_remediation() -> None:
    with pytest.raises(RefusalError):
        refuse_raw_token("intro\n\n<!-- CODE_AUTHORS -->\n")
    # Clean body does not raise
    refuse_raw_token("intro\n\nCo-authored-by: W <w@x>\n")


def test_body_with_long_lines_passes_build_squash_message() -> None:
    """Commit #135: PR body lines exceeding 100 characters pass build_squash_message."""
    long_line = "x" * 150
    body = f"Summary line.\n\n{long_line}\n\nCloses #12\n"
    tsv = "ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io"
    res = build_squash_message(body, merger="me", tsv=tsv)
    assert long_line in res
    assert "Co-authored-by: Wf Zyx <wf@x.io>" in res


def test_check_title_length_enforces_limit_strictly() -> None:
    """Commit title header '<title> (#<num>)' must be <= 100 characters."""
    # 95 chars title + " (#7)" = 100 chars -> passes
    check_title_length("x" * 95, 7)

    # 96 chars title + " (#7)" = 101 chars -> fails
    with pytest.raises(RefusalError):
        check_title_length("x" * 96, 7)


# --- end to end: finalize and merge_pr against mock gh ---


def run_finalize(env: dict[str, str], body: str) -> subprocess.CompletedProcess[str]:
    script = f"""
import os, sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import finalize_squash_message
try:
    res = finalize_squash_message("t/r", "{NUM}", os.environ.get("B", ""))
    print(res, end="")
except Exception:
    sys.exit(1)
"""
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, **env, "B": body},
        cwd=REPO_ROOT,
    )


def run_merge(
    env: dict[str, str], body: str, title: str = "feat: x"
) -> subprocess.CompletedProcess[str]:
    script = f"""
import os, sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import merge_pr
ok = merge_pr("t/r", "{NUM}", "main", os.environ.get("T", ""), os.environ.get("B", ""))
sys.exit(0 if ok else 1)
"""
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, **env, "B": body, "T": title},
        cwd=REPO_ROOT,
    )


def test_finalize_appends_contributor_trailer_above_closes(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    body = "Summary.\n\nCloses #12\n"
    r = run_finalize(env, body)
    assert r.returncode == 0
    assert r.stdout == "Summary.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12"
    assert "appended trailers:" in r.stderr


def test_finalize_superseding_body_dedupes_to_one_trailer(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    body = "Supersedes #157.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #100\n"
    r = run_finalize(env, body)
    assert r.returncode == 0
    assert r.stdout == body.rstrip("\n")
    assert r.stdout.count("Co-authored-by:") == 1


def test_merge_pr_solo_self_merge_is_byte_identical(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io\nme\tMe\tme@x.io")
    body = "Solo work.\n\nCloses #9\n"
    r = run_merge(env, body)
    assert r.returncode == 0
    captured = open(env["CAPTURE"]).read()
    assert captured == body.rstrip("\n")
    assert "Co-authored-by:" not in captured


def test_merge_pr_appends_contributor_trailer(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    r = run_merge(env, "Summary.\n\nCloses #12\n")
    assert r.returncode == 0
    captured = open(env["CAPTURE"]).read()
    assert "Co-authored-by: Wf Zyx <wf@x.io>" in captured
    assert captured.index("Co-authored-by:") < captured.index("Closes #12")


def test_merge_refuses_when_commit_enumeration_fails(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_FAIL="1", COMMITS_TSV="ghuser\tWf Zyx\twf@x.io")
    r = run_merge(env, "Summary.\n\nCloses #12\n")
    assert r.returncode != 0
    assert "could not enumerate" in r.stderr
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_merge_template_body_falls_back_to_subjects(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io")
    template = open(os.path.join(REPO_ROOT, ".github", "pull_request_template.md")).read()
    assert "CODE_AUTHORS" in template
    r = run_merge(env, template)
    assert r.returncode == 0
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" in open(env["GH_LOG"]).read()


def test_merge_token_bearing_body_refused(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "intro\n\n<!-- CODE_AUTHORS: fill me -->\n")
    assert r.returncode != 0
    assert "CODE_AUTHORS" in r.stderr
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_merge_refuses_overlong_title_before_api_call(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "Solo.\n", title="x" * 101)
    assert r.returncode != 0
    assert "exceeds 100 chars" in r.stderr
    assert not os.path.exists(env["GH_LOG"]) or "pulls/7" not in open(env["GH_LOG"]).read()


def test_merge_accepts_title_at_exact_limit(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "Solo.\n", title="x" * 95)  # 95 + " (#7)" = 100
    assert r.returncode == 0
    assert os.path.exists(env["CAPTURE"])


def test_merge_body_with_long_lines_passes(tmp_path: Path) -> None:
    """Commit #135: PR body lines exceeding 100 characters pass merge."""
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "ok\n" + "x" * 150 + "\n")
    assert r.returncode == 0
    assert os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" in open(env["GH_LOG"]).read()


# --- --check dry run ---


def run_check(
    env: dict[str, str], *extra_args: str, use_sh: bool = False
) -> subprocess.CompletedProcess[str]:
    cmd = ["bash", str(PR_SH)] if use_sh else [sys.executable, str(PR_PY)]
    return subprocess.run(
        [*cmd, "--check", "--head", "feat-x", *extra_args],
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        cwd=REPO_ROOT,
    )


def test_check_dry_run_prints_trailers_and_creates_nothing(tmp_path: Path) -> None:
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="Summary.\n\nCloses #12\n",
    )
    r = run_check(env)
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\n"
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_check_dry_run_reports_when_nothing_to_append(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io", PR_BODY="Solo.\n")
    r = run_check(env)
    assert r.returncode == 0
    assert r.stdout == ""
    assert "no co-author trailers" in r.stderr


def test_check_template_body_reports_fallback(tmp_path: Path) -> None:
    template = open(os.path.join(REPO_ROOT, ".github", "pull_request_template.md")).read()
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io", PR_BODY=template)
    r = run_check(env)
    assert r.returncode == 0
    assert "omitted" in r.stdout
    assert "Co-authored-by" not in r.stdout


def test_check_long_line_body_passes(tmp_path: Path) -> None:
    """Commit #135: PR body with lines > 100 characters passes --check."""
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="ok\n" + "x" * 150 + "\n",
    )
    r = run_check(env)
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\n"


def test_check_refuses_raw_token_body(tmp_path: Path) -> None:
    env = make_gh_mock(tmp_path, PR_BODY="intro\n\n<!-- CODE_AUTHORS -->\n")
    r = run_check(env)
    assert r.returncode != 0
    assert r.stdout == ""
    assert "CODE_AUTHORS" in r.stderr


def test_check_evaluates_local_body_file(tmp_path: Path) -> None:
    """--check must evaluate local --body-file without being overwritten by remote gh api fetch."""
    local_file = tmp_path / "custom_pr.md"
    _ = local_file.write_text("Local authored body.\n\nCloses #42\n")
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="Remote body should not overwrite",
    )
    r = run_check(env, "--body-file", str(local_file))
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\n"


def test_check_evaluates_local_body_file_rejects_raw_token(tmp_path: Path) -> None:
    """--check must reject a local --body-file holding raw CODE_AUTHORS token."""
    bad_file = tmp_path / "bad_pr.md"
    _ = bad_file.write_text("intro\n\n<!-- CODE_AUTHORS -->\n")
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="Clean remote body",
    )
    r = run_check(env, "--body-file", str(bad_file))
    assert r.returncode != 0
    assert "CODE_AUTHORS" in r.stderr


def test_check_pr_sh_wrapper_matches_pr_py(tmp_path: Path) -> None:
    """pr.sh wrapper must work for --check and output the same trailers."""
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="Summary.\n\nCloses #12\n",
    )
    r = run_check(env, use_sh=True)
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\n"


# --- pr-refine script ---


def test_refine_lint_body_refuses_token_and_accepts_clean(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    _ = bad.write_text("intro\n\n<!-- CODE_AUTHORS -->\n")
    r = run_bash(f'bash "{REFINE_SH}" lint-body --body-file "{bad}"')
    assert r.returncode != 0
    assert "CODE_AUTHORS" in r.stderr
    ok = tmp_path / "ok.md"
    _ = ok.write_text("intro\n\nCo-authored-by: W <w@x>\n")
    r = run_bash(f'bash "{REFINE_SH}" lint-body --body-file "{ok}"')
    assert r.returncode == 0
    assert "body ok: no raw token" in r.stdout


def test_refine_lint_body_accepts_long_lines(tmp_path: Path) -> None:
    """Commit #135: PR body with lines > 100 characters passes refine.sh lint-body."""
    long_line = "x" * 150
    ok = tmp_path / "long.md"
    _ = ok.write_text(f"intro\n\n{long_line}\n\nCo-authored-by: W <w@x>\n")
    r = run_bash(f'bash "{REFINE_SH}" lint-body --body-file "{ok}"')
    assert r.returncode == 0
    assert "body ok: no raw token" in r.stdout


@pytest.mark.parametrize(
    ("tsv", "flow"),
    [
        ("false\to/r\to/r", "flow=A"),  # same-repo head: flag false, push anyway
        ("true\tfork/r\to/r", "flow=A"),  # fork, maintainer can modify
        ("false\tfork/r\to/r", "flow=B"),  # fork, cannot modify
        ("false\t\to/r", "flow=B"),  # deleted fork: null head repo
    ],
)
def test_refine_observe_routes_on_repo_not_flag_alone(tmp_path: Path, tsv: str, flow: str) -> None:
    env = make_gh_mock(tmp_path, OBSERVE_TSV=tsv)
    r = run_bash(f'bash "{REFINE_SH}" observe 157', env)
    assert r.returncode == 0
    assert "maintainerCanModify=" in r.stdout
    assert flow in r.stdout


# --- pr-refine routing eval: trigger phrasings must hit discriminating tokens ---
REQUIRED_TOKENS = {
    "merge then refine and push": {"refine", "push"},
    "refine the PR": {"refine"},
    "take over this PR": {"take", "over"},
}

STOPWORDS = {
    "merge",
    "then",
    "and",
    "the",
    "a",
    "an",
    "to",
    "this",
    "with",
    "or",
    "for",
    "on",
    "of",
    "in",
}


def skill_description(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"description: >-\n((?:  .*\n)+)", text)
    assert m, f"no folded description in {path}"
    return " ".join(line.strip() for line in m.group(1).splitlines())


def tokens(s: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in STOPWORDS}


def matches_required(phrasing: str, description: str) -> bool:
    return REQUIRED_TOKENS[phrasing] <= tokens(description)


@pytest.mark.parametrize("phrasing", list(REQUIRED_TOKENS))
def test_pr_refine_triggers_catch_contributor_pr_phrasings(phrasing: str) -> None:
    desc = skill_description(REPO_ROOT / "skills/gh-router/subskills/pr-refine/SKILL.md")
    assert matches_required(phrasing, desc), (
        f"{phrasing!r} needs {sorted(REQUIRED_TOKENS[phrasing])} in the pr-refine description"
    )
    assert len(desc) <= 300


def test_generic_pr_token_alone_satisfies_no_phrasing() -> None:
    for phrasing in REQUIRED_TOKENS:
        assert not matches_required(phrasing, "pr"), f"{phrasing!r} is satisfied by 'pr' alone"


def test_pr_refine_frontmatter_declares_negative_space() -> None:
    desc = skill_description(REPO_ROOT / "skills/gh-router/subskills/pr-refine/SKILL.md")
    assert "pr-enhance" in desc
    assert "pr-land" in desc
    router = (REPO_ROOT / "skills/gh-router/SKILL.md").read_text(encoding="utf-8")
    assert "pr-refine" in router
