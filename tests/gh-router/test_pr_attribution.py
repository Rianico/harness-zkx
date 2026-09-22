"""Squash-merge attribution: co-author trailers, gates, --check, and pr-refine routing.

Same mock-gh pattern as test_pr_land.py: a stub `gh` on PATH dispatches on argv and
answers from env (COMMITS_TSV, MERGER_LOGIN, PR_BODY, OBSERVE_TSV), capturing the merge
PUT's commit_message to $CAPTURE. Pure functions are driven via `source pr.sh`.
"""

import os
import stat
import subprocess

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PR_SH = os.path.join(REPO_ROOT, "skills", "gh-router", "subskills", "pr-land", "scripts", "pr.sh")
REFINE_SH = os.path.join(
    REPO_ROOT, "skills", "gh-router", "subskills", "pr-refine", "scripts", "refine.sh"
)
NUM = "7"


def run_bash(script, env_extra=None, cwd=REPO_ROOT):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run(["bash", "-c", script], capture_output=True, text=True, env=env, cwd=cwd)


def make_gh_mock(tmp_path, **env_extra):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    gh.write_text(
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


def trailers_source(tsv, merger="me", body="notes"):
    return (
        f'source "{PR_SH}"; '
        f'if printf \'%s\' "$TSV" | BODY="$BODY_ARG" pr_co_author_trailers "{merger}"; '
        "then echo RC=0; else echo RC=$?; fi"
    )


# --- pr_co_author_trailers: credit-all-except-merger, dedupe, skips ---


def test_merger_skipped_contributor_credited():
    tsv = "ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io"
    r = run_bash(trailers_source(tsv), {"TSV": tsv, "BODY_ARG": "notes"})
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\nRC=0\n"


def test_unlinked_author_with_empty_login_still_credited():
    # .author.login is null when the commit isn't linked to a GitHub account;
    # the name/email in .commit.author must still earn a trailer.
    tsv = "\tGhost\tg@x.io\nme\tMe\tme@x.io"
    r = run_bash(trailers_source(tsv), {"TSV": tsv, "BODY_ARG": "notes"})
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Ghost <g@x.io>\nRC=0\n"


def test_empty_name_email_skipped():
    tsv = "\tGhost\tg@x.io\nx\t\te@x.io\ny\tWhy\t\nme\tMe\tme@x.io"
    r = run_bash(trailers_source(tsv), {"TSV": tsv, "BODY_ARG": "notes"})
    assert r.returncode == 0
    # Empty login with a real name/email is still credited (nothing to exclude it by);
    # empty names and empty emails are skipped, as is the merger.
    assert r.stdout == "Co-authored-by: Ghost <g@x.io>\nRC=0\n"


def test_duplicate_commit_emails_yield_one_trailer():
    tsv = "a\tWf Zyx\twf@x.io\nb\tDouble U\tWF@X.IO"
    r = run_bash(trailers_source(tsv), {"TSV": tsv, "BODY_ARG": "notes"})
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\nRC=0\n"


def test_existing_trailer_skipped_case_insensitively():
    tsv = "ghuser\tWf Zyx\twf@x.io"
    body = "notes\n\nco-authored-by: Wf Zyx <WF@X.IO>\n"
    r = run_bash(trailers_source(tsv), {"TSV": tsv, "BODY_ARG": body})
    assert r.returncode == 0
    assert r.stdout == "RC=0\n"


# --- insert_trailers: splice position, byte-identical fast path, normalization ---


def splice(body, new):
    return run_bash(
        f'source "{PR_SH}"; printf \'%s\' "$NEW" | BODY="$BODY_ARG" insert_trailers',
        {"BODY_ARG": body, "NEW": new},
    )


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Closes #12", "MATCH"),
        ("Closes #160", "MATCH"),
        ("Closes: #12", "MATCH"),
        ("Closes GH-12", "MATCH"),
        ("Fixes owner/repo#3", "MATCH"),
        ("Fixes the parser edge case", "NOMATCH"),
        ("Fixed the cache bug", "NOMATCH"),
        ("Refs the design doc", "NOMATCH"),
        ("resolves ambiguity here", "NOMATCH"),
        ("Resolves the ambiguity noted in #88.", "NOMATCH"),
        ("Fixes the cache (#42) by keying per root.", "NOMATCH"),
        ("- Closes #9", "NOMATCH"),
    ],
)
def test_is_closing_line_requires_issue_reference(line, expected):
    # R2: a closing line is a reference line (keyword plus #N), not a bare verb.
    r = run_bash(
        f'source "{PR_SH}"; if is_closing_line "$L"; then echo MATCH; else echo NOMATCH; fi',
        {"L": line},
    )
    assert r.returncode == 0
    assert r.stdout.strip() == expected


def test_issue_citing_prose_does_not_attract_trailers():
    # R2-residual: prose citing an issue number mid-paragraph is not a directive.
    body = "Summary cites #88 in passing.\n\nFixes the cache (#42) by keying.\n\nCloses #160\n"
    r = splice(body, "Co-authored-by: W <w@x>")
    assert r.returncode == 0
    assert r.stdout == (
        "Summary cites #88 in passing.\n\n"
        "Fixes the cache (#42) by keying.\n\nCo-authored-by: W <w@x>\n\nCloses #160\n"
    )


def test_prose_verbs_do_not_attract_trailers():
    # R2 repro: the Summary sentence starts with "Closes" but carries no reference.
    body = (
        "## Summary\n\nCloses the attribution gap.\n\nFixes the parser edge case.\n\nCloses #160\n"
    )
    r = splice(body, "Co-authored-by: W <w@x>")
    assert r.returncode == 0
    assert r.stdout == (
        "## Summary\n\nCloses the attribution gap.\n\n"
        "Fixes the parser edge case.\n\nCo-authored-by: W <w@x>\n\nCloses #160\n"
    )


def test_trailers_spliced_above_closes():
    r = splice("Summary.\n\nCloses #12\n", "Co-authored-by: Wf Zyx <wf@x.io>")
    assert r.returncode == 0
    assert r.stdout == "Summary.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12\n"


def test_trailers_appended_at_end_without_closing_line():
    r = splice("Just text.\n", "Co-authored-by: Wf Zyx <wf@x.io>")
    assert r.returncode == 0
    assert r.stdout == "Just text.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n"


def test_noop_is_byte_identical():
    for body in (
        "Notes.\n\nCo-authored-by: A <a@x>\n\nCloses #1\n",
        "Just text, no trailers, no closing.\n",
        "",
    ):
        r = splice(body, "")
        assert r.returncode == 0
        assert r.stdout == body


def test_pasted_duplicate_trailers_normalized_above_closes():
    body = "Intro.\n\nCo-authored-by: Wf Zyx <wf@x.io>\nCO-AUTHORED-BY: Wf Zyx <WF@X.IO>\n\nCloses #12\n"
    r = splice(body, "")
    assert r.returncode == 0
    assert r.stdout == "Intro.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12\n"


def test_trailer_below_closes_moved_up():
    r = splice("Intro.\n\nCloses #12\nCo-authored-by: W <w@x>\n", "")
    assert r.returncode == 0
    assert r.stdout == "Intro.\n\nCo-authored-by: W <w@x>\n\nCloses #12\n"


# --- gates: length-100 and raw-token refusal ---


def test_long_line_refused_with_numbers_then_wrapped_retry_passes():
    bad = "ok\nok\n" + "x" * 120 + "\n"
    r = run_bash(
        f'source "{PR_SH}"; if printf \'%s\' "$B" | refuse_long_lines; then echo RC=0; else echo RC=$?; fi',
        {"B": bad},
    )
    assert r.returncode == 0
    assert "RC=1" in r.stdout
    assert ": 3" in r.stderr
    good = "ok\nok\n" + "x" * 100 + "\n"
    r = run_bash(
        f'source "{PR_SH}"; if printf \'%s\' "$B" | refuse_long_lines; then echo RC=0; else echo RC=$?; fi',
        {"B": good},
    )
    assert "RC=0" in r.stdout


def test_raw_token_refused_with_remediation():
    r = run_bash(
        f'source "{PR_SH}"; if printf \'%s\' "$B" | refuse_raw_token; then echo RC=0; else echo RC=$?; fi',
        {"B": "intro\n\n<!-- CODE_AUTHORS -->\n"},
    )
    assert r.returncode == 0
    assert "RC=1" in r.stdout
    assert "remediation" in r.stderr
    r = run_bash(
        f'source "{PR_SH}"; if printf \'%s\' "$B" | refuse_raw_token; then echo RC=0; else echo RC=$?; fi',
        {"B": "intro\n\nCo-authored-by: W <w@x>\n"},
    )
    assert "RC=0" in r.stdout


# --- end to end: finalize and merge_pr against mock gh ---


def test_finalize_appends_contributor_trailer_above_closes(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    body = "Summary.\n\nCloses #12\n"
    r = run_bash(
        f'source "{PR_SH}"; REPO=t/r; NUM={NUM}; BODY="$B"; finalize_squash_message "$B"',
        {**env, "B": body},
    )
    assert r.returncode == 0
    # finalize returns through $(...) which strips trailing newlines — the same
    # shaping today's merge path applies, so pin the stripped bytes, not the input.
    assert r.stdout == "Summary.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #12"
    assert "appended trailers:" in r.stderr


def test_finalize_superseding_body_dedupes_to_one_trailer(tmp_path):
    # Flow B: hand-written trailer + Supersedes + Closes meets the same commit author.
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    body = "Supersedes #157.\n\nCo-authored-by: Wf Zyx <wf@x.io>\n\nCloses #100\n"
    r = run_bash(
        f'source "{PR_SH}"; REPO=t/r; NUM={NUM}; BODY="$B"; finalize_squash_message "$B"',
        {**env, "B": body},
    )
    assert r.returncode == 0
    assert r.stdout == body.rstrip("\n")
    assert r.stdout.count("Co-authored-by:") == 1


def run_merge(env, body, title="feat: x"):
    return run_bash(
        f'source "{PR_SH}"; REPO=t/r; NUM={NUM}; TITLE="$T"; BASE=main; BODY="$B"; merge_pr',
        {**env, "B": body, "T": title},
    )


def test_merge_pr_solo_self_merge_is_byte_identical(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io\nme\tMe\tme@x.io")
    body = "Solo work.\n\nCloses #9\n"
    r = run_merge(env, body)
    assert r.returncode == 0
    captured = open(env["CAPTURE"]).read()
    # $(...) in the merge path strips trailing newlines today; S1 pins those exact
    # bytes — nothing appended, nothing reformatted.
    assert captured == body.rstrip("\n")
    assert "Co-authored-by:" not in captured


def test_merge_pr_appends_contributor_trailer(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io")
    r = run_merge(env, "Summary.\n\nCloses #12\n")
    assert r.returncode == 0
    captured = open(env["CAPTURE"]).read()
    assert "Co-authored-by: Wf Zyx <wf@x.io>" in captured
    assert captured.index("Co-authored-by:") < captured.index("Closes #12")


def test_merge_refuses_when_commit_enumeration_fails(tmp_path):
    # R1: a failed commits call is not an empty commit list — refuse loudly,
    # never merge silently unattributed.
    env = make_gh_mock(tmp_path, COMMITS_FAIL="1", COMMITS_TSV="ghuser\tWf Zyx\twf@x.io")
    r = run_merge(env, "Summary.\n\nCloses #12\n")
    assert r.returncode != 0
    assert "could not enumerate" in r.stderr
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_merge_template_body_falls_back_to_subjects(tmp_path):
    # R9(a): the default invocation stamps the template (with CODE_AUTHORS) as the
    # body; squash_message maps it to no commit_message, so the merge proceeds and
    # GitHub builds the message with its own attribution.
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io")
    template = open(os.path.join(REPO_ROOT, ".github", "pull_request_template.md")).read()
    assert "CODE_AUTHORS" in template
    r = run_merge(env, template)
    assert r.returncode == 0
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" in open(env["GH_LOG"]).read()


def test_merge_token_bearing_body_refused(tmp_path):
    # R9(a): the token gate applies exactly when the body becomes the message.
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "intro\n\n<!-- CODE_AUTHORS: fill me -->\n")
    assert r.returncode != 0
    assert "CODE_AUTHORS" in r.stderr
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_merge_refuses_overlong_title_before_api_call(tmp_path):
    # R4: header "<title> (#7)" at 106 chars exceeds commitlint header-max-length.
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "Solo.\n", title="x" * 101)
    assert r.returncode != 0
    assert "exceeds 100 chars" in r.stderr
    assert not os.path.exists(env["GH_LOG"]) or "pulls/7" not in open(env["GH_LOG"]).read()


def test_merge_accepts_title_at_exact_limit(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "Solo.\n", title="x" * 95)  # 95 + " (#7)" = 100
    assert r.returncode == 0
    assert os.path.exists(env["CAPTURE"])


def test_merge_pr_refuses_before_api_call_on_long_line(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io")
    r = run_merge(env, "ok\n" + "x" * 120 + "\n")
    assert r.returncode != 0
    assert not os.path.exists(env["CAPTURE"])
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


# --- --check dry run ---


def test_check_dry_run_prints_trailers_and_creates_nothing(tmp_path):
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="Summary.\n\nCloses #12\n",
    )
    r = run_bash(f'bash "{PR_SH}" --check --head feat-x', env)
    assert r.returncode == 0
    assert r.stdout == "Co-authored-by: Wf Zyx <wf@x.io>\n"
    assert "pulls/7/merge" not in open(env["GH_LOG"]).read()


def test_check_dry_run_reports_when_nothing_to_append(tmp_path):
    env = make_gh_mock(tmp_path, COMMITS_TSV="me\tMe\tme@x.io", PR_BODY="Solo.\n")
    r = run_bash(f'bash "{PR_SH}" --check --head feat-x', env)
    assert r.returncode == 0
    assert r.stdout == ""
    assert "no co-author trailers" in r.stderr


def test_check_template_body_reports_fallback(tmp_path):
    # R11: a pristine-template body never becomes the message — the dry run says
    # so and exits 0 instead of refusing where the merge proceeds.
    template = open(os.path.join(REPO_ROOT, ".github", "pull_request_template.md")).read()
    env = make_gh_mock(tmp_path, COMMITS_TSV="ghuser\tWf Zyx\twf@x.io", PR_BODY=template)
    r = run_bash(f'bash "{PR_SH}" --check --head feat-x', env)
    assert r.returncode == 0
    assert "omitted" in r.stdout
    assert "Co-authored-by" not in r.stdout


def test_check_refuses_long_line_body(tmp_path):
    # R3: the dry run runs the same gates as the merge — no green dry run
    # where the merge would refuse.
    env = make_gh_mock(
        tmp_path,
        COMMITS_TSV="ghuser\tWf Zyx\twf@x.io\nme\tMe\tme@x.io",
        PR_BODY="ok\n" + "x" * 120 + "\n",
    )
    r = run_bash(f'bash "{PR_SH}" --check --head feat-x', env)
    assert r.returncode != 0
    assert r.stdout == ""
    assert "exceed" in r.stderr


def test_check_refuses_raw_token_body(tmp_path):
    env = make_gh_mock(tmp_path, PR_BODY="intro\n\n<!-- CODE_AUTHORS -->\n")
    r = run_bash(f'bash "{PR_SH}" --check --head feat-x', env)
    assert r.returncode != 0
    assert r.stdout == ""
    assert "CODE_AUTHORS" in r.stderr


# --- pr-refine script ---


def test_refine_lint_body_refuses_token_and_accepts_clean(tmp_path):
    bad = tmp_path / "bad.md"
    bad.write_text("intro\n\n<!-- CODE_AUTHORS -->\n")
    r = run_bash(f'bash "{REFINE_SH}" lint-body --body-file "{bad}"')
    assert r.returncode != 0
    assert "CODE_AUTHORS" in r.stderr
    ok = tmp_path / "ok.md"
    ok.write_text("intro\n\nCo-authored-by: W <w@x>\n")
    r = run_bash(f'bash "{REFINE_SH}" lint-body --body-file "{ok}"')
    assert r.returncode == 0
    assert "body ok" in r.stdout


@pytest.mark.parametrize(
    ("tsv", "flow"),
    [
        ("false\to/r\to/r", "flow=A"),  # same-repo head: flag false, push anyway
        ("true\tfork/r\to/r", "flow=A"),  # fork, maintainer can modify
        ("false\tfork/r\to/r", "flow=B"),  # fork, cannot modify
        ("false\t\to/r", "flow=B"),  # deleted fork: null head repo
    ],
)
def test_refine_observe_routes_on_repo_not_flag_alone(tmp_path, tsv, flow):
    # R10: maintainerCanModify is false for same-repo branches — Flow A iff the
    # flag is true OR the head repo is the base repo.
    env = make_gh_mock(tmp_path, OBSERVE_TSV=tsv)
    r = run_bash(f'bash "{REFINE_SH}" observe 157', env)
    assert r.returncode == 0
    assert "maintainerCanModify=" in r.stdout
    assert flow in r.stdout


# --- pr-refine routing eval: trigger phrasings must hit discriminating tokens ---
# Each phrasing names the tokens that distinguish it from a generic "PR" mention;
# the eval asserts those exact tokens, so a description containing only "pr" fails.
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


def skill_description(path):
    import re

    text = open(path).read()
    m = re.search(r"description: >-\n((?:  .*\n)+)", text)
    assert m, f"no folded description in {path}"
    return " ".join(line.strip() for line in m.group(1).splitlines())


def tokens(s):
    import re

    return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t and t not in STOPWORDS}


def matches_required(phrasing, description):
    return REQUIRED_TOKENS[phrasing] <= tokens(description)


@pytest.mark.parametrize("phrasing", list(REQUIRED_TOKENS))
def test_pr_refine_triggers_catch_contributor_pr_phrasings(phrasing):
    desc = skill_description(
        os.path.join(REPO_ROOT, "skills", "gh-router", "subskills", "pr-refine", "SKILL.md")
    )
    assert matches_required(phrasing, desc), (
        f"{phrasing!r} needs {sorted(REQUIRED_TOKENS[phrasing])} in the pr-refine description"
    )
    assert len(desc) <= 300


def test_generic_pr_token_alone_satisfies_no_phrasing():
    # R7 negative case, run through the same helper against a synthetic
    # description: refutable — weakening any REQUIRED set to {"pr"} fails it.
    for phrasing in REQUIRED_TOKENS:
        assert not matches_required(phrasing, "pr"), f"{phrasing!r} is satisfied by 'pr' alone"


def test_pr_refine_frontmatter_declares_negative_space():
    desc = skill_description(
        os.path.join(REPO_ROOT, "skills", "gh-router", "subskills", "pr-refine", "SKILL.md")
    )
    assert "pr-enhance" in desc
    assert "pr-land" in desc
    router = open(os.path.join(REPO_ROOT, "skills", "gh-router", "SKILL.md")).read()
    assert "pr-refine" in router
