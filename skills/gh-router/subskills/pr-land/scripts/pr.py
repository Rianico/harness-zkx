#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# ///
"""pr.py — create pull request, watch every check, squash-merge (deterministic bytes)

Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--verbose] [--merge|--no-merge] [--draft] [--check] [--status] [--json] [--out LEAF] [--no-stamp] [--force-scaffold] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; one stderr line per poll (mergeable_state + verdict); a conflicting or unresolved PR fails fast, exit 1
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; a conflicting or unresolved PR fails fast, refuses otherwise)
  --check : preflight + draft phase — run the merge gates and print counts, title facts, the squash preview, and one curation hint (no PR created; refusals carry reason/remedy/site on stderr)
  --status : read-only landing state — predicates, failure states, artifact, title facts, squash preview, refusals[] and transitions[] (never refuses, always exit 0; --json for the pinned schema)
  --out LEAF : scaffold leaf under <repo-root>/.lsz/gh-router/ (default <head-slug>.md); a body-less --check writes it only when absent
  --force-scaffold : with a body-less --check, regenerate the scaffold leaf over an existing file (default: write nothing, report path + stale)
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
Env: GH_TOKEN via gh auth. PR URL on stdout (facts on --check/--status), progress on stderr. Fails loud, no secrets in logs.
Exit: 0 ok | 1 checks failed, body refused, gh pr ready failed, or merge refused | 2 usage or unusable head ref → default slim; --verbose dumps the logs
"""

import json
import sys
from pathlib import Path

_LIB_DIR: str = str(Path(__file__).resolve().parents[3] / "lib")
if _LIB_DIR not in sys.path:
    sys.path.insert(0, _LIB_DIR)

import _github
from _changelog import stamp_changelog, stamp_needed, unreleased_attributes_pr, warn_ledger_gap
from _draft import run_draft_phase
from _errors import REFUSAL_SCHEMA, PrError, RefusalError, UsageError
from _github import (
    classify_failure,
    merge_pr,
    pr_url,
    ready_pr,
    resolve_base,
    resolve_head,
    resolve_repo,
    resolve_title_and_body,
    warn_closed_issues,
    watch_checks,
)
from _options import PrOptions, resolve_squash_override
from _squash import (
    DEFAULT_TEMPLATE_PATH,
    check_explicit_squash_message,
    clean_squash_body,
    is_unfilled_body,
    print_squash_message_required,
    refuse_mechanic_copy,
    refuse_unfilled_body,
    refuse_unfilled_sentinels,
)
from _status import make_refusal, make_transition, preflight_title, run_status


def print_usage() -> None:
    usage = """pr.py — create pull request, watch every check, squash-merge (deterministic bytes)
Usage: pr.py [--title "…"] [--body "…" | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--verbose] [--merge|--no-merge] [--draft] [--check] [--status] [--json] [--out LEAF] [--no-stamp] [--force-scaffold] [--squash-message MSG | --squash-message-file FILE]
  --watch : poll EVERY check on the PR until all pass; one stderr line per poll (mergeable_state + verdict); a conflicting or unresolved PR fails fast, exit 1
  --merge : after a green watch, squash-merge (waits for mergeable_state clean; a conflicting or unresolved PR fails fast, refuses otherwise)
  --check : preflight + draft phase — run the merge gates, print counts, title facts, the squash preview, one curation hint (no PR created; body-less runs write the scaffold leaf only when absent, --force-scaffold regenerates)
  --status : read-only landing state, always exit 0 (--json for the pinned schema)
  --out LEAF : scaffold leaf under <repo-root>/.lsz/gh-router/ (default <head-slug>.md)
  --draft : leave the PR a draft (no gh pr ready); default / --no-draft ends a NEWLY CREATED PR ready; an existing open PR is never readied or re-drafted (a reused draft without --draft exits 1 with the manual fix)
  --no-stamp : skip auto-stamp (#<PR_NUMBER>) in CHANGELOG.md unreleased ledger; the flip to ready still happens (caller owns the changelog) — head unstamped, expect a red changelog gate
  --body/--body-file : required to open a PR; the caller drafts the description (pr-enhance workflow). An empty body or the unfilled repo template is refused.
  --squash-message/--squash-message-file : explicit squash commit message (mutually exclusive); REQUIRED with --merge — no PR-body fallback (spec: GLOSSARY.md "Curated Squash Message"). --check still previews a derived message.
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
    out: Path | None = None
    squash_message: str | None = None
    squash_message_file: Path | None = None
    squash_message_supplied = False
    watch = False
    merge = False
    status = False
    json_output = False
    check = False
    draft = False
    no_stamp = False
    verbose = False
    force_scaffold = False

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
        elif arg == "--out":
            if i + 1 >= len(args):
                raise UsageError("missing argument for --out")
            out = Path(args[i + 1])
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
        elif arg == "--status":
            status = True
            i += 1
        elif arg == "--no-status":
            status = False
            i += 1
        elif arg == "--json":
            json_output = True
            i += 1
        elif arg == "--no-json":
            json_output = False
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
        elif arg == "--force-scaffold":
            force_scaffold = True
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
        out=out,
        watch=watch,
        merge=merge,
        check=check,
        status=status,
        json_output=json_output,
        draft=draft,
        no_stamp=no_stamp,
        verbose=verbose,
        title_supplied=title_supplied,
        body_supplied=body_supplied,
        squash_message=squash_message,
        squash_message_file=squash_message_file,
        squash_message_supplied=squash_message_supplied,
        force_scaffold=force_scaffold,
    )


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
    manual remediation instead of returning success. On the fresh-create path the branch
    is pushed to its configured remote first, so the PR opens against the real head.
    """
    template_path = (cwd / DEFAULT_TEMPLATE_PATH) if cwd else DEFAULT_TEMPLATE_PATH
    if body_supplied and is_unfilled_body(body, template_path=template_path):
        refuse_unfilled_body(body)
    if body_supplied:
        refuse_unfilled_sentinels(body)

    ref = _github.lookup_pr(repo, head_ref, state="open", cwd=cwd)
    if ref is not None:
        num = ref.number
        is_draft = ref.is_draft
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
            raise RefusalError(
                f"reused PR #{num} is still a draft",
                refusals=[
                    make_refusal(
                        "pr_draft",
                        f"reused PR #{num} is still a draft and --draft was not passed; "
                        "reuse never mutates draft state, so CI never ran",
                        f"run manually: gh pr ready {num} --repo {repo}",
                        f"PR #{num}",
                    )
                ],
                transitions=[
                    make_transition(
                        f"gh pr ready {num} --repo {repo}",
                        ["changelog_stamped"],
                        "remote",
                    )
                ],
            )
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
                required=True,
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
                required=True,
            )
            final_body = b_res.stdout

        if patch_args:
            _ = _github.run_command(
                ["gh", "api", f"repos/{repo}/pulls/{num}", "-X", "PATCH", *patch_args],
                cwd=cwd,
                required=True,
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
        raise RefusalError(
            "no PR body supplied",
            refusals=[
                make_refusal(
                    "body_missing",
                    "no PR body supplied; opening a PR requires a description",
                    "draft the description from the git-diff-digest surface (skills/gh-router/subskills/git-diff-digest), then re-run with --body-file",
                    "--body-file",
                )
            ],
        )

    _github.ensure_branch_pushed(head_ref, cwd=cwd)

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
        required=True,
    )
    num = create_res.stdout.strip()
    print(f"created PR #{num} (draft)", file=sys.stderr)
    return num, title, final_body, True


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    try:
        options = parse_args(argv)
        if options.status:
            if options.merge or options.watch:
                raise UsageError(
                    "--status combined with --merge/--watch: --status is read-only and merges nothing; drop the mutating flag"
                )
            # Read-only orientation first: derived state, advisory facts, always
            # exit 0 — even when the head ref or repo slug cannot be resolved.
            return run_status(options)
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
            # The title gate runs before create_or_reuse_pr: a bad title refuses
            # here (exit 1, facts attached) instead of after watch/merge work.
            # merge_pr keeps its authoritative check against the real PR number.
            preflight_title(title, derived=not title_supplied)
        repo = resolve_repo(head)

        if options.check:
            # Advisory-only: a Closes #N on an already-closed issue warns, never refuses.
            _ = warn_closed_issues(repo, body, squash_override or "")
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
            if created and stamp_needed(num) and not stamp_changelog(head, num):
                # The stamp had an entry to attribute and failed: hard-fail with
                # the PR url and the remedy. The no-op and stranded-recovery paths
                # below stay soft (T1): only a failed wanted stamp refuses.
                raise RefusalError(
                    f"changelog stamp failed for PR #{num} ({url}); "
                    f"the stamp did not complete (see the warning above); "
                    f"the (#{num}) entry must exist and be pushed",
                    refusals=[
                        make_refusal(
                            "stamp_failed",
                            f"changelog stamp failed for PR #{num} ({url}); "
                            f"the stamp did not complete (see the warning above); "
                            f"the (#{num}) entry must exist and be pushed",
                            f"make sure an entry ending in (#{num}) exists under ## [Unreleased], "
                            f"commit it to {head}, push, then re-run",
                            "CHANGELOG.md",
                        )
                    ],
                )
            elif not created or not stamp_needed(num):
                _ = stamp_changelog(head, num)
        if created and not unreleased_attributes_pr(num):
            warn_ledger_gap(num, options.draft, options.no_stamp, final_title)
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
            # Advisory-only: warn on a Closes #N already closed, then merge regardless.
            _ = warn_closed_issues(repo, final_body, squash_override or "")
            _ = merge_pr(
                repo=repo,
                num=num,
                base=base,
                title=final_title,
                body=final_body,
                squash_message_override=squash_override,
                squash_message_supplied=squash_supplied,
            )
        return 0

    except UsageError as e:
        print(f"{e}", file=sys.stderr)
        return 2
    except RefusalError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        refusals = exc.refusals or [
            make_refusal(
                "refused",
                str(exc) or "refused",
                "see the stderr line above and re-run",
                "unknown",
            )
        ]
        print(json.dumps({"schema": REFUSAL_SCHEMA, "refusals": refusals}, indent=2))
        if exc.transitions:
            print(
                json.dumps({"transitions": exc.transitions}, indent=2),
                file=sys.stderr,
            )
        return 1
    except PrError as e:
        failure = classify_failure(e)
        entry = make_refusal(failure.code, str(e), failure.remedy, failure.tool)
        print(json.dumps({"refusals": [entry], "transitions": []}, indent=2), file=sys.stderr)
        print(f"pr error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
