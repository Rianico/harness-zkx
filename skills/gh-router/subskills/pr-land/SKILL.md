---
name: pr-land
description: >-
  Create PR, watch verification checks, and squash-merge via gh api. Use when opening pull requests, monitoring CI check-runs, or merging approved PRs.
arguments: title_or_branch
argument-hint: |-
  "[--title '…'] [--body '…' | --body-file FILE] [--base main] [--head BRANCH] [--check] [--out-dir DIR] [--watch] [--verbose] [--merge] [--draft] [--no-stamp] [--squash-message '…' | --squash-message-file FILE]"
metadata:
  managed-by: gh-router
---

# PR — Create → Watch → Squash-Merge

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Owns the `POST pulls` → `poll every check` → `PUT merge squash` loop. `pr.py` is the only writer: run it once per phase, `--check` first (see [Draft Phase](#draft-phase)); never hand-roll `gh` calls and never invent a squash message.

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Script

`$SKILL_DIR/scripts/pr.py` (755, Python >=3.14 via `uv run`, `GH_TOKEN` via `gh auth`; accompanied by thin backward-compatible `$SKILL_DIR/scripts/pr.sh`). Repo identity and the check verdict come from the skill's shared modules — `$SKILL_DIR/../../lib/repo.sh` (push remote first; `gh repo view` only as last resort) and `$SKILL_DIR/../../lib/checks.sh` — re-implemented cleanly in Python.

```bash
uv run $SKILL_DIR/scripts/pr.py --check --body-file .lsz/tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.py --body-file .lsz/tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.py --watch --merge --body-file .lsz/tmp/pr_body.md
```

Flags: `--base` (default `default_branch()` — push-remote slug → `origin/HEAD` → `main`), `--head` (`git rev-parse --abbrev-ref HEAD`), `--title` (default `git log -1 --pretty=%s <head>`, fallback cwd HEAD; a guess warning prints when the range holds no unique commits), `--body` / `--body-file` (required to open a PR — takes no template default), `--squash-message` / `--squash-message-file` (explicit squash commit message; mutually exclusive; sanitized through the same hygiene as a derived message), `--watch` (poll **every** check on the PR via `gh pr checks --json name,bucket`, 60×10s; one stderr line per poll — a `behind` head rides that same line, and a conflict or an unresolved mergeability fails fast), `--verbose` (dump the full failure logs; the default is slim — see [Watch](#flow)), `--merge` (requires a green watch; waits `mergeable_state clean`, refuses otherwise — a `behind` head the watch accepted is refused here — then `PUT merge squash`), `--draft` (keep the PR draft after stamping — skips the ready flip; default ends a newly created PR ready; an existing open PR is never readied or re-drafted, and a reused draft without `--draft` exits `1` naming the manual `gh pr ready` remediation), `--no-stamp` (skips auto-stamping `(#NUM)` into `CHANGELOG.md`; the ready flip still happens), `--check` / `--out-dir` (draft phase, below).

## Draft Phase

`--check` is the preflight and drafting pass: it runs the Title Budget, Title Shape, Squash Shape, Body Required, Fail-Closed Squash Message, and Raw Token gates, appends the trailers a merge would carry, writes `<out-dir>/draft.json` + `<out-dir>/pr_body.md`, and creates nothing. Run it before the create phase, and again after each description edit. Before a PR exists there is no PR number, so a declared Links section cannot be validated yet: re-run `--check` after the create phase, where the PR link is known.

```bash
uv run $SKILL_DIR/scripts/pr.py --check --body-file .lsz/tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.py --check --body-file tmp/drafts/pr_body.md --out-dir tmp/drafts
```

`--out-dir DIR` sets the directory; the default is `<repo-root>/.lsz/tmp`, and missing parents are created. Every run writes both files, a refused run included.

stdout stays small — `commits: N`, `trailers: N`, both paths, one `hint:` line. The full text lives on disk only. `draft.json` carries the range facts (one row per commit: full `sha`, `subject`, `body` capped at 15 lines), the trailers, and `squash_body` (the cleaned text a merge would commit), plus `pr_number` / `pr_url` (null before a PR exists), `status` / `exit_code` / `note`, a `dirty` block (porcelain plus diff stat, empty when clean — uncommitted work never enters the fingerprint), and `dirty_files` in `counts`.

Curate `<out-dir>/pr_body.md` — the authored body exactly as supplied or fetched (Mermaid and `<details>` kept, since they are for humans) plus the `Co-authored-by` trailers a merge would append — then pass it to the create phase. Author the prose from the git-diff-digest brief with `pr-enhance`; a hand-written squash message is `--squash-message`, never improvisation at merge time.

Exit: `0` gates passed · `1` a gate refused (see below) · `2` usage error, or no body supplied while no PR exists for the head.

## Invariants & Gates

| Gate | Observable refusal (stderr) | Exit |
| --- | --- | --- |
| Title Budget | `refusing squash merge: commit title exceeds 100 chars (NNN): <title> (#N)` | 1 |
| Title Shape | `refusing squash merge: commit title is not a Conventional Commit "type(scope): subject": <title> (#N)` | 1 |
| Squash Shape | `refusing squash merge: squash body carries no Core section` · `… a fix squash body carries no Root section` · `… the Blast Radius section carries neither a \`Door:\` line nor the template's \`Rollback / containment:\` line` · `… the Blast Radius section states no rollback` · `… the Evidence section states no before -> after` · `… the Links section carries no PR link` · `… closing-keyword line is not one issue` · `… squash body carries N bullets (max 5)` | 1 |
| Body Required | `refusing to open PR: no --body/--body-file supplied` · `refusing PR: no description supplied` | 1 |
| Fail-Closed Squash Message | `refusing squash merge: PR body is empty or the unfilled repo template` | 1 |
| Raw Token | `refusing squash message: raw CODE_AUTHORS token still present` | 1 |
| Reused Draft | `reused PR #N is still a draft and --draft was not passed` | 1 |
| Ready Flip | `gh pr ready failed for PR #N` + the verbatim `gh pr ready N --repo <repo>` remediation | 1 |
| Checks | `checks failed: failing run id(s): <ids>` + the `gh run view --run-id <id> --log-failed` pointer (slim default; `--verbose` adds the run log and `gh pr checks` tail); `checks timeout after 600s — no green verdict` | 1 |
| Merge State | `refusing to merge: mergeable_state=<state> (not clean)`, preceded by the shared refusal report (`PR <url>` · `<verdict>: mergeable=… merge_state_status=…` · `touched files: …` — every path the PR changes, `(none resolved)` when the read is empty or fails · the pr-conflict pointer) | 1 |
| Pushed Head | `failed to create PR: …` (head missing on the remote) | 1 |

An explicit `--squash-message` that sanitizes to nothing is a usage error, exit `2`.

- **Squash Body Hygiene.** Every path to `commit_message` runs `clean_squash_body`: strips HTML comments, fenced ```mermaid blocks, line-anchored `<details>…</details>` blocks (a `<details>` opened mid-line is prose and is left alone), the review-only `## Architecture` / `## Verification Evidence` sections, `## Checklist` items, `Landing:` / `Ledger-Waiver:` directives, checkbox lines, and empty headings; unclosed fences/blocks stop at the next heading, `Closes` keyword, or trailer line. Preserves `## Summary`, `## What Changed`, `## Blast Radius & Safety`, `## Evidence`, `Closes #NN` on standalone lines, and `Co-authored-by` trailers, appending the latter automatically. Idempotent — the merge path cleans twice.
- **Squash Shape.** `--check` and the merge both run the same gate over the cleaned body. Core is required on every path. Root is required only for a `fix` title — non-`fix` types never need it. Blast Radius, Evidence, and Links are validated only when their section is present, so a prose-only body passes with Core alone; when declared, Blast Radius needs a `Door:` line (or the shipped template's `**Rollback / containment:**` label) plus a rollback statement, Evidence needs a before -> after, and Links needs the PR link once the PR exists (see [Draft Phase](#draft-phase)). Each `Closes #NN` line names one issue. Validation only — Mermaid and `<details>` stay in the PR body (`pr_body.md`) for humans.
- **Changelog Auto-Stamping.** Unattributed `## [Unreleased]` entries get `(#PR)` committed and pushed to the branch. `--no-stamp` leaves the ledger to you, and a red changelog gate follows.
- **Ready-Flip Advisory.** After stamping, a new PR whose `## [Unreleased]` entry lacks `(#NUM)` warns on stderr that the Ledger floor gate rejects the ready flip. Advisory only: exit codes and the flip never change.
- **CI Runs Once Ready.** Workflows trigger on `opened`/`synchronize`/`reopened`/`ready_for_review`, and every job skips drafts. Jobs stage `changelog-gate` → `typecheck` → `tests`.

## Flow

1. **Draft** — run `--check`; read `draft.json`, curate `pr_body.md`. *Done when* `--check` exits `0`.
2. **Create or reuse** — `GET pulls?head=owner:HEAD` reuses `number` + `PATCH title/body`, else `POST pulls` (always `draft=true`). Stamps `(#NUM)` into unattributed unreleased entries, pushes, then flips a new PR ready via `gh pr ready` so the `ready_for_review` event fires. Existing open PRs stay untouched. *Done when* stdout prints `PR <url>` and the ready flip exits `0`.
3. **Watch** (`--watch`) — every check-run *and* commit status counts: `gh pr checks --json name,bucket` → `checks_verdict`. One stderr line per poll carries both halves of the state: `checks <verdict> (mergeable_state=<state>, <i>/<tries>)`, with `, head behind <base>` appended for a `behind` head. Mergeability is resolved first: `unknown` retries 5×2s (~8s) and then refuses through the shared report with the verdict word `unknown` (never `conflicting`) so an unresolved PR never burns the 60×10s poll budget; `dirty` is confirmed twice 3s apart before it counts as a conflict (any non-dirty reading resets the strikes). A `behind` head is accepted here with the warning folded into the poll line. Default output is slim — a `failure` verdict prints the failing run ID(s) plus a `gh run view --run-id <id> --log-failed` pointer (or `ci.sh why`), and a timeout prints only its line; `--verbose` adds the `gh run view` tails and the `gh pr checks` dump. *Done when* stderr prints `checks success`; a `failure` verdict exits `1`, only a `pending` verdict keeps polling to 60×10s.
4. **Merge** (`--merge`) — requires a green watch even without `--watch`, then resolves `mergeable_state` with the same budgets (unknown 5×2s; a `dirty` reading is debounced 2×3s): a conflicting or unresolved state fails fast through the shared refusal report (`PR <url>`, verdict, `touched files: …`, the pr-conflict pointer) instead of waiting out the retries; a `behind` head (which the watch accepted with a warning) and any other non-`clean` state refuse. Then `PUT pulls/$NUM/merge merge_method=squash` with `commit_title=<title> (#N)` and a `commit_message` built from the body plus rebuilt trailers. *Done when* stderr prints `merged #N (squash) to <base>`.

Fail-loud, no secrets in logs: PR URL on stdout, progress on stderr. Re-trigger is model-driven — the script returns failure info, the model edits, pushes, and re-runs `--watch --merge`.
