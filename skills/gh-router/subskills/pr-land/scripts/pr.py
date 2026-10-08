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
A squash merge never omits commit_message: it is either the explicit --squash-message (file) or a
message derived from the PR body. An empty or template-only body without an explicit message is
refused (exit 1) instead of letting GitHub synthesize commit subjects.
Opening a PR requires a description: an empty body or the unfilled repo template is refused pre-create.
Commit title is one Conventional Commit line `type(scope): subject (#NUM)` <= 100 chars; a fix
body states Root, and the body stays at most 5 bullets.
Env: GH_TOKEN via gh auth. PR URL on stdout (draft paths on --check), progress on stderr. Fails loud, no secrets in logs.
Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref → default slim; --verbose dumps the logs
"""

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)
from range_authority import (
    MalformedSpec,
    RangeRefusal,
    RangeResolution,
    find_repo_root,
    get_commit_summary,
    resolve_range,
)

SLUG_PATTERN = re.compile(r"^[^/: \t\r\n]+/[^/: \t\r\n]+$")
TRAILER_RE = re.compile(r"^[ \t]*co-authored-by:[ \t]*", re.IGNORECASE)
EMAIL_KEY_RE = re.compile(r"^[ \t]*co-authored-by:[^<]*<([^<>]+)>", re.IGNORECASE)
CLOSING_RE = re.compile(
    r"^[ \t]*(closes?|closed|fixes?|fixed|resolves?|resolved|refs?)[ \t]*:?[ \t]+(#[0-9]|GH-[0-9]|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9])",
    re.IGNORECASE,
)
PROCEDURAL_SECTION_RE = re.compile(r"^#{1,6}\s+(Checklist|Landing)\b", re.IGNORECASE)
REVIEW_ONLY_SECTION_RE = re.compile(
    r"^#{1,6}\s+(Architecture|Verification Evidence)\b", re.IGNORECASE
)
MERMAID_FENCE_RE = re.compile(
    r"^[ \t]*```mermaid\b.*?^[ \t]*```[ \t]*$", re.DOTALL | re.MULTILINE | re.IGNORECASE
)
MERMAID_UNCLOSED_OPENER_RE = re.compile(r"^[ \t]*```mermaid\b", re.IGNORECASE)
DETAILS_BLOCK_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?<details\b.*?</details>", re.DOTALL | re.MULTILINE | re.IGNORECASE
)
DETAILS_UNCLOSED_OPENER_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?<details\b", re.MULTILINE | re.IGNORECASE
)
HEADING_RE = re.compile(r"^#{1,6}\s+\S")
DIRECTIVE_RE = re.compile(r"^[ \t]*(Landing|Ledger-Waiver):", re.IGNORECASE)
EMPTY_BULLET_RE = re.compile(r"^[ \t]*[*+-][ \t]*$")
CHECKBOX_RE = re.compile(r"^[ \t]*(?:[-*+][ \t]+)?\[[ xX]\](?:[ \t]|$)")
SQUASH_BULLET_RE = re.compile(r"^[ \t]*(?:[*+-]|\d+[.)])[ \t]+\S")
SQUASH_TITLE_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<breaking>!)?:[ \t]+(?P<subject>\S.*)$"
)
SQUASH_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<name>.+?)[ \t]*#*[ \t]*$")
SQUASH_LABEL_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*)?(?P<name>[A-Za-z][A-Za-z &/-]*?)(?:\*\*)?[ \t]*:[ \t]*(?:\*\*)?[ \t]*(?P<rest>.*)$"
)
# The shipped PR template names containment with `**Rollback / containment:**`, so that
# label opens Blast Radius just as a `Door:` line does; `Door:` stays canonical.
DOOR_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*)?(?:door|rollback[ \t]*/[ \t]*containment)(?:\*\*)?[ \t]*:",
    re.IGNORECASE,
)
ROLLBACK_RE = re.compile(r"rollback", re.IGNORECASE)
CLOSES_REF_RE = re.compile(
    r"^(?:closes?|closed|fix(?:es|ed)?|resolve[sd]?)[ \t]+#\d", re.IGNORECASE
)
CLOSES_LINE_RE = re.compile(
    r"^(?:closes?|closed|fix(?:es|ed)?|resolve[sd]?)[ \t]+#\d+$", re.IGNORECASE
)

_UNRELEASED_BULLET_RE = re.compile(r"^[*+-]\s+")
_UNRELEASED_SECTION_RE = re.compile(r"^###\s+")
_UNRELEASED_VERSION_END_RE = re.compile(r"^## \[[^\]]+\]", re.MULTILINE)
_UNRELEASED_ATTR_RES: dict[str, re.Pattern[str]] = {}
SQUASH_TITLE_MAX = 100
# The squash body stays one screen: a short Core line, then the optional parts.
SQUASH_BODY_MAX_BULLETS = 5
CONVENTIONAL_TYPES = frozenset(
    {
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
    }
)
FIX_TYPE = "fix"
# Canonical body parts (the PR Body Contract) and the label aliases that open them.
SQUASH_SECTIONS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "what changed", "core"),
    "root_cause": ("root cause", "root"),
    "blast_radius": ("blast radius & safety", "blast radius and safety", "blast radius"),
    "evidence": ("evidence", "proof"),
    "links": ("links", "related issues"),
}
BEFORE_AFTER_ARROW = ("\u2192", "->")
BEFORE_MARKERS = ("before", "was", "old", "prior")
AFTER_MARKERS = ("after", "now", "new")
# A bare label line (`**Before (command + output):**`) ends at its colon: it names a slot
# and states no output, so the Evidence gate counts it only when output follows it.
LABEL_ONLY_RE = re.compile(r":[ \t]*(?:[*_`]+[ \t]*)*$")
CODE_AUTHORS_TOKEN = "CODE_AUTHORS"
DEFAULT_TEMPLATE_PATH = Path(".github/pull_request_template.md")
DRAFT_OUT_DIR = Path(".lsz") / "tmp"
DRAFT_SCHEMA = "gh-router/pr-land/draft@1"
DRAFT_BODY_MAX_LINES = 15
DRAFT_BODY_PLACEHOLDER = (
    "<!-- draft: no authored PR body resolved; replace this file with the curated description -->\n"
    "## Summary\n\n## What Changed\n\n## Blast Radius & Safety\n\n## Evidence\n"
)
POLL_TRIES = 60
POLL_INTERVAL = 10.0
# Mergeability is computed lazily, so a `null`/`unknown` reading is retried UNKNOWN_TRIES times
# UNKNOWN_INTERVAL apart before the gate refuses; the merge-wait shares that budget.
UNKNOWN_TRIES = 5
UNKNOWN_INTERVAL = 2.0
MERGE_STATE_TRIES = UNKNOWN_TRIES
MERGE_STATE_INTERVAL = UNKNOWN_INTERVAL
# A `dirty` reading is confirmed DIRTY_STRIKES times, DIRTY_INTERVAL apart, before it fails the gate.
DIRTY_STRIKES = 2
DIRTY_INTERVAL = 3.0
CONFLICT_FILES_MAX = 10
CONFLICT_HELPER = (
    "uv run skills/gh-router/subskills/pr-conflict/scripts/extract_conflict_context.py"
)
DEFAULT_TIMEOUT = 30.0
LOG_TIMEOUT = 60.0


class PrError(Exception):
    """Base exception for pr module."""


class UsageError(PrError):
    """Usage or configuration error (exit code 2)."""


class RefusalError(PrError):
    """Operation refused by policy (exit code 1)."""


class CheckFailureError(PrError):
    """Checks failed (exit code 1)."""


def run_command(
    cmd: list[str],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    cwd: Path | None = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            cwd=cwd,
            check=check,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        cmd_str = " ".join(cmd)
        raise PrError(f"command timed out after {timeout}s: {cmd_str}") from e


@dataclass(frozen=True)
class PrOptions:
    base: str | None = None
    head: str | None = None
    title: str | None = None
    body: str | None = None
    body_file: Path | None = None
    out_dir: Path | None = None
    watch: bool = False
    merge: bool = False
    check: bool = False
    draft: bool = False
    no_stamp: bool = False
    title_supplied: bool = False
    body_supplied: bool = False
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied: bool = False
    verbose: bool = False


def print_usage() -> None:
    usage = """pr.py — create pull request, watch every check, squash-merge (deterministic bytes)
Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--verbose] [--merge|--no-merge] [--draft] [--check] [--out-dir DIR] [--no-stamp] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; one stderr line per poll (mergeable_state + verdict); a conflicting or unresolved PR fails fast, exit 1
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; a conflicting or unresolved PR fails fast, refuses otherwise)
  --check : preflight + draft phase — write <out-dir>/draft.json + <out-dir>/pr_body.md, print counts, both paths, one curation hint (no PR created; --out-dir DIR defaults to <repo-root>/.lsz/tmp, parents created)
  --draft : leave the PR a draft (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens (caller owns the changelog) — head unstamped, expect a red changelog gate
  --body/--body-file : required to open a PR; the caller drafts the description (pr-enhance workflow). An empty body or the unfilled repo template is refused.
  --squash-message/--squash-message-file : explicit squash commit message (mutually exclusive); a squash merge never omits commit_message (explicit or derived) — an empty/template body without an explicit message is refused (exit 1), never GitHub's commit-subject synthesis.
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


def resolve_head(head_ref: str | None = None, cwd: Path | None = None) -> str:
    if not head_ref:
        res = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
        )
        if res.returncode != 0:
            raise UsageError("cannot resolve HEAD ref")
        head_ref = res.stdout.strip()
    if head_ref in ("HEAD", "main"):
        raise UsageError(f"refusing to open PR from {head_ref}")
    return head_ref


def repo_remote_for_ref(ref: str | None = None, cwd: Path | None = None) -> str:
    if not ref:
        res = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
        )
        ref = res.stdout.strip() if res.returncode == 0 else ""
    if ref:
        push_remote_res = run_command(
            ["git", "config", "--get", f"branch.{ref}.pushRemote"],
            cwd=cwd,
        )
        val = push_remote_res.stdout.strip()
        if push_remote_res.returncode == 0 and val:
            return val
        remote_res = run_command(
            ["git", "config", "--get", f"branch.{ref}.remote"],
            cwd=cwd,
        )
        val = remote_res.stdout.strip()
        if remote_res.returncode == 0 and val:
            return val
    return "origin"


def repo_slug_from_url(url: str) -> str | None:
    if not url:
        return None
    s = url.strip()
    s = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://", "", s)
    s = re.sub(r"^[^/@]*@", "", s)
    s = re.sub(r"^[^/:]+[:/]", "", s)
    s = re.sub(r"/+$", "", s)
    s = re.sub(r"\.git$", "", s)
    s = re.sub(r"/+$", "", s)
    if SLUG_PATTERN.match(s):
        return s
    return None


def resolve_repo(head_ref: str | None = None, cwd: Path | None = None) -> str:
    remote = repo_remote_for_ref(head_ref, cwd=cwd)
    url_res = run_command(
        ["git", "remote", "get-url", "--push", remote],
        cwd=cwd,
    )
    url = url_res.stdout.strip() if url_res.returncode == 0 else ""
    if not url:
        origin_res = run_command(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd,
        )
        url = origin_res.stdout.strip() if origin_res.returncode == 0 else ""
    slug = repo_slug_from_url(url)
    if not slug:
        gh_res = run_command(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=cwd,
        )
        gh_slug = gh_res.stdout.strip() if gh_res.returncode == 0 else ""
        if gh_slug and SLUG_PATTERN.match(gh_slug):
            slug = gh_slug
    if not slug:
        raise UsageError("cannot resolve repo slug (no GitHub remote for branch/origin)")
    return slug


def default_branch(repo: str, cwd: Path | None = None) -> str | None:
    res = run_command(
        ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
        cwd=cwd,
    )
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip()
    return None


def _authority_resolve(spec: str, mode: str, cwd: Path | None = None) -> RangeResolution:
    """Resolve *spec* through the shared range authority inside the target repo.

    resolve_range discovers its repo from the process cwd, so temporarily
    chdir when the caller targets another checkout. Restores cwd on return.
    """
    if cwd is None:
        return resolve_range(spec, mode)
    previous = Path.cwd()
    target = cwd if cwd.is_absolute() else previous / cwd
    os.chdir(target)
    try:
        return resolve_range(spec, mode)
    finally:
        os.chdir(previous)


def _remote_branch_exists(name: str, cwd: Path | None = None) -> bool:
    """True when refs/remotes/origin/<name> resolves locally (no network)."""
    res = run_command(
        ["git", "rev-parse", "--verify", "-q", f"refs/remotes/origin/{name}"],
        cwd=cwd,
    )
    return res.returncode == 0


def _local_base_from_authority(cwd: Path | None = None) -> str:
    """Resolve the local base through the shared range authority (bare branch name).

    Single-ref resolution walks the authority's ordered local candidates
    (origin/HEAD, then origin/main, then origin/master) without touching the
    network. The result is stripped to the bare branch name GitHub's
    `-f base=` expects.
    """
    resolution = _authority_resolve("HEAD", "..", cwd)
    base_ref = resolution.base_ref
    if base_ref == "origin/HEAD":
        sym = run_command(
            ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
            cwd=cwd,
        )
        if sym.returncode == 0 and sym.stdout.strip():
            out = sym.stdout.strip()
            if out.startswith("origin/"):
                out = out.removeprefix("origin/")
            if out and _remote_branch_exists(out, cwd=cwd):
                return out
            for fallback in ("main", "master"):
                if _remote_branch_exists(fallback, cwd=cwd):
                    return fallback
        raise RefusalError(
            "cannot resolve PR base: the git-diff-digest range authority "
            "resolved origin/HEAD but it names no branch"
        )
    if base_ref.startswith("origin/"):
        return base_ref.removeprefix("origin/")
    return base_ref


def _digest_range_spec(base: str, head_ref: str, cwd: Path | None = None) -> str:
    """Build the `git log` range so trailer authors equal the digest's commit set.

    The resolved base goes first as a two-dot range; when it cannot resolve
    locally the digest's own single-ref derivation is used instead. Raises
    RangeRefusal when neither resolves.
    """
    try:
        resolution = _authority_resolve(f"{base}..{head_ref}", "..", cwd)
    except RangeRefusal:
        resolution = _authority_resolve(head_ref, "..", cwd)
    return f"{resolution.base_ref}..{head_ref}"


def resolve_base(base: str | None, repo: str, cwd: Path | None = None) -> str:
    if base:
        return base
    b = default_branch(repo, cwd=cwd)
    if b:
        return b
    sym_res = run_command(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        cwd=cwd,
    )
    if sym_res.returncode == 0 and sym_res.stdout.strip():
        out = sym_res.stdout.strip()
        if out.startswith("origin/"):
            out = out.removeprefix("origin/")
        if out and _remote_branch_exists(out, cwd=cwd):
            return out
    try:
        return _local_base_from_authority(cwd=cwd)
    except RangeRefusal as exc:
        raise RefusalError(
            "cannot resolve PR base: no explicit --base, no GitHub default_branch, "
            "and the git-diff-digest range authority found no local base "
            f"({exc})"
        ) from exc


def resolve_title_and_body(
    options: PrOptions, cwd: Path | None = None
) -> tuple[str, str, bool, bool]:
    title = options.title
    title_supplied = options.title_supplied
    if not title:
        if options.head:
            res = run_command(
                ["git", "log", "-1", "--pretty=%s", options.head],
                cwd=cwd,
            )
            if res.returncode == 0 and res.stdout.strip():
                title = res.stdout.strip()
        if not title:
            res = run_command(
                ["git", "log", "-1", "--pretty=%s"],
                cwd=cwd,
            )
            title = res.stdout.strip() if res.returncode == 0 else ""

    body = options.body or ""
    body_supplied = options.body_supplied
    if options.body_file:
        bf = (
            options.body_file
            if options.body_file.is_absolute()
            else ((cwd or Path.cwd()) / options.body_file)
        )
        if not bf.is_file():
            raise UsageError(f"body file not found or not readable: {options.body_file}")
        try:
            body = bf.read_text(encoding="utf-8")
        except OSError:
            raise UsageError(f"body file not found or not readable: {options.body_file}") from None
        body_supplied = True

    return title, body, title_supplied, body_supplied


def checks_verdict(payload: str) -> str:
    """Evaluate checks payload (name<TAB>bucket lines) returning 'success', 'failure', or 'pending'."""
    total = 0
    failed = 0
    pending = 0
    passed = 0
    skipping = 0
    for line in payload.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            bucket = parts[1].strip()
        else:
            tokens = line.split()
            bucket = tokens[-1] if len(tokens) >= 2 else line
        total += 1
        if bucket in ("fail", "cancel"):
            failed += 1
        elif bucket == "pass":
            passed += 1
        elif bucket == "skipping":
            skipping += 1
        else:
            pending += 1

    if failed > 0:
        return "failure"
    if total == 0 or pending > 0:
        return "pending"
    if passed == 0 and skipping > 0:
        # All reported checks skipped (draft PRs get all-skipped runs): zero CI is not green.
        return "pending"
    return "success"


def pr_conflict_verdict(mergeable: str | None, state: str | None) -> str:
    m = (mergeable or "").strip()
    s = (state or "").strip()
    if m in ("false", "CONFLICTING"):
        return "conflicting"
    if s in ("dirty", "DIRTY"):
        return "conflicting"
    if s in ("behind", "BEHIND"):
        return "behind"
    if s in ("unknown", "UNKNOWN", ""):
        return "unknown"
    if m in ("null", ""):
        return "unknown"
    return "clean"


def trailer_email_key(line: str) -> str:
    m = EMAIL_KEY_RE.search(line)
    if m:
        return m.group(1).strip().lower()
    return ""


def is_trailer_line(line: str) -> bool:
    return bool(TRAILER_RE.search(line))


def is_closing_line(line: str) -> bool:
    return bool(CLOSING_RE.search(line))


def pr_co_author_trailers(tsv: str, merger: str = "", body: str = "") -> str:
    merger_key = merger.strip().lower()
    existing_emails: set[str] = set()
    for line in body.splitlines():
        k = trailer_email_key(line)
        if k:
            existing_emails.add(k)

    seen: set[str] = set()
    trailers: list[str] = []

    for row in tsv.splitlines():
        if not row:
            continue
        parts = row.split("\t")
        login = parts[0].strip().lower() if len(parts) > 0 else ""
        name = parts[1].strip() if len(parts) > 1 else ""
        email = parts[2].strip() if len(parts) > 2 else ""

        if not name or not email:
            continue
        if merger_key and (login == merger_key or email.lower() == merger_key):
            continue
        key = email.lower()
        if key in seen or key in existing_emails:
            continue
        seen.add(key)
        trailers.append(f"Co-authored-by: {name} <{email}>")

    if not trailers:
        return ""
    return "\n".join(trailers) + "\n"


def insert_trailers(body: str, new_text: str) -> str:
    new_text_stripped = new_text.strip("\n")
    new_trailers = (
        [line for line in new_text_stripped.split("\n") if line.strip()]
        if new_text_stripped
        else []
    )

    seen: set[str] = set()
    existing_trailers: list[str] = []
    stripped_lines: list[str] = []
    dupes = False
    below = False
    closing_seen = False

    for line in body.splitlines():
        if is_trailer_line(line):
            key = trailer_email_key(line)
            if key:
                if key in seen:
                    dupes = True
                else:
                    seen.add(key)
                    existing_trailers.append(line)
                if closing_seen:
                    below = True
                continue
        if not closing_seen and is_closing_line(line):
            closing_seen = True
        stripped_lines.append(line)

    if not new_trailers and not dupes and not below:
        return body

    before_lines: list[str] = []
    after_lines: list[str] = []
    found_closing = False
    for line in stripped_lines:
        if not found_closing and is_closing_line(line):
            found_closing = True
            after_lines.append(line)
        elif not found_closing:
            before_lines.append(line)
        else:
            after_lines.append(line)

    all_trailers = existing_trailers + new_trailers
    all_str = "\n".join(all_trailers) if all_trailers else ""

    before = "\n".join(before_lines).rstrip("\n")
    after = "\n".join(after_lines).strip("\n")

    out = before
    if all_str:
        if out:
            out = out + "\n\n" + all_str
        else:
            out = all_str
        if after:
            out = out + "\n\n" + after
    else:
        if after:
            if out:
                out = out + "\n" + after
            else:
                out = after

    if body.endswith("\n"):
        out += "\n"
    return out


def check_raw_token(text: str, token: str = CODE_AUTHORS_TOKEN) -> bool:
    in_comment = False
    for line in text.splitlines(keepends=True):
        idx = 0
        while idx < len(line):
            if not in_comment:
                start = line.find("<!--", idx)
                if start == -1:
                    break
                in_comment = True
                idx = start + 4
            else:
                end = line.find("-->", idx)
                if end == -1:
                    if token in line[idx:]:
                        return True
                    break
                if token in line[idx:end]:
                    return True
                in_comment = False
                idx = end + 3
    return False


def refuse_raw_token(text: str, token: str = CODE_AUTHORS_TOKEN) -> None:
    if check_raw_token(text, token):
        print(f"refusing squash message: raw {token} token still present", file=sys.stderr)
        print(
            "remediation: replace the token with Co-authored-by lines for outside contributors (or delete the block), then re-run",
            file=sys.stderr,
        )
        raise RefusalError(f"raw {token} token still present")


def check_title_length(title: str, num: str | int) -> None:
    header = f"{title} (#{num})"
    if len(header) > SQUASH_TITLE_MAX:
        print(
            f"refusing squash merge: commit title exceeds {SQUASH_TITLE_MAX} chars ({len(header)}): {header}",
            file=sys.stderr,
        )
        print("remediation: shorten the PR title, then re-run", file=sys.stderr)
        raise RefusalError(f"commit title exceeds {SQUASH_TITLE_MAX} chars: {header}")


def _refuse_squash(message: str, remediation: str) -> NoReturn:
    print(f"refusing squash merge: {message}", file=sys.stderr)
    print(f"remediation: {remediation}", file=sys.stderr)
    raise RefusalError(message)


def check_squash_title(title: str, num: str | int) -> None:
    """Title gate: `type(scope): subject (#N)` — a Conventional Commit line, <= 100 chars.

    The length budget reports first, so an over-long title keeps its one message.
    The scope and the breaking `!` stay optional, as in the Convention.
    """
    check_title_length(title, num)
    match = SQUASH_TITLE_RE.match(title.strip())
    if match is None or match.group("type") not in CONVENTIONAL_TYPES:
        _refuse_squash(
            f'commit title is not a Conventional Commit "type(scope): subject": {title} (#{num})',
            "rename the PR title to `type(scope): subject` "
            "(feat, fix, docs, refactor, test, ...), then re-run",
        )


def _section_key(name: str) -> str | None:
    """Canonical key for a section heading or label; None when the name is prose."""
    normalized = re.sub(r"\s+", " ", name.strip().strip("*_` ").strip().lower())
    # `## Root Cause:` and `## Root Cause` open the same section: a trailing colon is shape.
    normalized = normalized.removesuffix(":").strip()
    for key, aliases in SQUASH_SECTIONS.items():
        if normalized in aliases:
            return key
    return None


def _section_open(line: str) -> tuple[str | None, str]:
    """The heading or label name opening a line, with any inline label content.

    A heading whose name is not a section is retried before its first colon, so
    `## Root Cause: <why>` opens Root with `<why>` as its content.
    """
    heading = SQUASH_HEADING_RE.match(line)
    if heading:
        name = heading.group("name")
        if _section_key(name) is not None:
            return name, ""
        prefix, sep, rest = name.partition(":")
        if sep and _section_key(prefix) is not None:
            return prefix, rest.strip()
        return name, ""
    label = SQUASH_LABEL_RE.match(line)
    if label:
        return label.group("name"), label.group("rest")
    return None, ""


def split_squash_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    """Bucket a cleaned squash body into declared sections plus the prose outside them.

    A heading (`## Evidence`) or a label line (`- Blast Radius: …`) opens a section;
    an unrecognized name stays prose. Prose before the first section is the Core
    narrative, so a heading-free body still carries a Core.
    """
    sections: dict[str, list[str]] = {}
    prose: list[str] = []
    current: str | None = None
    for line in text.split("\n"):
        name, rest = _section_open(line)
        key = _section_key(name) if name is not None else None
        if key is not None:
            current = key
            section = sections.setdefault(key, [])
            if rest.strip():
                section.append(rest)
            continue
        if current is None:
            prose.append(line)
        else:
            sections[current].append(line)
    return sections, prose


def _section_content(sections: dict[str, list[str]], key: str) -> str:
    return "\n".join(sections.get(key, [])).strip()


def check_closes_lines(msg: str) -> None:
    """Every closing-keyword line names exactly one issue (`Closes #12`, GitHub syntax)."""
    for line in msg.splitlines():
        stripped = line.strip()
        if CLOSES_REF_RE.match(stripped) and not CLOSES_LINE_RE.match(stripped):
            _refuse_squash(
                f'closing-keyword line is not one issue: "{stripped}"',
                "write each issue as its own `Closes #NN` line (never comma-separated), then re-run",
            )


FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _count_squash_bullets(text: str) -> int:
    """Bullet lines outside fenced code blocks; a quoted diff or log is not the list.

    A fence opens a quoted span only when a matching closer appears later (backtick
    and tilde fences, any info string, not mermaid): every line in the balanced span
    is quoted material. An unclosed opener quotes nothing, so the bullets after it
    still count (fail closed). Markers are `*`, `+`, `-`, and numbered `1.` / `1)`.
    """
    lines = text.splitlines()
    quoted = [False] * len(lines)
    i = 0
    while i < len(lines):
        opener = FENCE_RE.match(lines[i])
        if opener is not None:
            char = opener.group(1)[0]
            closer = i + 1
            while closer < len(lines):
                end = FENCE_RE.match(lines[closer])
                if end is not None and end.group(1)[0] == char:
                    break
                closer += 1
            if closer < len(lines):
                for k in range(i, closer + 1):
                    quoted[k] = True
                i = closer + 1
                continue
        i += 1
    return sum(1 for k, line in enumerate(lines) if not quoted[k] and SQUASH_BULLET_RE.match(line))


def _states_rollback(blast_radius: list[str]) -> bool:
    """A rollback *statement*, never the label that merely names containment.

    The shipped template's `**Rollback / containment:**` label counts only when
    content follows its colon; a `Door:` line never counts on its own name. Any
    other line (or the content after a label) that names a rollback counts too.
    """
    for line in blast_radius:
        label = SQUASH_LABEL_RE.match(line)
        if label is None:
            if ROLLBACK_RE.search(line):
                return True
            continue
        name = label.group("name")
        rest = label.group("rest")
        if ROLLBACK_RE.search(name) and rest.strip():
            return True
        if ROLLBACK_RE.search(rest):
            return True
    return False


def _is_label_line(line: str) -> bool:
    """True for a bare label: nothing after its colon but emphasis markers and space.

    The shipped template's `**Before (command + output):**` is one; it names a slot, not output.
    """
    return bool(LABEL_ONLY_RE.search(line.strip()))


def _evidence_marker_text(evidence: list[str]) -> str:
    """The Evidence text the before -> after markers match against.

    A bare label line states no output, so it counts only when the block under it — the
    lines up to the next label — carries content. The shipped template's bare
    `**Before (command + output):**` / `**After (command + output):**` pair therefore reads
    as empty text and is refused; the same labels over pasted output still pair, and output
    pasted on the label's own line counts directly.
    """
    kept: list[str] = []
    for index, line in enumerate(evidence):
        if not _is_label_line(line):
            kept.append(line)
            continue
        block: list[str] = []
        for candidate in evidence[index + 1 :]:
            if _is_label_line(candidate):
                break
            block.append(candidate)
        if any(candidate.strip() for candidate in block):
            kept.append(line)
    return "\n".join(kept).lower()


def check_squash_body(msg: str, *, title: str = "", pr_link: str = "") -> None:
    """Body gate over the cleaned squash message.

    Core is required on every path. Root is required for every `fix` title, prose
    bodies included, and never for any other type. Blast Radius, Evidence, and Links
    are validated when declared: a `Door:` line (or the shipped template's
    `Rollback / containment:` label) plus a rollback statement, a before -> after over
    pasted output (a bare label is not proof), and the PR link. At most
    SQUASH_BODY_MAX_BULLETS bullets outside any fenced block
    keep the message one screen.
    """
    sections, prose = split_squash_sections(msg)
    if not _section_content(sections, "summary") and not "\n".join(prose).strip():
        _refuse_squash(
            "squash body carries no Core section",
            "write one `## Summary` line (or `- Core: <one line>`) saying what changed and why, then re-run",
        )
    match = SQUASH_TITLE_RE.match(title.strip())
    is_fix = match is not None and match.group("type").lower() == FIX_TYPE
    if is_fix and not _section_content(sections, "root_cause"):
        _refuse_squash(
            "a fix squash body carries no Root section",
            "add a `## Root Cause` line naming why the bug happened, then re-run",
        )
    blast_radius = sections.get("blast_radius")
    if blast_radius is not None:
        if not any(DOOR_RE.match(line) for line in blast_radius):
            _refuse_squash(
                "the Blast Radius section carries neither a `Door:` line nor the "
                "template's `Rollback / containment:` line",
                "open Blast Radius with `Door: one-way` (or the template's "
                "`**Rollback / containment:** revert the squash commit`), then re-run",
            )
        if not _states_rollback(blast_radius):
            _refuse_squash(
                "the Blast Radius section states no rollback",
                "state the rollback (`**Rollback / containment:** revert the squash commit`), then re-run",
            )
    evidence = sections.get("evidence")
    if evidence is not None:
        text = _evidence_marker_text(evidence)
        arrowed = any(arrow in text for arrow in BEFORE_AFTER_ARROW)
        both = any(marker in text for marker in BEFORE_MARKERS) and any(
            marker in text for marker in AFTER_MARKERS
        )
        if not (arrowed or both):
            _refuse_squash(
                "the Evidence section states no before -> after",
                "show the before output and the after output "
                "(`before: 3 failed -> after: 0 failed`), then re-run",
            )
    links = sections.get("links")
    if links is not None and pr_link and pr_link not in "\n".join(links):
        _refuse_squash(
            "the Links section carries no PR link",
            f"add `{pr_link}` to Links, then re-run",
        )
    check_closes_lines(msg)
    bullets = _count_squash_bullets(msg)
    if bullets > SQUASH_BODY_MAX_BULLETS:
        _refuse_squash(
            f"squash body carries {bullets} bullets (max {SQUASH_BODY_MAX_BULLETS})",
            "condense the change into at most 5 bullets, then re-run",
        )


def _is_stop_line(line: str) -> bool:
    return bool(HEADING_RE.match(line) or is_closing_line(line) or is_trailer_line(line))


def _strip_unclosed(text: str, opener: re.Pattern[str]) -> str:
    """Drop each unclosed construct from its opener line up to (exclusive) the
    first heading, closing keyword, or trailer line."""
    out: list[str] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if opener.search(lines[i]):
            i += 1
            while i < len(lines) and not _is_stop_line(lines[i]):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def clean_squash_body(body: str) -> str:
    """Strip review-only ephemera from a squash body.

    Removal order is deterministic: HTML comments → mermaid fences → <details>
    blocks → review-only sections → procedural sections → directives → task-list
    checkboxes →
    empty-section pruning. <details> removal runs before pruning so a section
    holding only a details block becomes empty and is dropped. Unclosed
    mermaid/<details> strips stop before the next heading, Closes keyword, or
    Co-authored-by trailer, so the sanitizer never removes those lines. Fenced
    ephemera are anchored at line start (optionally after a list marker): a
    <details> opened mid-line is prose, not markup, and is not stripped; a line
    that begins with the tag is an opener.
    """
    refuse_raw_token(body)
    text = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    # Closing/trailer lines are safe by construction: _strip_unclosed stops
    # before CLOSING_RE/TRAILER_RE lines and section scanning exits on them,
    # so every such line in text survives into pruned.
    text = MERMAID_FENCE_RE.sub("", text)
    text = _strip_unclosed(text, MERMAID_UNCLOSED_OPENER_RE)
    text = DETAILS_BLOCK_RE.sub("", text)
    text = _strip_unclosed(text, DETAILS_UNCLOSED_OPENER_RE)

    lines: list[str] = []
    in_procedural_section = False

    for line in text.splitlines():
        if HEADING_RE.match(line):
            if PROCEDURAL_SECTION_RE.match(line) or REVIEW_ONLY_SECTION_RE.match(line):
                in_procedural_section = True
                continue
            in_procedural_section = False

        if in_procedural_section:
            if is_closing_line(line) or is_trailer_line(line):
                in_procedural_section = False
            else:
                continue

        if DIRECTIVE_RE.match(line):
            continue

        if CHECKBOX_RE.match(line):
            continue

        lines.append(line)

    pruned: list[str] = []
    for i, line in enumerate(lines):
        if HEADING_RE.match(line):
            has_content = False
            for next_line in lines[i + 1 :]:
                if HEADING_RE.match(next_line):
                    break
                s = next_line.strip()
                if (
                    s
                    and not EMPTY_BULLET_RE.match(s)
                    and not is_closing_line(next_line)
                    and not is_trailer_line(next_line)
                ):
                    has_content = True
                    break
            if not has_content:
                continue
        pruned.append(line)

    result = "\n".join(pruned)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    if body.endswith("\n") and result:
        result += "\n"
    return result


def squash_message(body: str, template_path: Path | None = None) -> str:
    template = ""
    if template_path and template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
    elif not template_path:
        default_tmpl = DEFAULT_TEMPLATE_PATH
        if default_tmpl.is_file():
            template = default_tmpl.read_text(encoding="utf-8")
    trimmed_body = body.strip()
    trimmed_template = template.strip()
    if not trimmed_body or (trimmed_template and trimmed_body == trimmed_template):
        return ""
    return clean_squash_body(body)


def is_fallback_body(body: str, template_path: Path | None = None) -> bool:
    return squash_message(body, template_path=template_path) == ""


def is_unfilled_body(body: str, template_path: Path | None = None) -> bool:
    """True when *body* carries no authored description: empty, or the repo template verbatim."""
    return is_fallback_body(body, template_path=template_path)


def refuse_unfilled_body(body: str) -> None:
    """Refuse a PR whose description is empty or the unfilled repo template (exit 1)."""
    if body.strip():
        print("refusing PR: the description is the unfilled repo template", file=sys.stderr)
    else:
        print("refusing PR: no description supplied", file=sys.stderr)
    print(
        "remediation: draft the description from the git-diff-digest surface "
        "(skills/gh-router/subskills/git-diff-digest), then pass it with --body-file",
        file=sys.stderr,
    )
    raise RefusalError("PR body is empty or an unfilled template")


def resolve_squash_message(
    body: str,
    *,
    explicit: str | None,
    supplied: bool,
    template_path: Path | None = None,
) -> str:
    """Single decision point for the squash commit message (fail closed).

    The PR body's raw CODE_AUTHORS token is refused on both paths. An explicit
    message is sanitized through clean_squash_body; an empty one is a usage
    error. Without an explicit message the PR body must yield a non-empty
    derived squash message, or the merge is refused — GitHub's commit-subject
    synthesis is never an outcome.
    """
    if supplied:
        refuse_raw_token(body)
        cleaned = clean_squash_body(explicit or "")
        if not cleaned.strip():
            raise UsageError("--squash-message is empty")
        return cleaned
    derived = squash_message(body, template_path=template_path)
    if not derived.strip():
        print(
            "refusing squash merge: PR body is empty or the unfilled repo template",
            file=sys.stderr,
        )
        print(
            "remediation: draft the description from the git-diff-digest surface "
            "(skills/gh-router/subskills/git-diff-digest), then pass an explicit "
            "message with --squash-message (or --squash-message-file)",
            file=sys.stderr,
        )
        raise RefusalError("squash message refused: body is empty or the repo template")
    return derived


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
            explicit = mf.read_text(encoding="utf-8")
        except OSError:
            raise UsageError(
                f"squash message file not found or not readable: {options.squash_message_file}"
            ) from None
    return explicit, options.squash_message_supplied


def build_squash_message(msg: str, merger: str, tsv: str) -> str:
    cleaned = clean_squash_body(msg)
    new_trailers = pr_co_author_trailers(tsv, merger=merger, body=cleaned)
    final = insert_trailers(cleaned, new_trailers)
    # 100-character line limit on body is dropped per commit #135
    if new_trailers.strip():
        print("appended trailers:", file=sys.stderr)
        print(new_trailers, end="", file=sys.stderr)
    return final


def finalize_squash_message(repo: str, num: str, msg: str, cwd: Path | None = None) -> str:
    merger_res = run_command(
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
    tsv_res = run_command(
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


@dataclass(frozen=True, slots=True)
class MergeObservation:
    """One mergeability reading of a PR: the verdict word plus the raw fields behind it.

    ``verdict`` is ``pr_conflict_verdict``'s word (``conflicting``/``behind``/``clean``/
    ``unknown``); ``dirty`` singles out GitHub's ``dirty`` state, the conflict candidate
    that must be confirmed before it fails the gate.
    """

    verdict: str
    mergeable: str = ""
    state: str = ""
    url: str = ""

    @property
    def dirty(self) -> bool:
        """True for GitHub's `dirty` state — a conflict candidate needing a second strike."""
        return self.verdict == "conflicting" and self.state.strip().lower() == "dirty"


type MergeFetch = Callable[[str, str, Path | None], MergeObservation]


def fetch_mergeability(repo: str, num: str, cwd: Path | None = None) -> MergeObservation:
    """Read mergeable / mergeable_state / html_url in one `gh api` call."""
    res = run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls/{num}",
            "--jq",
            '[(if .mergeable == null then "null" else (.mergeable|tostring) end), (.mergeable_state // "unknown"), (.html_url // "")] | @tsv',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to check PR #{num} mergeable state: {res.stderr.strip() or 'gh api failed'}"
        )
    line = res.stdout.strip()
    if not line:
        raise PrError(f"failed to check PR #{num} mergeable state: empty response from gh api")
    parts = line.split("\t")
    mergeable = parts[0] if len(parts) > 0 else ""
    state = parts[1] if len(parts) > 1 else ""
    url = parts[2] if len(parts) > 2 else ""
    return MergeObservation(
        verdict=pr_conflict_verdict(mergeable, state), mergeable=mergeable, state=state, url=url
    )


def merge_state_verdict(state: str) -> str:
    """Verdict word for a bare `mergeable_state` reading: only `clean` may merge.

    ``pr_conflict_verdict`` needs `mergeable` too; the pre-merge probe reads the state
    alone, so every state that is not clean/behind/dirty reads as `unknown` and refuses.
    `behind` is its own verdict: the `--watch` loop accepts it with a warning folded into
    the poll line, while `--merge` refuses it (this function never returns `clean` for it).
    """
    normalized = state.strip().lower()
    if normalized == "clean":
        return "clean"
    if normalized in ("dirty", "conflicting"):
        return "conflicting"
    if normalized == "behind":
        return "behind"
    return "unknown"


def fetch_merge_state(repo: str, num: str, cwd: Path | None = None) -> MergeObservation:
    """Read `mergeable_state` alone — the pre-merge probe, which needs no `mergeable`/url."""
    res = run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".mergeable_state"], cwd=cwd
    )
    state = res.stdout.strip() if res.returncode == 0 and res.stdout.strip() else "unknown"
    return MergeObservation(verdict=merge_state_verdict(state), state=state)


def resolve_merge_state(
    repo: str,
    num: str,
    *,
    fetch: MergeFetch = fetch_mergeability,
    unknown_tries: int = UNKNOWN_TRIES,
    unknown_interval: float = UNKNOWN_INTERVAL,
    dirty_strikes: int = DIRTY_STRIKES,
    dirty_interval: float = DIRTY_INTERVAL,
    cwd: Path | None = None,
) -> MergeObservation:
    """Poll mergeability until a confident verdict, then return that observation.

    An `unknown` reading (and a transient `gh api` failure) is retried up to
    `unknown_tries` times, `unknown_interval` apart. The default budget is intentionally
    short — about 8s (5 tries x 2s) — after which the caller refuses with the verdict word
    `unknown`. That word is distinct from `conflicting`: `unknown` means GitHub never
    computed mergeability, `conflicting` means a real conflict. A `dirty` reading is
    confirmed `dirty_strikes` times, `dirty_interval` apart, before it counts as
    conflicting; any non-dirty reading resets that streak. An unresolved `unknown` comes
    back as-is: the caller refuses on it, so a PR whose mergeability GitHub never computes
    fails fast instead of stalling the watch.
    """
    unknown_left = max(1, unknown_tries)
    strikes = 0
    while True:
        try:
            obs = fetch(repo, num, cwd)
        except PrError:
            unknown_left -= 1
            if unknown_left <= 0:
                raise
            time.sleep(unknown_interval)
            continue
        if obs.dirty:
            strikes += 1
            if strikes >= max(1, dirty_strikes):
                return obs
            time.sleep(dirty_interval)
            continue
        strikes = 0
        if obs.verdict == "unknown":
            unknown_left -= 1
            if unknown_left <= 0:
                return obs
            time.sleep(unknown_interval)
            continue
        return obs


def conflicting_files(repo: str, num: str, cwd: Path | None = None) -> list[str]:
    """Every path the PR touches, best-effort — NOT the conflicting subset.

    ``gh pr view --json files`` lists all changed files and has no conflict filter, so the
    report must not call them the conflicting set. Empty when the `gh pr view` read fails.
    """
    res = run_command(
        [
            "gh",
            "pr",
            "view",
            num,
            "--repo",
            repo,
            "--json",
            "files",
            "--jq",
            '[.files[].path] | join(" ")',
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        return []
    return res.stdout.strip().strip('"').split()


def report_merge_refusal(
    obs: MergeObservation, repo: str, num: str, cwd: Path | None = None
) -> None:
    """Print the one refusal report shared by the watch fast-fail, the gate, and the merge.

    Verdict word, PR url, up to ``CONFLICT_FILES_MAX`` touched files (every path the PR
    changes — not a conflicting subset, which ``gh pr view --json files`` cannot supply;
    ``(+N more)`` past the cap), and the pr-conflict helper pointer. An empty or failed
    file read prints ``touched files: (none resolved)`` instead of dropping the line.
    """
    url = obs.url or pr_url(repo, num, cwd=cwd)
    print(f"PR {url}", file=sys.stderr)
    mergeable = f"mergeable={obs.mergeable} " if obs.mergeable else ""
    print(f"{obs.verdict}: {mergeable}merge_state_status={obs.state}", file=sys.stderr)
    files = conflicting_files(repo, num, cwd=cwd)
    if files:
        shown = files[:CONFLICT_FILES_MAX]
        extra = len(files) - len(shown)
        more = f" (+{extra} more)" if extra > 0 else ""
        print(f"touched files: {' '.join(shown)}{more}", file=sys.stderr)
    else:
        print("touched files: (none resolved)", file=sys.stderr)
    lead = "conflict detected" if obs.verdict == "conflicting" else "mergeability unresolved"
    print(
        f"{lead}: run '{CONFLICT_HELPER}' to inspect hunks and commit intent, "
        "then delegate resolution to a worker subagent.",
        file=sys.stderr,
    )


def check_conflicts(repo: str, num: str, base: str, cwd: Path | None = None) -> bool:
    """Refuse when the PR cannot merge: conflicting, or mergeability that stays unresolved.

    Compatibility wrapper kept for the tests; the live paths (``--watch``, ``--merge``)
    call ``resolve_merge_state`` + ``report_merge_refusal`` directly. Returns False on a
    conflict and on an `unknown` state that survives UNKNOWN_TRIES retries, True
    otherwise; raises PrError when the `gh api` read fails outright. A refusal names the
    touched files and the pr-conflict resolution pointer on stderr. A `behind` head is
    accepted here with a warning, the same as the watch loop (``--merge`` refuses it).
    """
    obs = resolve_merge_state(repo, num, cwd=cwd)
    if obs.verdict in ("conflicting", "unknown"):
        report_merge_refusal(obs, repo, num, cwd=cwd)
        return False
    if obs.verdict == "behind":
        print(f"warning: head branch is behind {base}", file=sys.stderr)
    return True


def failing_run_ids(repo: str, num: str, cwd: Path | None = None) -> list[str]:
    """Run IDs behind the failing/cancelled checks on this PR, best-effort, deduped."""
    run_ids: list[str] = []
    checks_json_res = run_command(
        [
            "gh",
            "pr",
            "checks",
            num,
            "--repo",
            repo,
            "--json",
            "name,bucket,link,state",
        ],
        cwd=cwd,
    )
    if checks_json_res.returncode == 0 and checks_json_res.stdout.strip():
        try:
            checks_data = json.loads(checks_json_res.stdout)
            if isinstance(checks_data, list):
                for check in checks_data:
                    if isinstance(check, dict):
                        bucket = str(check.get("bucket", "")).lower()
                        state = str(check.get("state", "")).upper()
                        if bucket in ("fail", "cancel") or state in (
                            "FAILURE",
                            "CANCELLED",
                            "TIMED_OUT",
                        ):
                            link = str(check.get("link", ""))
                            m = re.search(r"/actions/runs/(\d+)", link)
                            if m:
                                rid = m.group(1)
                                if rid not in run_ids:
                                    run_ids.append(rid)
        except ValueError, TypeError, KeyError:
            pass

    if not run_ids:
        sha_res = run_command(
            ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".head.sha"],
            cwd=cwd,
        )
        sha = sha_res.stdout.strip() if sha_res.returncode == 0 else ""
        if sha:
            runs_res = run_command(
                [
                    "gh",
                    "api",
                    f"repos/{repo}/actions/runs?head_sha={sha}&status=completed&per_page=10",
                    "--jq",
                    '[.workflow_runs[] | select(.conclusion == "failure" or .conclusion == "cancelled") | .id] | .[0] // empty',
                ],
                cwd=cwd,
            )
            rid = runs_res.stdout.strip() if runs_res.returncode == 0 else ""
            if rid:
                run_ids.append(rid)
            else:
                any_run_res = run_command(
                    [
                        "gh",
                        "api",
                        f"repos/{repo}/actions/runs?head_sha={sha}&per_page=1",
                        "--jq",
                        ".workflow_runs[0].id // empty",
                    ],
                    cwd=cwd,
                )
                rid = any_run_res.stdout.strip() if any_run_res.returncode == 0 else ""
                if rid:
                    run_ids.append(rid)

    return run_ids


def dump_failure_logs(repo: str, num: str, cwd: Path | None = None, verbose: bool = True) -> None:
    """Print the evidence behind a red watch.

    ``verbose`` (the default) keeps the full dump: the `gh run view` log tails plus a
    `gh pr checks` dump. ``verbose=False`` is the slim `--watch` default — the failing run
    ID(s) and the one-line pointer, no log bodies.
    """
    run_ids = failing_run_ids(repo, num, cwd=cwd)
    if not verbose:
        ids = " ".join(run_ids) if run_ids else "(none resolved)"
        print(f"checks failed: failing run id(s): {ids}", file=sys.stderr)
        print(
            "run 'gh run view --run-id <id> --log-failed' (or 'ci.sh why') for the failing step log",
            file=sys.stderr,
        )
        return

    for run_id in run_ids[:2]:
        try:
            view_res = run_command(
                ["gh", "run", "view", run_id, "--repo", repo, "--log-failed"],
                timeout=LOG_TIMEOUT,
                cwd=cwd,
            )
            combined = (view_res.stdout + view_res.stderr).strip()
            if not combined or view_res.returncode != 0:
                view_res = run_command(
                    ["gh", "run", "view", run_id, "--repo", repo, "--log"],
                    timeout=LOG_TIMEOUT,
                    cwd=cwd,
                )
                combined = (view_res.stdout + view_res.stderr).strip()

            tail_lines = combined.splitlines()[-200:]
            if tail_lines:
                print("\n".join(tail_lines), file=sys.stderr)
        except PrError as e:
            print(f"warning: could not fetch run logs: {e}", file=sys.stderr)

    checks_res = run_command(
        ["gh", "pr", "checks", num, "--repo", repo],
        cwd=cwd,
    )
    combined_checks = (checks_res.stdout + checks_res.stderr).splitlines()
    tail_checks = combined_checks[-50:]
    if tail_checks:
        print("\n".join(tail_checks), file=sys.stderr)


def watch_checks(
    repo: str,
    num: str,
    base: str,
    poll_tries: int = POLL_TRIES,
    poll_interval: float = POLL_INTERVAL,
    cwd: Path | None = None,
    verbose: bool = False,
) -> bool:
    """Poll mergeability and every check until a verdict, one stderr line per poll.

    A conflict — or a mergeability GitHub never computes — fails fast through the shared
    refusal report. A `behind` head is accepted here: the fact rides the poll line, so a
    behind PR still prints exactly one line per poll. The `--merge` path refuses `behind`
    instead (see ``merge_state_verdict``). Output is slim by default: a failing check
    prints its run ID(s) and a `gh run view` pointer, and only `verbose` adds the log
    bodies.
    """
    for i in range(1, poll_tries + 1):
        obs = resolve_merge_state(repo, num, cwd=cwd)
        if obs.verdict in ("conflicting", "unknown"):
            report_merge_refusal(obs, repo, num, cwd=cwd)
            return False
        checks_res = run_command(
            [
                "gh",
                "pr",
                "checks",
                num,
                "--repo",
                repo,
                "--json",
                "name,bucket",
                "--jq",
                ".[] | [.name,.bucket] | @tsv",
            ],
            cwd=cwd,
        )
        payload = checks_res.stdout if checks_res.returncode == 0 else ""
        verdict = checks_verdict(payload)
        behind = f", head behind {base}" if obs.verdict == "behind" else ""
        print(
            f"checks {verdict} (mergeable_state={obs.state}, {i}/{poll_tries}{behind})",
            file=sys.stderr,
        )
        if verdict == "success":
            return True
        if verdict == "failure":
            dump_failure_logs(repo, num, cwd=cwd, verbose=verbose)
            return False
        time.sleep(poll_interval)

    print(
        f"checks timeout after {int(poll_tries * poll_interval)}s — no green verdict",
        file=sys.stderr,
    )
    if verbose:
        last_checks = run_command(
            ["gh", "pr", "checks", num, "--repo", repo],
            cwd=cwd,
        )
        tail_lines = (last_checks.stdout + last_checks.stderr).splitlines()[-30:]
        if tail_lines:
            print("\n".join(tail_lines), file=sys.stderr)
    return False


@dataclass(frozen=True, slots=True)
class CheckReport:
    """Outcome of the --check preflight: gate code, trailers, and the PR it evaluated.

    ``body`` is the cleaned squash text a merge would commit; ``authored_body`` is
    the description exactly as supplied or fetched, so the draft can write the
    human-facing `pr_body.md` (Mermaid and `<details>` included) from it.
    """

    exit_code: int
    trailers: str = ""
    pr_number: str | None = None
    pr_url: str | None = None
    body: str = ""
    authored_body: str = ""
    note: str = ""


def check_trailers_report(
    repo: str,
    head_ref: str,
    body: str,
    body_supplied: bool,
    title: str = "",
    template_path: Path | None = None,
    cwd: Path | None = None,
    squash_message_override: str | None = None,
    squash_message_supplied: bool = False,
) -> CheckReport:
    """Run the --check merge gates and report the trailers a merge would append.

    Data-only twin of check_trailers: refusals and remediation still go to stderr,
    but the trailers and the resolved body come back in the report so the draft
    phase can write them to disk instead of stdout. Exit codes are unchanged.
    """
    owner = repo.split("/")[0]
    res = run_command(
        [
            "gh",
            "api",
            f"repos/{repo}/pulls?head={owner}:{head_ref}&state=open",
            "--jq",
            ".[0].number",
        ],
        cwd=cwd,
    )
    if res.returncode != 0:
        raise PrError(
            f"failed to query open PR for head {head_ref}: {res.stderr.strip() or 'gh api failed'}"
        )
    found = res.stdout.strip()
    if not found or found == "null":
        if not body_supplied:
            print(f"no open PR for head {head_ref}", file=sys.stderr)
            return CheckReport(exit_code=2, note=f"no open PR for head {head_ref}")

        if title:
            try:
                check_squash_title(title, 9999)
            except RefusalError:
                return CheckReport(exit_code=1, body=body, authored_body=body)

        try:
            resolved_msg = resolve_squash_message(
                body,
                explicit=squash_message_override,
                supplied=squash_message_supplied,
                template_path=template_path,
            )
        except RefusalError:
            return CheckReport(exit_code=1, body=body, authored_body=body)

        try:
            check_squash_body(resolved_msg, title=title)
        except RefusalError:
            return CheckReport(exit_code=1, body=resolved_msg, authored_body=body)

        try:
            base = resolve_base(None, repo, cwd=cwd)
            digest_range = _digest_range_spec(base, head_ref, cwd=cwd)
        except RefusalError as exc:
            print(f"{exc}", file=sys.stderr)
            return CheckReport(exit_code=1, body=body, authored_body=body)
        except RangeRefusal:
            digest_range = None
        log_res: subprocess.CompletedProcess[str] | None = None
        if digest_range is not None:
            log_res = run_command(
                ["git", "log", digest_range, "--pretty=format:\t%an\t%ae"],
                cwd=cwd,
            )
        if log_res is None or log_res.returncode != 0:
            log_res = run_command(
                ["git", "log", "-1", "--pretty=format:\t%an\t%ae", head_ref],
                cwd=cwd,
            )
        tsv = log_res.stdout if log_res.returncode == 0 else ""

        merger = ""
        user_res = run_command(["gh", "api", "user", "--jq", ".login"], cwd=cwd)
        if user_res.returncode == 0 and user_res.stdout.strip():
            merger = user_res.stdout.strip()
        if not merger:
            cfg_res = run_command(["git", "config", "user.email"], cwd=cwd)
            if cfg_res.returncode == 0:
                merger = cfg_res.stdout.strip()

        new_trailers = pr_co_author_trailers(tsv, merger=merger, body=resolved_msg)
        note = (
            ""
            if new_trailers.strip()
            else f"no co-author trailers would be appended for {head_ref}"
        )
        return CheckReport(
            exit_code=0, trailers=new_trailers, body=resolved_msg, authored_body=body, note=note
        )

    num = found
    url = f"https://github.com/{repo}/pull/{num}"

    try:
        if title.strip():
            check_squash_title(title, num)
        else:
            check_title_length(title, num)
    except RefusalError:
        return CheckReport(exit_code=1, pr_number=num, pr_url=url, authored_body=body)

    if not body_supplied:
        body_res = run_command(
            ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", '.body // ""'],
            cwd=cwd,
        )
        if body_res.returncode != 0:
            raise PrError(
                f"failed to fetch body for PR #{num}: {body_res.stderr.strip() or 'gh api failed'}"
            )
        body = body_res.stdout

    try:
        resolved_msg = resolve_squash_message(
            body,
            explicit=squash_message_override,
            supplied=squash_message_supplied,
            template_path=template_path,
        )
    except RefusalError:
        return CheckReport(exit_code=1, pr_number=num, pr_url=url, body=body, authored_body=body)

    try:
        check_squash_body(
            resolved_msg,
            title=title,
            pr_link=f"https://github.com/{repo}/pull/{num}",
        )
    except RefusalError:
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )

    merger_res = run_command(
        ["gh", "api", "user", "--jq", ".login"],
        cwd=cwd,
    )
    if merger_res.returncode != 0:
        raise PrError(
            f"failed to resolve current user login via gh api user: {merger_res.stderr.strip() or 'gh api user failed'}"
        )
    merger = merger_res.stdout.strip()

    tsv_res = run_command(
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
            f"refusing --check: could not enumerate PR #{num} commit authors (check network / GH_TOKEN scopes); re-run",
            file=sys.stderr,
        )
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )
    tsv = tsv_res.stdout

    try:
        _ = build_squash_message(resolved_msg, merger, tsv)
    except RefusalError:
        return CheckReport(
            exit_code=1, pr_number=num, pr_url=url, body=resolved_msg, authored_body=body
        )

    new_trailers = pr_co_author_trailers(tsv, merger=merger, body=resolved_msg)
    note = "" if new_trailers.strip() else f"no co-author trailers would be appended for #{num}"
    return CheckReport(
        exit_code=0,
        trailers=new_trailers,
        pr_number=num,
        pr_url=url,
        body=resolved_msg,
        authored_body=body,
        note=note,
    )


def check_trailers(
    repo: str,
    head_ref: str,
    body: str,
    body_supplied: bool,
    title: str = "",
    template_path: Path | None = None,
    cwd: Path | None = None,
    squash_message_override: str | None = None,
    squash_message_supplied: bool = False,
) -> int:
    """Backward-compatible --check gate: report the result, print trailers to stdout."""
    report = check_trailers_report(
        repo=repo,
        head_ref=head_ref,
        body=body,
        body_supplied=body_supplied,
        title=title,
        template_path=template_path,
        cwd=cwd,
        squash_message_override=squash_message_override,
        squash_message_supplied=squash_message_supplied,
    )
    if report.exit_code == 0:
        if report.trailers.strip():
            print(report.trailers, end="")
        else:
            print(report.note, file=sys.stderr)
    return report.exit_code


def resolve_out_dir(out_dir: Path | None, cwd: Path | None = None) -> Path:
    """Resolve the draft output directory (default <repo-root>/.lsz/tmp).

    An explicit --out-dir resolves against the working directory; the default
    resolves against the repository root so every --check in a checkout lands in
    the same place.
    """
    base = cwd or Path.cwd()
    if out_dir is not None:
        target = out_dir if out_dir.is_absolute() else base / out_dir
        return target.resolve()
    try:
        root = find_repo_root(base)
    except RuntimeError:
        root = base.resolve()
    return (root / DRAFT_OUT_DIR).resolve()


def cap_draft_body(text: str, max_lines: int = DRAFT_BODY_MAX_LINES) -> tuple[str, int]:
    """Cap a commit body at *max_lines*; return (capped text, omitted line count)."""
    lines = text.strip("\n").splitlines()
    if len(lines) <= max_lines:
        return ("\n".join(lines), 0)
    return ("\n".join(lines[:max_lines]), len(lines) - max_lines)


def draft_commits(
    range_resolution: RangeResolution | None, cwd: Path | None = None
) -> list[dict[str, object]]:
    """One row per range commit: full SHA pointer, subject, and a capped body."""
    if range_resolution is None:
        return []
    base = cwd or Path.cwd()
    try:
        root = find_repo_root(base)
    except RuntimeError:
        root = base.resolve()
    rows: list[dict[str, object]] = []
    for sha in range_resolution.commits:
        summary = get_commit_summary(root, sha) or {}
        body_text, omitted = cap_draft_body(str(summary.get("body", "")))
        rows.append(
            {
                "sha": sha,
                "short_sha": str(summary.get("sha", sha[:7])),
                "author": str(summary.get("author", "")),
                "subject": str(summary.get("subject", "")),
                "body": body_text,
                "body_lines": len(body_text.splitlines()) if body_text else 0,
                "body_omitted_lines": omitted,
            }
        )
    return rows


def _draft_range(
    base: str | None, head_ref: str, cwd: Path | None = None
) -> RangeResolution | None:
    """Resolve the landing range through the shared authority; None when it cannot."""
    specs = [f"{base}..{head_ref}"] if base else []
    specs.append(head_ref)
    for spec in specs:
        try:
            return _authority_resolve(spec, "..", cwd)
        except RangeRefusal, MalformedSpec:
            continue
    return None


def build_draft_payload(
    *,
    repo: str,
    head_ref: str,
    base: str | None,
    title: str,
    report: CheckReport,
    range_resolution: RangeResolution | None,
    commits: list[dict[str, object]],
    counts: dict[str, int],
    dirty: dict[str, list[str]],
    squash_body: str,
    draft_path: Path,
    body_path: Path,
    hint: str,
) -> dict[str, object]:
    """Assemble the JSON-only draft payload (no YAML view, no full stdout dump)."""
    return {
        "schema": DRAFT_SCHEMA,
        "repo": repo,
        "head": head_ref,
        "base": base,
        "title": title,
        "pr_number": report.pr_number,
        "pr_url": report.pr_url,
        "status": "ok" if report.exit_code == 0 else "refused",
        "exit_code": report.exit_code,
        "note": report.note,
        "range": range_resolution.to_dict() if range_resolution is not None else None,
        "counts": counts,
        "commits": commits,
        "dirty": dirty,
        "trailers": report.trailers,
        "squash_body": squash_body,
        "draft_path": str(draft_path),
        "body_path": str(body_path),
        "hint": hint,
    }


def _draft_dirty(cwd: Path | None = None) -> dict[str, list[str]]:
    """Advisory working-tree reading for draft.json; empty lists when clean or unreadable."""
    empty: dict[str, list[str]] = {"porcelain": [], "diff_stat": []}
    try:
        root = find_repo_root(cwd or Path.cwd())
    except RuntimeError:
        root = (cwd or Path.cwd()).resolve()
    try:
        porcelain = [
            line
            for line in run_command(
                ["git", "--no-optional-locks", "status", "--porcelain"],
                cwd=root,
            ).stdout.splitlines()
            if line.strip()
        ]
        if not porcelain:
            return empty
        diff_stat = [
            line
            for line in run_command(
                ["git", "--no-optional-locks", "diff", "HEAD", "--stat", "--", "."],
                cwd=root,
            ).stdout.splitlines()
            if line.strip()
        ]
    except PrError, OSError, RuntimeError:
        return empty
    return {"porcelain": porcelain[:20], "diff_stat": diff_stat[-8:]}


def run_draft_phase(
    *,
    options: PrOptions,
    repo: str,
    head_ref: str,
    title: str,
    body: str,
    body_supplied: bool,
    squash_message_override: str | None,
    squash_message_supplied: bool,
    template_path: Path | None = None,
    cwd: Path | None = None,
) -> int:
    """Emit draft.json + pr_body.md for --check, keep stdout small, return the gate code.

    Every --check run writes both files, even a refused one: the gate verdict is
    the exit code (and stderr), while the full text stays on disk. `pr_body.md`
    carries the authored description (Mermaid and `<details>` kept) plus the
    trailers a merge would append; `draft.json`'s `squash_body` is the cleaned
    text a merge would commit. stdout carries only counts, the two paths, and one
    curation hint.
    """
    out_dir = resolve_out_dir(options.out_dir, cwd=cwd)
    draft_path = out_dir / "draft.json"
    body_path = out_dir / "pr_body.md"

    report = check_trailers_report(
        repo=repo,
        head_ref=head_ref,
        body=body,
        body_supplied=body_supplied,
        title=title,
        template_path=template_path,
        cwd=cwd,
        squash_message_override=squash_message_override,
        squash_message_supplied=squash_message_supplied,
    )

    if report.exit_code == 0 and report.note:
        print(report.note, file=sys.stderr)

    squash_body = report.body.strip("\n")
    authored_body = report.authored_body.strip("\n")
    if report.exit_code == 0 and authored_body:
        body_text = insert_trailers(authored_body, report.trailers)
    elif authored_body:
        body_text = authored_body + "\n"
    else:
        body_text = DRAFT_BODY_PLACEHOLDER
    if not body_text.endswith("\n"):
        body_text += "\n"

    try:
        base: str | None = resolve_base(options.base, repo, cwd=cwd)
    except RefusalError as exc:
        print(f"{exc}", file=sys.stderr)
        base = None

    range_resolution = _draft_range(base, head_ref, cwd)
    commits = draft_commits(range_resolution, cwd)
    if not commits and not options.title_supplied and title:
        print(
            f"warning: no unique commits in range; draft title {title!r} is a guess "
            "-- pass --title explicitly",
            file=sys.stderr,
        )
    dirty = _draft_dirty(cwd)
    dirty_files = len(dirty["porcelain"])

    counts = {
        "commits": len(commits),
        "only_in_base": range_resolution.counts.only_in_base if range_resolution else 0,
        "trailers": sum(1 for line in report.trailers.splitlines() if line.strip()),
        "body_lines": len(body_text.splitlines()),
        "dirty_files": dirty_files,
    }
    hint = (
        f"curate {body_path.name} to <=5 bullets "
        "(Core + Root for fix + Risk:Door + Proof + Links), "
        "drop wip/fixup trivia, strip Mermaid/details/checklist; "
        f"then land with --body-file {body_path}"
    )
    payload = build_draft_payload(
        repo=repo,
        head_ref=head_ref,
        base=base,
        title=title,
        report=report,
        range_resolution=range_resolution,
        commits=commits,
        counts=counts,
        squash_body=squash_body,
        dirty=dirty,
        draft_path=draft_path,
        body_path=body_path,
        hint=hint,
    )

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        _ = draft_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        _ = body_path.write_text(body_text, encoding="utf-8")
    except OSError as exc:
        raise PrError(f"cannot write draft files under {out_dir}: {exc}") from exc

    print(f"commits: {counts['commits']}")
    print(f"trailers: {counts['trailers']}")
    print(f"draft: {draft_path}")
    print(f"body: {body_path}")
    print(f"hint: {hint}")
    return report.exit_code


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
    res = run_command(
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
            t_res = run_command(
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
            b_res = run_command(
                ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", '.body // ""'],
                cwd=cwd,
            )
            if b_res.returncode != 0:
                raise PrError(
                    f"failed to fetch body for PR #{num}: {b_res.stderr.strip() or 'gh api failed'}"
                )
            final_body = b_res.stdout

        if patch_args:
            patch_res = run_command(
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

    create_res = run_command(
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


def ready_pr(repo: str, num: str, cwd: Path | None = None) -> bool:
    """Flip a draft PR to ready so CI's ready_for_review event fires.

    Prints the command to stderr before running it. A non-zero gh pr ready is not
    silent: the exact manual fix is printed verbatim and the caller must exit 1 —
    a draft that never went ready is not success.
    """
    cmd = ["gh", "pr", "ready", num, "--repo", repo]
    print(" ".join(cmd), file=sys.stderr)
    res = run_command(cmd, cwd=cwd)
    if res.returncode != 0:
        detail = res.stderr.strip() or "gh pr ready failed"
        print(f"gh pr ready failed for PR #{num}: {detail}", file=sys.stderr)
        print(
            f"remediation: PR #{num} is still a draft; run manually: gh pr ready {num} --repo {repo}",
            file=sys.stderr,
        )
        return False
    return True


def pr_url(repo: str, num: str, cwd: Path | None = None) -> str:
    res = run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".html_url"],
        cwd=cwd,
    )
    if res.returncode != 0 or not res.stdout.strip():
        return f"https://github.com/{repo}/pull/{num}"
    return res.stdout.strip()


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

    m_res = run_command(
        ["gh", "api", f"repos/{repo}/pulls/{num}/merge", "-X", "PUT", *merge_args],
        cwd=cwd,
    )
    if m_res.returncode != 0:
        print(f"merge failed: {m_res.stderr.strip() or 'gh api failed'}", file=sys.stderr)
        return False
    print(f"merged #{num} (squash) to {base}", file=sys.stderr)
    return True


def _unreleased_attribution_re(pr_num: str) -> re.Pattern[str]:
    """Cached end-of-entry attribution matcher for one PR number (keeps re.escape)."""
    cached = _UNRELEASED_ATTR_RES.get(pr_num)
    if cached is None:
        cached = re.compile(r"\(#" + re.escape(pr_num) + r"\)(?:\s*\(BREAKING CHANGE\))?\s*$")
        _UNRELEASED_ATTR_RES[pr_num] = cached
    return cached


def _read_unreleased_block(cwd: Path | None = None) -> str | None:
    """Return the ## [Unreleased] block body, or None when absent or unreadable.

    A missing file, undecodable bytes, and a missing Unreleased heading all
    read as absent (None); the caller picks the advisory.
    """
    root = cwd or Path.cwd()
    try:
        content = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return None
    if "## [Unreleased]" not in content:
        return None
    _, rest = content.split("## [Unreleased]", 1)
    end = _UNRELEASED_VERSION_END_RE.search(rest)
    return rest[: end.start()] if end else rest


def unreleased_attributes_pr(pr_num: str, cwd: Path | None = None) -> bool:
    """Return True when the ## [Unreleased] block carries a bullet entry for this PR.

    Scans bullet lines only, and only after a ### section heading inside the
    block (mirroring parse_unreleased_sections in scripts/changelog-gate.py);
    an entry attributes N when it ends with (#N), optionally followed by
    (BREAKING CHANGE). Mirrors ATTRIBUTION_RE in scripts/changelog-gate.py.
    A missing or unreadable CHANGELOG.md, or no Unreleased block, reads as
    unattributed (False).
    """
    block = _read_unreleased_block(cwd)
    if block is None:
        return False
    attribution_re = _unreleased_attribution_re(pr_num)
    in_section = False
    for line in block.splitlines():
        if _UNRELEASED_SECTION_RE.match(line):
            in_section = True
            continue
        if not _UNRELEASED_BULLET_RE.match(line):
            continue
        if not in_section:
            continue
        if attribution_re.search(line.rstrip()):
            return True
    return False


def stamp_changelog(
    head_ref: str,
    pr_num: str,
    cwd: Path | None = None,
) -> bool:
    root = cwd or Path.cwd()
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        return False

    try:
        content = changelog_path.read_text(encoding="utf-8")
    except OSError:
        return False

    if "## [Unreleased]" not in content:
        return False

    before_unreleased, rest = content.split("## [Unreleased]", 1)
    version_match = re.search(r"^## \[[^\]]+\].*", rest, re.MULTILINE)
    if version_match:
        unreleased_block = rest[: version_match.start()]
        after_unreleased = rest[version_match.start() :]
    else:
        unreleased_block = rest
        after_unreleased = ""

    if f"(#{pr_num})" in unreleased_block:
        return False

    baseline_path = root / ".config" / "changelog-unattributed-baseline.txt"
    baseline: set[str] = set()
    if baseline_path.is_file():
        try:
            baseline = {
                line.strip()
                for line in baseline_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            }
        except OSError:
            baseline = set()

    attribution_re = re.compile(r"\(#\d+\)(?:\s*\(BREAKING CHANGE\))?\s*$")
    breaking_re = re.compile(r"\s*\(BREAKING CHANGE\)\s*$")
    bullet_re = re.compile(r"^([*+-]\s+)(.+)$")

    def entry_identity(text: str) -> str:
        s = text.strip()
        if s[:1] in "*+-":
            s = s[1:].strip()
        while True:
            trimmed = re.sub(r"\s*\(#\d+\)\s*$|\s*\(BREAKING CHANGE\)\s*$", "", s).rstrip()
            if trimmed == s:
                return s
            s = trimmed

    new_lines: list[str] = []
    modified = False

    for line in unreleased_block.splitlines(keepends=True):
        raw_line = line.rstrip("\r\n")
        m = bullet_re.match(raw_line)
        if not m:
            new_lines.append(line)
            continue

        prefix, body = m.group(1), m.group(2)
        if attribution_re.search(body):
            new_lines.append(line)
            continue

        identity = entry_identity(raw_line)
        if identity in baseline:
            new_lines.append(line)
            continue

        ending = ""
        if line.endswith("\r\n"):
            ending = "\r\n"
        elif line.endswith("\n"):
            ending = "\n"

        if breaking_re.search(body):
            body_without_breaking = breaking_re.sub("", body).rstrip()
            stamped_body = f"{body_without_breaking} (#{pr_num}) (BREAKING CHANGE)"
        else:
            stamped_body = f"{body.rstrip()} (#{pr_num})"

        new_lines.append(f"{prefix}{stamped_body}{ending}")
        modified = True

    if not modified:
        return False

    new_unreleased = "".join(new_lines)
    new_content = before_unreleased + "## [Unreleased]" + new_unreleased + after_unreleased

    try:
        _ = changelog_path.write_text(new_content, encoding="utf-8")
    except OSError as e:
        print(f"warning: could not write stamped CHANGELOG.md: {e}", file=sys.stderr)
        return False

    try:
        _ = run_command(["git", "add", "CHANGELOG.md"], cwd=cwd, check=True)
        commit_res = run_command(
            ["git", "commit", "-m", f"chore(changelog): attribute #{pr_num} in unreleased ledger"],
            cwd=cwd,
            timeout=60.0,
            env={**os.environ, "HARNESS_CHECK_SKIP_TESTS": "1"},
        )
        if commit_res.returncode != 0:
            print(
                f"warning: git commit failed during changelog stamp: {commit_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        remote = repo_remote_for_ref(head_ref, cwd=cwd)
        push_res = run_command(["git", "push", remote, head_ref], cwd=cwd)
        if push_res.returncode != 0:
            print(
                f"warning: git push to {remote} {head_ref} failed: {push_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        print(
            f"attributed #{pr_num} in CHANGELOG.md and pushed to {remote}/{head_ref}",
            file=sys.stderr,
        )
        return True
    except PrError as e:
        print(f"warning: changelog auto-stamp failed: {e}", file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        options = parse_args(argv)
        head = resolve_head(options.head)
        title, body, title_supplied, body_supplied = resolve_title_and_body(options)
        squash_override, squash_supplied = resolve_squash_override(options)
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
