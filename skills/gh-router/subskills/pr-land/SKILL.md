---
name: pr-land
description: >-
  Create PR, watch verification checks, and squash-merge via gh api. Use when opening pull requests, monitoring CI check-runs, or merging approved PRs.
argument-hint: |-
  "[--title '…'] [--body '…' | --body-file FILE] [--base main] [--head BRANCH] [--check] [--status] [--json] [--out LEAF] [--force-scaffold] [--watch] [--verbose] [--merge] [--draft] [--no-stamp] [--squash-message '…' | --squash-message-file FILE]"
metadata:
  managed-by: gh-router
---

# PR — Create → Watch → Squash-Merge

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Owns the `POST pulls` → `poll every check` → `PUT merge squash` loop. `pr.py` is the only writer. Run it once per phase: `--status` first, then `--check` (see [Flow](#flow)). Never hand-roll `gh` calls. Never invent a squash message.

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`. Invoke them, never restate them.

## Script

Run `$SKILL_DIR/scripts/pr.py` with `uv run` (Python >=3.14, `GH_TOKEN` via `gh auth`). The `$SKILL_DIR/scripts/pr.sh` shim execs it. Shared Python modules resolve repository identity (`_github.repo_slug_from_url`, push remote first) and check verdicts (`_github.checks_verdict`).

```bash
uv run $SKILL_DIR/scripts/pr.py --status --json
uv run $SKILL_DIR/scripts/pr.py --check --body-file .lsz/gh-router/feat-x.md
uv run $SKILL_DIR/scripts/pr.py --title '…' --body-file .lsz/gh-router/feat-x.md
uv run $SKILL_DIR/scripts/pr.py --title '…' --watch --merge --body-file .lsz/gh-router/feat-x.md --squash-message-file .lsz/gh-router/squash_message.md
```

| Flag | Description |
| --- | --- |
| `--base` | Base branch (default `default_branch()`: push-remote slug → `origin/HEAD` → `main`). |
| `--head` | Head branch (default `git rev-parse --abbrev-ref HEAD`). |
| `--title` | PR title (default `git log -1 --pretty=%s <head>`, fallback cwd HEAD). Warns when range has no unique commits. |
| `--body` / `--body-file` | PR description. Required to open a PR. Takes no template default. |
| `--squash-message` / `--squash-message-file` | Explicit squash commit message. Mutually exclusive. Required with `--merge` (no PR-body fallback). |
| `--watch` | Poll every check on the PR (60×10s). See [Flow](#flow) for fast-fail conditions. |
| `--verbose` | Dump full failure logs. Default output is slim. |
| `--merge` | Requires explicit `--squash-message` (file) and green watch. Waits for clean mergeable state, then squashes. |
| `--draft` | Keep new PR as draft after stamping. Skips ready flip. |
| `--no-stamp` | Skip auto-stamping `(#NUM)` into `CHANGELOG.md`. The ready flip still runs. |
| `--check` | Run drafting preflight: gates plus facts on stdout. See [Draft Phase](#draft-phase). |
| `--status` / `--json` | Read-only landing state: predicates, failure states, artifact, title facts, squash preview, `refusals[]`, `transitions[]`. `--status` never refuses (exit 0); `--json` prints the pinned schema. |
| `--out LEAF` | Scaffold leaf under `.lsz/gh-router/` (default `<head-slug>.md`; see [Draft Phase](#draft-phase)). |
| `--force-scaffold` | With a body-less `--check`, regenerate the leaf over an existing file. Otherwise the tool writes nothing and reports path + `stale`. |

## Draft Phase

`--check` is the preflight and drafting pass. It runs the Title Budget, Title Shape, Squash Shape, Body Required, Fail-Closed Squash Message, and Raw Token gates. Facts go to stdout — counts, title facts, the squash preview, and one curation hint (`--json` for machine reading) — commentary goes to stderr, and nothing is persisted except the body-less scaffold below. Run it before creating a PR, and again after each description edit. Before a PR exists, no PR number is known, so the title length check runs against the worst case — the title plus a five-digit ` (#99999)` suffix — and refuses when that exceeds the budget; both lengths are always reported. Re-run `--check` after creating the PR to validate any declared Links section against the known PR link.

```bash
uv run $SKILL_DIR/scripts/pr.py --check --body-file .lsz/gh-router/feat-x.md
uv run $SKILL_DIR/scripts/pr.py --check --out custom/leaf.md
```

`--out LEAF` names the scaffold leaf under `.lsz/gh-router/` (default `<head-slug>.md`, so two branches never collide). Missing parent directories are created automatically. A body-less `--check` writes the leaf only when absent.

Without a supplied body, the leaf is a candidate scaffold: the installed template shape plus mechanical facts only — a `<!-- Range: N commits, +X/-Y across Z files -->` line, the unchosen Door swapped for a `<FILL: one-way | two-way>` sentinel, Root Cause guidance, and detected `Closes #NN` lines or a visible FILL Closes slot. The marker top line names the head commit it was generated from. When the leaf exists the tool writes nothing and reports the path plus `stale` (marker commit vs HEAD); `--force-scaffold` regenerates deliberately. Fill or delete every sentinel before feeding the file back: the create, `--check`, and merge gates all refuse an unfilled placeholder.

A with-body `--check` prints `commits: N`, `trailers: N`, the title facts (`derived`, length, budget), the `squash_body_preview`, and one `hint:` line. A body-less run prints the counts, the leaf path, the hint, and the scaffold payload itself. The hint splits the two duties: the PR body keeps the repo's installed template shape (see `install-template.sh`; prose owned by `pr-enhance`), while the squash overview — never the PR body — is the artifact under the curation spec. An open PR already carries its description: a body-less `--check` gates on the fetched PR body and persists nothing.

`--status` is the machine-readable landing state: predicates (`branch_pushed`, `pr_state`, `body_state`, `checks`, `mergeable`, …), failure states (`diverged`, `head_stale`, `stamp_failed`, `base_unresolvable`), the artifact path plus `stale`, title facts, the squash preview, advisory `refusals[]`, and the legal `transitions[]` (each with its command, preconditions, and `mutation`). It never refuses and always exits 0.
Curate the scaffold leaf before passing it to the create phase as `--body-file`, in the repo's installed PR template shape (Summary · Root Cause for fixes · Blast Radius & Safety · Evidence · Checklist). It keeps the authored body as supplied or fetched, including human-facing Mermaid diagrams and `<details>` blocks; a merge appends `Co-authored-by` trailers itself.

Author prose from the git-diff-digest brief with `pr-enhance`. The PR body is the reviewer's artifact, not the commit message. Author the squash overview as a separate file (at most 5 bullets and 15 lines). Pass that file to `--merge` with `--squash-message-file`. The merge operation never falls back to the PR body. A message that reproduces the scaffold leaf (`.lsz/gh-router/<slug>.md`) is refused.

Exit: `0` gates passed · `1` a gate refused (see below) · `2` usage error, or a body-less `--check` with no open PR (scaffold path).

## Invariants & Gates

| Gate | Observable refusal (stderr) | Exit |
| --- | --- | --- |
| Title Budget | `… exceeds the 100-char budget in the worst case (NN chars bare, MMM chars as … (#99999))` (`--check`, worst case with five-digit suffix) · `refusing squash merge: commit title exceeds 100 chars (NNN): <title> (#N)` (merge, real number) | 1 |
| Title Shape | `… is not a Conventional Commit \`type(scope): subject\` line: …` (`--check`, names `--title` vs `HEAD` derivation) · `refusing squash merge: commit title is not a Conventional Commit "type(scope): subject": <title> (#N)` (merge, real number) | 1 |
| Squash Shape | `refusing squash merge: squash body carries no Core section` · `… a fix squash body carries no Root section` · `… the Blast Radius section carries neither a \`Door:\` line nor the template's \`Rollback / containment:\` line` · `… the Blast Radius section states no rollback` · `… the Evidence section states no before -> after` · `… the Links section carries no PR link` · `… closing-keyword line is not one issue` · `… squash body carries N bullets (max 5)` | 1 |
| Body Required | `refusing to open PR: no --body/--body-file supplied` · `refusing PR: no description supplied` | 1 |
| Fail-Closed Squash Message | `refusing squash merge: --merge requires an explicit squash commit message` (spec: `GLOSSARY.md` — Curated Squash Message) · `refusing squash merge: PR body is empty or the unfilled repo template` (the `--check` preview path) | 1 |
| Raw Token | `refusing squash message: raw CODE_AUTHORS token still present` | 1 |
| Reused Draft | `reused PR #N is still a draft and --draft was not passed` | 1 |
| Ready Flip | `gh pr ready failed for PR #N` + the verbatim `gh pr ready N --repo <repo>` remediation | 1 |
| Checks | `checks failed: failing run id(s): <ids>` + the `gh run view --run-id <id> --log-failed` pointer (slim default; `--verbose` adds the run log and `gh pr checks` tail); `checks timeout after 600s — no green verdict` | 1 |
| Merge State | `refusing to merge: mergeable_state=<state> (not clean)`, preceded by the shared refusal report (`PR <url>` · `<verdict>: mergeable=… merge_state_status=…` · `touched files: …` — every path the PR changes, `(none resolved)` when the read is empty or fails · the pr-conflict pointer) | 1 |
| Pushed Head | `refusing to push <head>: remote <remote>/<head> is ahead …` (never force-pushes; reconcile, then re-run) | 1 |

An explicit `--squash-message` that sanitizes to nothing is a usage error, exit `2`.

The Title Shape gate matches the type case-insensitively (`FEAT:` passes) and keeps the scope and `!` optional. The header ends `(#N)`.

- **Squash Body Hygiene.** Every path to `commit_message` runs `clean_squash_body`. It strips HTML comments and fenced Mermaid blocks (3+ backticks or tildes). It strips line-anchored `<details>…</details>` blocks. Inline `<details>` tags remain untouched. It strips review-only `## Architecture` and `## Verification Evidence` sections. It also removes `## Checklist` items, `Landing:`/`Ledger-Waiver:` directives, checkboxes, and empty headings. Unclosed fences stop at the next heading, `Closes` keyword, or trailer line. It preserves `## Summary`, `## What Changed`, `## Blast Radius & Safety`, `## Evidence`, standalone `Closes #NN` lines, and `Co-authored-by` trailers. Trailers append automatically. The operation is idempotent: the merge path cleans twice.
- **Squash Shape.** The PR body and squash message are separate artifacts. The body keeps full reviewer detail (Mermaid, `<details>`, evidence). The squash message is a curated overview of contract sections only, at most 5 bullets and 15 lines. Both `--check` (preview) and `--merge` (explicit message) run the cleaned shape gate.

  Core is the `## Summary` section (`What Changed` and `Core` are aliases; leading prose counts). Core is required on every path. Root is required only for a `fix` title. Non-`fix` types never need it. Blast Radius, Evidence, and Links are validated only when present. A prose-only body passes with Core alone. When declared, Blast Radius requires a `Door:` line (or the template's `**Rollback / containment:**` label) plus a rollback statement. Evidence requires a before -> after demonstration. Links requires the PR link once the PR exists (see [Draft Phase](#draft-phase)). Each `Closes #NN` line must name exactly one issue.

  The explicit merge path **refuses** shape-gate violations. It refuses non-contract headings (including flush `##Heading`), checkboxes (bare or ordered), Mermaid fences (3+ backticks or tildes), raw `CODE_AUTHORS` block tokens, and line or bullet caps. It also refuses any message that reproduces the body via the copy detector. The copy detector folds case and `-`/`_`, drops `Co-authored-by` lines, and evaluates 5-token shingles. It refuses above 0.80 on either Jaccard similarity or body coverage, with a 25-token floor.

  The explicit path **still sanitizes** HTML comments, `<details>` blocks, `Landing:`/`Ledger-Waiver:` directives, and empty headings, exactly as `--check` does. This enforces the REFUSE-vs-SANITIZE split: refuse forbidden constructs, sanitize cleanable markup. Mermaid diagrams and `<details>` blocks remain in `pr_body.md` for human review.
- **Changelog Auto-Stamping.** Unattributed `## [Unreleased]` entries get `(#PR)` committed and pushed to the branch. `--no-stamp` leaves the ledger to you, and a red changelog gate follows.
- **Ready-Flip Advisory.** After stamping, a new PR whose `## [Unreleased]` entry lacks `(#NUM)` warns on stderr that the Ledger floor gate rejects the ready flip. This warning is advisory only. Exit codes and the flip never change.
- **CI Runs Once Ready.** Workflows trigger on `opened`/`synchronize`/`reopened`/`ready_for_review`, and every job skips drafts. Jobs stage `changelog-gate` → `typecheck` → `tests`.

## Flow

1. **Orient** — run `--status` (`--json` for the pinned schema). Trust its predicates and `transitions[]` for the landing decision; it never refuses. *Done when* `--status` exits `0`.
2. **Draft** — run `--check`. Curate the scaffold leaf it writes (`.lsz/gh-router/<head-slug>.md`) and pass it back as `--body-file`. *Done when* `--check` exits `0`.
3. **Create or reuse** — `GET pulls?head=owner:HEAD` reuses `number` and calls `PATCH title/body`. Otherwise, call `POST pulls` (always with `draft=true`). Stamp `(#NUM)` into unattributed unreleased entries, push, and flip a new PR ready via `gh pr ready`. This fires the `ready_for_review` event. Existing open PRs remain untouched. *Done when* stdout prints `PR <url>` and the ready flip exits `0`.
4. **Watch** (`--watch`) — poll all check-runs and commit statuses: `gh pr checks --json name,bucket` → `checks_verdict`. Each poll prints one stderr line: `checks <verdict> (mergeable_state=<state>, <i>/<tries>)`. A `behind` head appends `, head behind <base>`. Resolve mergeability first. An `unknown` state retries 5×2s (~8s) and refuses through the shared report with verdict `unknown`. A `dirty` reading requires confirmation twice 3s apart before counting as conflicting. Non-dirty readings reset strikes. A `behind` head is accepted with a folded warning. Default output is slim. A `failure` verdict prints failing run IDs plus a `gh run view --run-id <id> --log-failed` pointer (or `ci.sh why`). A timeout prints only its line. Pass `--verbose` to view full tails. *Done when* stderr prints `checks success`. A `failure` verdict exits `1`. Only a `pending` verdict continues polling up to 60×10s.
5. **Merge** (`--merge`) — require an explicit `--squash-message` (or `--squash-message-file`) and a green watch. The title gate runs before any `gh` mutation. Resolve `mergeable_state` using the same retry budgets (unknown 5×2s, dirty debounced 2×3s). A conflicting or unresolved state fails fast through the shared refusal report (`PR <url>`, verdict, touched files, pr-conflict pointer). A `behind` head and any other non-`clean` state refuse. A missing explicit message refuses before any `PUT`. There is no PR-body fallback. Finally, run `PUT pulls/$NUM/merge merge_method=squash` with `commit_title=<title> (#N)` and `commit_message` set to the cleaned explicit message with rebuilt trailers. *Done when* stderr prints `merged #N (squash) to <base>`.

Fail-loud, no secrets in logs: PR URL on stdout, progress on stderr. Re-trigger is model-driven — the script returns failure info, the model edits, pushes, and re-runs `--watch --merge`.
