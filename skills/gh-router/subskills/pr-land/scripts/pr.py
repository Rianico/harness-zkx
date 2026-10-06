#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# ///
"""pr.py — create pull request, watch every check, squash-merge (deterministic bytes)

Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge|--no-merge] [--draft] [--check] [--no-stamp] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; on failure dump logs and exit 1 for the model to fix
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; refuses otherwise)
  --check : dry run — print the Co-authored-by trailers a merge would append, then exit (no PR created)
  --draft : leave the PR a draft after stamping (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens
    (the caller owns the changelog) — the head was not stamped, so expect a red changelog gate
  --squash-message / --squash-message-file : explicit squash commit message (mutually exclusive)
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
Commit title length is strictly limited to 100 characters (TITLE (#NUM) <= 100).
Env: GH_TOKEN via gh auth. PR URL on stdout, progress on stderr. Fails loud, no secrets in logs.
Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref
"""

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

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

SQUASH_TITLE_MAX = 100
CODE_AUTHORS_TOKEN = "CODE_AUTHORS"
DEFAULT_TEMPLATE_PATH = Path(".github/pull_request_template.md")
POLL_TRIES = 60
POLL_INTERVAL = 10.0
MERGE_STATE_TRIES = 5
MERGE_STATE_INTERVAL = 2.0
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


def print_usage() -> None:
    usage = """pr.py — create pull request, watch every check, squash-merge (deterministic bytes)
Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge|--no-merge] [--draft] [--check] [--no-stamp] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; on failure dump logs and exit 1 for the model to fix
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; refuses otherwise)
  --check : dry run — print the Co-authored-by trailers a merge would append, then exit (no PR created)
  --draft : leave the PR a draft (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens (caller owns the changelog) — head unstamped, expect a red changelog gate
  --body/--body-file : required to open a PR; the caller drafts the description (pr-enhance workflow). An empty body or the unfilled repo template is refused.
  --squash-message/--squash-message-file : explicit squash commit message (mutually exclusive); a squash merge never omits commit_message (explicit or derived) — an empty/template body without an explicit message is refused (exit 1), never GitHub's commit-subject synthesis.
Draft handshake: a NEWLY CREATED PR is created as a draft (draft=true), stamped (commit+push), then readied via gh pr ready so CI's ready_for_review fires; a failed flip prints the verbatim manual fix and exits 1. Existing open PRs are reused untouched — never readied, never re-drafted; a reused draft without --draft fails loudly with the same manual remediation and exits 1.
Squash body is the PR body plus one Co-authored-by trailer per distinct PR commit author except the merger (an explicit commit_message disables GitHub's own auto-attribution, so the script rebuilds it). A body still holding the raw CODE_AUTHORS template token is refused pre-merge.
Commit title length is strictly limited to 100 characters (TITLE (#NUM) <= 100).
Env: GH_TOKEN via gh auth. PR URL on stdout, progress on stderr. Fails loud, no secrets in logs.
Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref"""
    print(usage)


def parse_args(args: list[str]) -> PrOptions:
    base: str | None = None
    head: str | None = None
    title: str | None = None
    title_supplied = False
    body: str | None = None
    body_supplied = False
    body_file: Path | None = None
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied = False
    watch = False
    merge = False
    check = False
    draft = False
    no_stamp = False

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
        watch=watch,
        merge=merge,
        check=check,
        draft=draft,
        no_stamp=no_stamp,
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
        if out:
            return out
    return "main"


def resolve_title_and_body(
    options: PrOptions, cwd: Path | None = None
) -> tuple[str, str, bool, bool]:
    title = options.title
    title_supplied = options.title_supplied
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
    blocks → review-only sections → procedural sections → directives →
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
        "remediation: draft the description via the pr-enhance workflow "
        "(analyze-pr.py → draft → tmp/pr_body.md), then pass it with --body-file",
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
            "remediation: draft the description via the pr-enhance workflow, "
            "then pass an explicit message with --squash-message (or --squash-message-file)",
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


def check_conflicts(repo: str, num: str, base: str, cwd: Path | None = None) -> bool:
    tries = 3
    verdict = ""
    mergeable = ""
    state = ""
    url = ""
    last_error = ""
    while tries > 0:
        tries -= 1
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
            last_error = res.stderr.strip() or "gh api failed"
            if tries > 0:
                time.sleep(1)
                continue
            raise PrError(f"failed to check PR #{num} mergeable state: {last_error}")

        line = res.stdout.strip()
        if not line:
            if tries > 0:
                time.sleep(1)
                continue
            raise PrError(f"failed to check PR #{num} mergeable state: empty response from gh api")

        parts = line.split("\t")
        mergeable = parts[0] if len(parts) > 0 else ""
        state = parts[1] if len(parts) > 1 else ""
        url = parts[2] if len(parts) > 2 else ""
        verdict = pr_conflict_verdict(mergeable, state)
        if verdict != "unknown":
            break
        if tries > 0:
            time.sleep(1)

    if verdict == "conflicting":
        files_res = run_command(
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
        files = files_res.stdout.strip() if files_res.returncode == 0 else ""
        print(f"PR {url}", file=sys.stderr)
        print(
            f"conflicting: mergeable={mergeable} merge_state_status={state}",
            file=sys.stderr,
        )
        if files:
            print(f"files: {files}", file=sys.stderr)
        print(
            "conflict detected: run 'uv run skills/gh-router/subskills/pr-conflict/scripts/extract_conflict_context.py' to inspect hunks and commit intent, then delegate resolution to a worker subagent.",
            file=sys.stderr,
        )
        return False
    if verdict == "behind":
        print(f"warning: head branch is behind {base}", file=sys.stderr)
    return True


def dump_failure_logs(repo: str, num: str, cwd: Path | None = None) -> None:
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
) -> bool:
    for i in range(1, poll_tries + 1):
        if not check_conflicts(repo, num, base, cwd=cwd):
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
        if verdict == "success":
            print("checks success", file=sys.stderr)
            return True
        if verdict == "failure":
            print("checks failed — fetching logs", file=sys.stderr)
            dump_failure_logs(repo, num, cwd=cwd)
            return False
        print(f"checks pending ({i}/{poll_tries})…", file=sys.stderr)
        time.sleep(poll_interval)

    print(
        f"checks timeout after {int(poll_tries * poll_interval)}s — no green verdict",
        file=sys.stderr,
    )
    last_checks = run_command(
        ["gh", "pr", "checks", num, "--repo", repo],
        cwd=cwd,
    )
    combined = (last_checks.stdout + last_checks.stderr).splitlines()
    tail_lines = combined[-30:]
    if tail_lines:
        print("\n".join(tail_lines), file=sys.stderr)
    return False


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
            return 2

        if title:
            try:
                check_title_length(title, 9999)
            except RefusalError:
                return 1

        try:
            resolved_msg = resolve_squash_message(
                body,
                explicit=squash_message_override,
                supplied=squash_message_supplied,
                template_path=template_path,
            )
        except RefusalError:
            return 1

        log_res = run_command(
            ["git", "log", f"origin/main..{head_ref}", "--pretty=format:\t%an\t%ae"],
            cwd=cwd,
        )
        if log_res.returncode != 0:
            log_res = run_command(
                ["git", "log", f"main..{head_ref}", "--pretty=format:\t%an\t%ae"],
                cwd=cwd,
            )
        if log_res.returncode != 0:
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
        if new_trailers.strip():
            print(new_trailers, end="")
        else:
            print(f"no co-author trailers would be appended for {head_ref}", file=sys.stderr)
        return 0

    num = found

    try:
        check_title_length(title, num)
    except RefusalError:
        return 1

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
        return 1

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
        return 1
    tsv = tsv_res.stdout

    try:
        _ = build_squash_message(resolved_msg, merger, tsv)
    except RefusalError:
        return 1

    new_trailers = pr_co_author_trailers(tsv, merger=merger, body=resolved_msg)
    if new_trailers.strip():
        print(new_trailers, end="")
    else:
        print(f"no co-author trailers would be appended for #{num}", file=sys.stderr)
    return 0


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
            "remediation: draft the description via the pr-enhance workflow "
            "(analyze-pr.py → draft → tmp/pr_body.md), then re-run with --body-file",
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
    check_title_length(title, num)
    state = "unknown"
    for _ in range(MERGE_STATE_TRIES):
        st_res = run_command(
            ["gh", "api", f"repos/{repo}/pulls/{num}", "--jq", ".mergeable_state"],
            cwd=cwd,
        )
        state = (
            st_res.stdout.strip() if st_res.returncode == 0 and st_res.stdout.strip() else "unknown"
        )
        if state == "clean":
            break
        print(f"mergeable_state={state} waiting…", file=sys.stderr)
        time.sleep(MERGE_STATE_INTERVAL)

    if state != "clean":
        print(f"refusing to merge: mergeable_state={state} (not clean)", file=sys.stderr)
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
            return check_trailers(
                repo=repo,
                head_ref=head,
                body=body,
                body_supplied=body_supplied,
                title=title,
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
        elif created:
            print(
                f"warning: --no-stamp: head was not stamped for PR #{num} — "
                "expect a red changelog gate until it is stamped and pushed",
                file=sys.stderr,
            )

        if created and not options.draft:
            if not ready_pr(repo, num):
                return 1

        if options.watch:
            if not watch_checks(repo, num, base):
                return 1

        if options.merge:
            if not options.watch:
                if not watch_checks(repo, num, base):
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
