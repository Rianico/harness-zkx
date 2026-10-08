#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# ///
"""pr.py — create pull request, watch every check, squash-merge (deterministic bytes)

Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--verbose] [--merge|--no-merge] [--draft] [--check] [--out-dir DIR] [--no-stamp] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; one stderr line per poll (mergeable_state + verdict); a conflicting or unresolved PR fails fast, exit 1
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; a conflicting or unresolved PR fails fast, refuses otherwise)
  --check : preflight + draft phase — run the merge gates, write <out-dir>/draft.json and
    <out-dir>/pr_body.md, and print only counts, the two paths, and one curation hint (no PR created)
  --out-dir DIR : directory for the --check draft files (default <repo-root>/.lsz/tmp); parents are created
  --draft : leave the PR a draft after stamping (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens
    (the caller owns the changelog) — the head was not stamped, so expect a red changelog gate
  --squash-message / --squash-message-file : explicit squash commit message (mutually exclusive)
  --verbose : full failure logs (gh run view bodies + gh pr checks tail); default is slim — failing run id(s) + one gh run view pointer
Draft handshake: every NEWLY CREATED PR is created as a draft (draft=true), stamped (commit+push), then explicitly
readied via `gh pr ready <num> --repo <repo>` so CI's ready_for_review event fires. A gh pr ready failure
prints the exact manual fix and exits 1: a draft that never went ready is not success. An existing open
PR is reused untouched — never readied, never re-drafted; a reused draft without --draft fails loudly with
the same manual remediation and exits 1.
Squash body is the PR body plus one Co-authored-by trailer per distinct PR commit author
except the merger (an explicit commit_message disables GitHub's own auto-attribution, so the
script rebuilds it). A body still holding the raw CODE_AUTHORS template token is refused pre-merge.
A squash merge never omits commit_message: --merge requires the explicit --squash-message (or
--squash-message-file); there is no PR-body fallback. --check still previews a message derived
from the body, and an empty or template-only body there without an explicit message is refused
(exit 1) instead of letting GitHub synthesize commit subjects.
Opening a PR requires a description: an empty body or the unfilled repo template is refused pre-create.
Commit title is one Conventional Commit line `type(scope): subject (#NUM)` <= 100 chars; a fix
body states Root, and the body stays at most 5 bullets.
Env: GH_TOKEN via gh auth. PR URL on stdout (draft paths on --check), progress on stderr. Fails loud, no secrets in logs.
Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref → default slim; --verbose dumps the logs
"""

import json as json
import os as os
import re as re
import subprocess as subprocess  # kept: part of the pre-split public surface of `pr`
import sys
import time as time  # kept: test seam — test_pr_watch patches pr.time.sleep
from collections.abc import (
    Callable as Callable,  # kept: part of the pre-split public surface of `pr`
)
from dataclasses import dataclass as dataclass  # kept: part of the pre-split public surface of `pr`
from pathlib import Path
from typing import NoReturn as NoReturn  # kept: part of the pre-split public surface of `pr`

import _github
from _changelog import _UNRELEASED_ATTR_RES as _UNRELEASED_ATTR_RES
from _changelog import _UNRELEASED_BULLET_RE as _UNRELEASED_BULLET_RE
from _changelog import _UNRELEASED_SECTION_RE as _UNRELEASED_SECTION_RE
from _changelog import _UNRELEASED_VERSION_END_RE as _UNRELEASED_VERSION_END_RE
from _changelog import _read_unreleased_block as _read_unreleased_block
from _changelog import _unreleased_attribution_re as _unreleased_attribution_re
from _changelog import stamp_changelog as stamp_changelog
from _changelog import unreleased_attributes_pr as unreleased_attributes_pr
from _check import CheckReport as CheckReport
from _check import check_trailers as check_trailers
from _check import check_trailers_report as check_trailers_report
from _draft import DRAFT_BODY_MAX_LINES as DRAFT_BODY_MAX_LINES
from _draft import DRAFT_BODY_PLACEHOLDER as DRAFT_BODY_PLACEHOLDER
from _draft import DRAFT_OUT_DIR as DRAFT_OUT_DIR
from _draft import DRAFT_SCHEMA as DRAFT_SCHEMA
from _draft import _draft_dirty as _draft_dirty
from _draft import _draft_range as _draft_range
from _draft import build_draft_payload as build_draft_payload
from _draft import cap_draft_body as cap_draft_body
from _draft import draft_commits as draft_commits
from _draft import resolve_out_dir as resolve_out_dir
from _draft import run_draft_phase as run_draft_phase
from _errors import CheckFailureError as CheckFailureError
from _errors import PrError as PrError
from _errors import RefusalError as RefusalError
from _errors import UsageError as UsageError
from _github import CONFLICT_FILES_MAX as CONFLICT_FILES_MAX
from _github import CONFLICT_HELPER as CONFLICT_HELPER
from _github import DEFAULT_TIMEOUT as DEFAULT_TIMEOUT
from _github import DIRTY_INTERVAL as DIRTY_INTERVAL
from _github import DIRTY_STRIKES as DIRTY_STRIKES
from _github import LOG_TIMEOUT as LOG_TIMEOUT
from _github import MERGE_STATE_INTERVAL as MERGE_STATE_INTERVAL
from _github import MERGE_STATE_TRIES as MERGE_STATE_TRIES
from _github import POLL_INTERVAL as POLL_INTERVAL
from _github import POLL_TRIES as POLL_TRIES
from _github import SLUG_PATTERN as SLUG_PATTERN
from _github import UNKNOWN_INTERVAL as UNKNOWN_INTERVAL
from _github import UNKNOWN_TRIES as UNKNOWN_TRIES
from _github import MergeFetch as MergeFetch
from _github import MergeObservation as MergeObservation
from _github import _authority_resolve as _authority_resolve
from _github import _digest_range_spec as _digest_range_spec
from _github import _local_base_from_authority as _local_base_from_authority
from _github import _remote_branch_exists as _remote_branch_exists
from _github import check_conflicts as check_conflicts
from _github import checks_verdict as checks_verdict
from _github import conflicting_files as conflicting_files
from _github import default_branch as default_branch
from _github import dump_failure_logs as dump_failure_logs
from _github import failing_run_ids as failing_run_ids
from _github import fetch_merge_state as fetch_merge_state
from _github import fetch_mergeability as fetch_mergeability
from _github import merge_state_verdict as merge_state_verdict
from _github import pr_conflict_verdict as pr_conflict_verdict
from _github import pr_url as pr_url
from _github import ready_pr as ready_pr
from _github import repo_remote_for_ref as repo_remote_for_ref
from _github import repo_slug_from_url as repo_slug_from_url
from _github import report_merge_refusal as report_merge_refusal
from _github import resolve_base as resolve_base
from _github import resolve_head as resolve_head
from _github import resolve_merge_state as resolve_merge_state
from _github import resolve_repo as resolve_repo
from _github import resolve_title_and_body as resolve_title_and_body
from _github import run_command as run_command
from _github import watch_checks as watch_checks
from _options import PrOptions as PrOptions
from _squash import AFTER_MARKERS as AFTER_MARKERS
from _squash import BEFORE_AFTER_ARROW as BEFORE_AFTER_ARROW
from _squash import BEFORE_MARKERS as BEFORE_MARKERS
from _squash import CHECKBOX_RE as CHECKBOX_RE
from _squash import CLOSES_LINE_RE as CLOSES_LINE_RE
from _squash import CLOSES_REF_RE as CLOSES_REF_RE
from _squash import CLOSING_RE as CLOSING_RE
from _squash import CODE_AUTHORS_TOKEN as CODE_AUTHORS_TOKEN
from _squash import CONVENTIONAL_TYPES as CONVENTIONAL_TYPES
from _squash import COPY_OVERLAP_THRESHOLD as COPY_OVERLAP_THRESHOLD
from _squash import COPY_TOKEN_FLOOR as COPY_TOKEN_FLOOR
from _squash import DEFAULT_TEMPLATE_PATH as DEFAULT_TEMPLATE_PATH
from _squash import DETAILS_BLOCK_RE as DETAILS_BLOCK_RE
from _squash import DETAILS_UNCLOSED_OPENER_RE as DETAILS_UNCLOSED_OPENER_RE
from _squash import DIRECTIVE_RE as DIRECTIVE_RE
from _squash import DOOR_RE as DOOR_RE
from _squash import EMAIL_KEY_RE as EMAIL_KEY_RE
from _squash import EMPTY_BULLET_RE as EMPTY_BULLET_RE
from _squash import FENCE_RE as FENCE_RE
from _squash import FIX_TYPE as FIX_TYPE
from _squash import HEADING_RE as HEADING_RE
from _squash import LABEL_ONLY_RE as LABEL_ONLY_RE
from _squash import MERMAID_FENCE_RE as MERMAID_FENCE_RE
from _squash import MERMAID_UNCLOSED_OPENER_RE as MERMAID_UNCLOSED_OPENER_RE
from _squash import PROCEDURAL_SECTION_RE as PROCEDURAL_SECTION_RE
from _squash import REVIEW_ONLY_SECTION_RE as REVIEW_ONLY_SECTION_RE
from _squash import ROLLBACK_RE as ROLLBACK_RE
from _squash import SQUASH_BODY_MAX_BULLETS as SQUASH_BODY_MAX_BULLETS
from _squash import SQUASH_BULLET_RE as SQUASH_BULLET_RE
from _squash import SQUASH_HEADING_RE as SQUASH_HEADING_RE
from _squash import SQUASH_LABEL_RE as SQUASH_LABEL_RE
from _squash import SQUASH_MESSAGE_MAX_LINES as SQUASH_MESSAGE_MAX_LINES
from _squash import SQUASH_MESSAGE_SPEC as SQUASH_MESSAGE_SPEC
from _squash import SQUASH_SECTIONS as SQUASH_SECTIONS
from _squash import SQUASH_TITLE_MAX as SQUASH_TITLE_MAX
from _squash import SQUASH_TITLE_RE as SQUASH_TITLE_RE
from _squash import TRAILER_RE as TRAILER_RE
from _squash import _copy_tokens as _copy_tokens
from _squash import _count_squash_bullets as _count_squash_bullets
from _squash import _evidence_marker_text as _evidence_marker_text
from _squash import _fenced_line_mask as _fenced_line_mask
from _squash import _is_label_line as _is_label_line
from _squash import _is_stop_line as _is_stop_line
from _squash import _refuse_squash as _refuse_squash
from _squash import _section_content as _section_content
from _squash import _section_key as _section_key
from _squash import _section_open as _section_open
from _squash import _states_rollback as _states_rollback
from _squash import _strip_unclosed as _strip_unclosed
from _squash import build_squash_message as build_squash_message
from _squash import check_closes_lines as check_closes_lines
from _squash import check_explicit_squash_message as check_explicit_squash_message
from _squash import check_raw_token as check_raw_token
from _squash import check_squash_body as check_squash_body
from _squash import check_squash_title as check_squash_title
from _squash import check_title_length as check_title_length
from _squash import clean_squash_body as clean_squash_body
from _squash import copy_body_coverage as copy_body_coverage
from _squash import copy_overlap as copy_overlap
from _squash import insert_trailers as insert_trailers
from _squash import is_closing_line as is_closing_line
from _squash import is_fallback_body as is_fallback_body
from _squash import is_trailer_line as is_trailer_line
from _squash import is_unfilled_body as is_unfilled_body
from _squash import pr_co_author_trailers as pr_co_author_trailers
from _squash import print_squash_message_required as print_squash_message_required
from _squash import refuse_mechanic_copy as refuse_mechanic_copy
from _squash import refuse_raw_token as refuse_raw_token
from _squash import refuse_unfilled_body as refuse_unfilled_body
from _squash import resolve_squash_message as resolve_squash_message
from _squash import split_squash_sections as split_squash_sections
from _squash import squash_message as squash_message
from _squash import trailer_email_key as trailer_email_key

# Annotated on purpose: a module-level variable annotation is what makes CPython 3.14 build
# the module's PEP 649 `__annotate__`/`__conditional_annotations__`. The pristine pr.py had
# the split's only one (`_UNRELEASED_ATTR_RES`), which now lives in `_changelog`; keeping
# one here keeps `dir(pr)` a superset of the pre-split surface.
_LIB_DIR: str = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import MalformedSpec as MalformedSpec
from range_authority import RangeRefusal as RangeRefusal
from range_authority import RangeResolution as RangeResolution
from range_authority import find_repo_root as find_repo_root
from range_authority import get_commit_summary as get_commit_summary
from range_authority import resolve_range as resolve_range


def print_usage() -> None:
    usage = """pr.py — create pull request, watch every check, squash-merge (deterministic bytes)
Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--verbose] [--merge|--no-merge] [--draft] [--check] [--out-dir DIR] [--no-stamp] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; one stderr line per poll (mergeable_state + verdict); a conflicting or unresolved PR fails fast, exit 1
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; a conflicting or unresolved PR fails fast, refuses otherwise)
  --check : preflight + draft phase — write <out-dir>/draft.json + <out-dir>/pr_body.md, print counts, both paths, one curation hint (no PR created; --out-dir DIR defaults to <repo-root>/.lsz/tmp, parents created)
  --draft : leave the PR a draft (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens (caller owns the changelog) — head unstamped, expect a red changelog gate
  --body/--body-file : required to open a PR; the caller drafts the description (pr-enhance workflow). An empty body or the unfilled repo template is refused.
  --squash-message/--squash-message-file : explicit squash commit message (mutually exclusive); REQUIRED with --merge — no PR-body fallback (spec: CONTEXT.md "Curated Squash Message"). --check still previews a derived message.
  --verbose : full failure logs (gh run view bodies + gh pr checks tail); default is slim — failing run id(s) + one gh run view pointer
Draft handshake: a NEWLY CREATED PR is created as a draft (draft=true), stamped (commit+push), then readied via gh pr ready so CI's ready_for_review fires; a failed flip prints the verbatim manual fix and exits 1. Existing open PRs are reused untouched — never readied, never re-drafted; a reused draft without --draft fails loudly with the same manual remediation and exits 1.
Squash body is the PR body plus one Co-authored-by trailer per distinct PR commit author except the merger (an explicit commit_message disables GitHub's own auto-attribution, so the script rebuilds it). A body still holding the raw CODE_AUTHORS template token is refused pre-merge.
Commit title is one Conventional Commit line `type(scope): subject (#NUM)` <= 100 chars; a fix body states Root, a body at most 5 bullets.
Env: GH_TOKEN via gh auth. PR URL on stdout, progress on stderr. Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref"""
    print(usage)


def parse_args(args: list[str]) -> PrOptions:
    base: str | None = None
    head: str | None = None
    title: str | None = None
    title_supplied = False
    body: str | None = None
    body_supplied = False
    body_file: Path | None = None
    out_dir: Path | None = None
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied = False
    watch = False
    merge = False
    check = False
    draft = False
    no_stamp = False
    verbose = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--base":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --base")
            base = args[i + 1]
            i += 2
        elif arg == "--head":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --head")
            head = args[i + 1]
            i += 2
        elif arg == "--title":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --title")
            title = args[i + 1]
            title_supplied = True
            i += 2
        elif arg == "--body":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --body")
            body = args[i + 1]
            body_supplied = True
            i += 2
        elif arg == "--body-file":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --body-file")
            body_file = Path(args[i + 1])
            body_supplied = True
            i += 2
        elif arg == "--out-dir":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --out-dir")
            out_dir = Path(args[i + 1])
            i += 2
        elif arg == "--squash-message":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --squash-message")
            squash_message = args[i + 1]
            squash_message_supplied = True
            i += 2
        elif arg == "--squash-message-file":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --squash-message-file")
            squash_message_file = Path(args[i + 1])
            squash_message_supplied = True
            i += 2
        elif arg == "--watch":
            watch = True
            i += 1
        elif arg == "--no-watch":
            watch = False
            i += 1
        elif arg == "--merge":
            merge = True
            i += 1
        elif arg == "--no-merge":
            merge = False
            i += 1
        elif arg == "--check":
            check = True
            i += 1
        elif arg == "--no-check":
            check = False
            i += 1
        elif arg == "--draft":
            draft = True
            i += 1
        elif arg == "--no-draft":
            draft = False
            i += 1
        elif arg == "--no-stamp":
            no_stamp = True
            i += 1
        elif arg == "--stamp":
            no_stamp = False
            i += 1
        elif arg == "--verbose":
            verbose = True
            i += 1
        elif arg in ("-h", "--help"):
            print_usage()
            sys.exit(0)
        else:
            raise UsageError(f"unknown arg: {arg}")

    if squash_message is not None and squash_message_file is not None:
        raise UsageError("--squash-message and --squash-message-file are mutually exclusive")

    return PrOptions(
        base=base,
        head=head,
        title=title,
        body=body,
        body_file=body_file,
        out_dir=out_dir,
        watch=watch,
        merge=merge,
        check=check,
        draft=draft,
        no_stamp=no_stamp,
        verbose=verbose,
        title_supplied=title_supplied,
        body_supplied=body_supplied,
        squash_message=squash_message,
        squash_message_file=squash_message_file,
        squash_message_supplied=squash_message_supplied,
    )


def resolve_squash_override(options: PrOptions, cwd: Path | None = None) -> tuple[str | None, bool]:
    explicit = options.squash_message
    if options.squash_message_file:
        mf = (
            options.squash_message_file
            if options.squash_message_file.is_absolute()
            else ((cwd or Path.cwd()) / options.squash_message_file)
        )
        if not mf.is_file():
            raise UsageError(
                f"squash message file not found or not readable: {options.squash_message_file}"
            )
        try:
            # utf-8-sig drops a BOM so `\ufeff## Summary` never rides in as prose (F11).
            explicit = mf.read_text(encoding="utf-8-sig")
        except OSError:
            raise UsageError(
                f"squash message file not found or not readable: {options.squash_message_file}"
            ) from None
    return explicit, options.squash_message_supplied


def finalize_squash_message(repo: str, num: str, msg: str, cwd: Path | None = None) -> str:
    merger_res = _github.run_command(
        ["gh", "api", "user", "--jq", ".login"],
        cwd=cwd,
    )
    if merger_res.returncode != 0:
        print(
            f"refusing squash message: could not resolve current user login via gh api user: {merger_res.stderr.strip()}",
            file=sys.stderr,
        )
        raise RefusalError("could not resolve current user login")
    merger = merger_res.stdout.strip()
    tsv_res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{num}/commits",
            "--jq",
            '.[] | [(.author.login // ""), (.commit.author.name // ""), (.commit.author.email // "")] | @tsv',
        ],
        cwd=cwd,
    )
    if tsv_res.returncode != 0:
        print(
            f"refusing squash message: could not enumerate PR #{num} commit authors (check network / GH_TOKEN scopes); re-run rather than merge without attribution",
            file=sys.stderr,
        )
        raise RefusalError(f"could not enumerate PR #{num} commit authors")
    return build_squash_message(msg, merger, tsv_res.stdout).rstrip("\n")


def create_or_reuse_pr(
    repo: str,
    head_ref: str,
    base: str,
    title: str,
    body: str,
    title_supplied: bool,
    body_supplied: bool,
    draft: bool = False,
    cwd: Path | None = None,
) -> tuple[str, str, str, bool]:
    """Create or reuse open PR for head_ref. Returns (num, final_title, final_body, created).

    New PRs are always created as a draft (draft=true); the caller flips them ready after
    stamping via ready_pr, honoring the retained draft flag at the flip, not here. An
    existing open PR is reused untouched: its draft state is never changed. A reused draft
    PR without --draft is a silent no-op hole: it now refuses (exit 1) with the verbatim
    manual remediation instead of returning success on a draft that never runs CI.
    """
    template_path = (cwd / DEFAULT_TEMPLATE_PATH) if cwd else DEFAULT_TEMPLATE_PATH
    if body_supplied and is_unfilled_body(body, template_path=template_path):
        refuse_unfilled_body(body)

    owner = repo.split("/")[0]
    res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls?head={owner}:{head_ref}&state=open",
            "--jq",
            r'.[0] // empty | "\(.number)\t\(.isDraft)"',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to query open PR for head {head_ref}: {res.stderr.strip() or 'gh api failed'}"
        )
    existing = res.stdout.strip()
    if existing and existing != "null":
        fields = existing.split("\t")
        num = fields[0].strip()
        is_draft = len(fields) > 1 and fields[1].strip().lower() == "true"
        print(f"found existing PR #{num}", file=sys.stderr)
        if is_draft and not draft:
            print(
                f"reused PR #{num} is still a draft and --draft was not passed; "
                "reuse never mutates draft state, so CI never ran",
                file=sys.stderr,
            )
            print(
                f"remediation: PR #{num} is still a draft; run manually: gh pr ready {num} --repo {repo}",
                file=sys.stderr,
            )
            raise RefusalError(f"reused PR #{num} is still a draft")
        patch_args: list[str] = []
        updated_fields: list[str] = []
        final_title = title
        final_body = body

        if title_supplied:
            patch_args.extend(["-f", f"title={title}"])
            updated_fields.append("title")
        else:
            t_res = _github.run_command(
                ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".title // empty"],
                cwd=cwd,
            )
            if t_res.returncode != 0:
                raise PrError(
                    f"failed to fetch title for PR #{num}: {t_res.stderr.strip() or 'gh api failed'}"
                )
            if t_res.stdout.strip():
                final_title = t_res.stdout.strip()

        if body_supplied:
            patch_args.extend(["-f", f"body={body}"])
            updated_fields.append("body")
        else:
            b_res = _github.run_command(
                ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", '.body // ""'],
                cwd=cwd,
            )
            if b_res.returncode != 0:
                raise PrError(
                    f"failed to fetch body for PR #{num}: {b_res.stderr.strip() or 'gh api failed'}"
                )
            final_body = b_res.stdout

        if patch_args:
            patch_res = _github.run_command(
                ["gh", "api", f"repos/{repo}/pulls/{num}", "-X", "PATCH", *patch_args],
                cwd=cwd,
            )
            if patch_res.returncode != 0:
                raise PrError(
                    f"failed to update PR #{num}: {patch_res.stderr.strip() or 'gh api failed'}"
                )
            fields_str = ", ".join(updated_fields)
            print(f"updating PR #{num}: {fields_str}", file=sys.stderr)
        return num, final_title, final_body, False

    final_body = body
    if not body_supplied:
        print("refusing to open PR: no --body/--body-file supplied", file=sys.stderr)
        print(
            "remediation: draft the description from the git-diff-digest surface "
            "(skills/gh-router/subskills/git-diff-digest), then re-run with --body-file",
            file=sys.stderr,
        )
        raise RefusalError("no PR body supplied")

    create_res = _github.run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls",
            "-X",
            "POST",
            "-f",
            f"title={title}",
            "-f",
            f"head={head_ref}",
            "-f",
            f"base={base}",
            "-f",
            f"body={final_body}",
            "-F",
            "draft=true",
            "--jq",
            ".number",
        ],
        cwd=cwd,
    )
    if create_res.returncode != 0:
        raise PrError(f"failed to create PR: {create_res.stderr.strip() or 'gh api failed'}")
    num = create_res.stdout.strip()
    print(f"created PR #{num} (draft)", file=sys.stderr)
    return num, title, final_body, True


def merge_pr(
    repo: str,
    num: str,
    base: str,
    title: str,
    body: str,
    template_path: Path | None = None,
    cwd: Path | None = None,
    squash_message_override: str | None = None,
    squash_message_supplied: bool = False,
) -> bool:
    if title.strip():
        check_squash_title(title, num)
    else:
        check_title_length(title, num)
    obs = resolve_merge_state(
        repo,
        num,
        fetch=fetch_merge_state,
        unknown_tries=MERGE_STATE_TRIES,
        unknown_interval=MERGE_STATE_INTERVAL,
        cwd=cwd,
    )
    if obs.verdict != "clean":
        if obs.verdict in ("conflicting", "unknown"):
            report_merge_refusal(obs, repo, num, cwd=cwd)
        print(f"refusing to merge: mergeable_state={obs.state} (not clean)", file=sys.stderr)
        return False
    header = f"{title} (#{num})"
    merge_args: list[str] = [
        "-f",
        "merge_method=squash",
        "-f",
        f"commit_title={header}",
    ]
    try:
        msg = resolve_squash_message(
            body,
            explicit=squash_message_override,
            supplied=squash_message_supplied,
            template_path=template_path,
            require_explicit=True,
        )
    except RefusalError:
        return False
    try:
        check_squash_body(
            msg,
            title=title,
            pr_link=f"https://github.com/{repo}/pull/{num}",
        )
    except RefusalError:
        return False
    try:
        msg = finalize_squash_message(repo, num, msg, cwd=cwd)
    except RefusalError:
        return False
    merge_args.extend(["-f", f"commit_message={msg}"])

    m_res = _github.run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}/merge", "-X", "PUT", *merge_args],
        cwd=cwd,
    )
    if m_res.returncode != 0:
        print(f"merge failed: {m_res.stderr.strip() or 'gh api failed'}", file=sys.stderr)
        return False
    print(f"merged #{num} (squash) to {base}", file=sys.stderr)
    return True


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        options = parse_args(argv)
        head = resolve_head(options.head)
        title, body, title_supplied, body_supplied = resolve_title_and_body(options)
        squash_override, squash_supplied = resolve_squash_override(options)
        # `--check` is the read-only draft preflight: the merge-only explicit
        # squash-message requirement must not gate it (spec 3).
        if options.merge and not options.check:
            if not squash_supplied:
                print_squash_message_required()
                return 1
            # Fail closed before any gh mutation: hold the explicit text to the copy
            # check and the shape gate here too, so a pasted description or an
            # ephemera-only message names its defect before `PR <url>` is ever printed
            # (T2). `merge_pr` keeps its own authoritative check against the final body.
            refuse_mechanic_copy(squash_override or "", body)
            check_explicit_squash_message(squash_override or "")
            if not clean_squash_body(squash_override or "").strip():
                raise UsageError("--squash-message is empty")
        repo = resolve_repo(head)

        if options.check:
            return run_draft_phase(
                options=options,
                repo=repo,
                head_ref=head,
                title=title,
                body=body,
                body_supplied=body_supplied,
                squash_message_override=squash_override,
                squash_message_supplied=squash_supplied,
            )

        base = resolve_base(options.base, repo)
        num, final_title, final_body, created = create_or_reuse_pr(
            repo=repo,
            head_ref=head,
            base=base,
            title=title,
            body=body,
            title_supplied=title_supplied,
            body_supplied=body_supplied,
            draft=options.draft,
        )
        url = pr_url(repo, num)
        print(f"PR {url}")

        if not options.no_stamp:
            _ = stamp_changelog(head, num)
            if created and not unreleased_attributes_pr(num):
                if _read_unreleased_block() is None:
                    print(
                        "warning: no ## [Unreleased] section in CHANGELOG.md; "
                        "the Ledger floor gate requires one before this PR can land. "
                        f"Add the section with an entry ending in (#{num}).",
                        file=sys.stderr,
                    )
                elif options.draft:
                    print(
                        f"note: no ## [Unreleased] entry carries (#{num}); "
                        "the Ledger floor gate rejects this PR once it goes ready. "
                        f"Add an entry ending in (#{num}) before you flip it ready "
                        "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR).",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"warning: no ## [Unreleased] entry carries (#{num}); "
                        "the Ledger floor gate\n"
                        f'("#{num} carries no entries in ## [Unreleased]") will reject this PR on the\n'
                        f"ready flip. Add an entry ending in (#{num}), commit it to this branch, or\n"
                        "leave the PR draft until the entry lands "
                        "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR).",
                        file=sys.stderr,
                    )
        elif created:
            if not unreleased_attributes_pr(num):
                if _read_unreleased_block() is None:
                    print(
                        "warning: no ## [Unreleased] section in CHANGELOG.md; "
                        "the Ledger floor gate requires one before this PR can land. "
                        f"Add the section with an entry ending in (#{num}).",
                        file=sys.stderr,
                    )
                elif options.draft:
                    print(
                        f"note: --no-stamp: head was not stamped for PR #{num} — "
                        f"no ## [Unreleased] entry carries (#{num}); the Ledger floor gate "
                        "(changelog gate) rejects this PR once it goes ready. "
                        f"Add an entry ending in (#{num}) before you flip it ready.",
                        file=sys.stderr,
                    )
                else:
                    print(
                        f"warning: --no-stamp: head was not stamped for PR #{num} — "
                        f"no ## [Unreleased] entry carries (#{num}); the Ledger floor gate "
                        f'("#{num} carries no entries in ## [Unreleased]") will reject this PR '
                        "and the changelog gate stays red "
                        "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR). "
                        f"Add an entry ending in (#{num}) and push it, or re-run without --no-stamp.",
                        file=sys.stderr,
                    )

        if created and not options.draft:
            if not ready_pr(repo, num):
                return 1

        if options.watch:
            if not watch_checks(repo, num, base, verbose=options.verbose):
                return 1

        if options.merge:
            if not options.watch:
                if not watch_checks(repo, num, base, verbose=options.verbose):
                    return 1
            if not merge_pr(
                repo=repo,
                num=num,
                base=base,
                title=final_title,
                body=final_body,
                squash_message_override=squash_override,
                squash_message_supplied=squash_supplied,
            ):
                return 1
        return 0

    except UsageError as e:
        print(f"{e}", file=sys.stderr)
        return 2
    except RefusalError:
        return 1
    except CheckFailureError:
        return 1
    except PrError as e:
        print(f"pr error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
