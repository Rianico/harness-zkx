# Git Convention — daily default

`dev worktree → task sub-worktree → squash to dev → curated [Unreleased] → PR → squash to main` — never auto-merge.

## 1. Branch

- `dev` or `dev/<milestone>` for integration/staging; `feat|fix|doc/<slug>` for task branches. Never commit directly on `main`.

## 2. Repo identity

- **Inference lies.** In a multi-remote checkout (fork + upstream, two projects), `gh repo view` and every `gh` command without `--repo` may resolve to the _upstream_, not the remote you push to. `origin` is not proof of the push target — `branch.<ref>.pushRemote` is.
- **Truth, in order:** `branch.<ref>.pushRemote` → `branch.<ref>.remote` → `origin`, then `git remote get-url --push <remote>` → `owner/name`.
- **Pin it:** `--repo owner/name` on `gh run|pr|issue|release`, `gh api repos/owner/name/...`. `gh repo view` is a last-resort fallback only when no remote parses.
- **Pre-flight:** before a repo-mutating call (dispatch, release, run lookup, PR/issue write), print the resolved slug and confirm it against `git remote -v`.
- **Class fix:** when a slug/identity bug lands in one script, `rg -n 'gh repo view'` the toolchain before closing — same trap, different call site.

## 3. Worktree & Hierarchy

- **Architecture:** `dev` worktree is the integration anchor; task worktrees branch off `dev`.
  - `dev` worktree: created from `main`. Staging ground for cohesive deliverable.
  - Sub-worktree per task: `wt switch --create <task> --base dev --no-cd` in sibling dir.
- **Commit hygiene:**
  - Iterative review / exploratory commits live inside task sub-worktree.
  - Squash-merge task worktree back into `dev` (`wt merge --squash`) with clean, atomic Conventional Commit(s).
  - `dev` worktree may accumulate multiple features/fixes across task merges.
  - When merging `dev` to `main` via PR: squash-merge into `main` with clean summary commit.
- **Use `wt`:** `wt switch` / `wt merge` / `wt list --format=json`. Raw `git worktree` / `git merge` bypasses hooks, `copy-ignored`, and port allocation.
- **Truth:** `.config/wt.toml` — don't restate hooks in prose.

## 4. Gate

- `.config/wt.toml [pre-merge]` runs on every `wt merge`. Merge only when green.

## 5. Commits & Changelog Ledger

- **Curated `[Unreleased]` Ledger:**
  - Both internal and external PRs carry curated entries under `## [Unreleased]` in `CHANGELOG.md`.
  - Entries are attributed with `(#N)`. When a `dev` worktree PR contains multiple features, multiple entries are expected.
  - CI gate (`scripts/changelog-gate.py` via `changelog-check.yml`) verifies:
    - `CHANGELOG.md` starts with `# Changelog`.
    - Every PR entry under `## [Unreleased]` references the PR (`(#N)`).
    - Unattributed entries match baseline or PR waiver.
- **PR tooling & squash-merge hygiene:**
  - `pr.py` (in the `gh-router` skill: `subskills/pr-land/scripts/pr.py`) auto-attributes `(#N)` upon PR creation so the changelog ledger gate stays green without manual intervention.
  - Squash commit body cleans ephemeral review and CI procedural noise (`## Checklist`, `Landing: squash`, `Ledger-Waiver:`, HTML comments, empty headings, fenced Mermaid diagrams, `<details>` blocks, `## Architecture`, and `## Verification Evidence`) while preserving authored sections (`## Summary`, `## What Changed`, `## Blast Radius & Safety`, `## Evidence`), `Closes #NN` issue closing directives, and `Co-authored-by:` trailers. `pr.py` requires an explicit `--squash-message` / `--squash-message-file` on the merge path (no PR-body fallback, exit 1) and fails closed (exit 1) if the `--check` preview body is empty or unfilled without one, preventing mechanical commit subject dumps on squash.
- **Escape and debt:** A blocked changelog gate can be waived via `Ledger-Waiver: <reason>` in PR body (or `--waiver "<reason>"`). Accepts fixable findings only, never unverified code. Unattributed baseline (`.config/changelog-unattributed-baseline.txt`) is a migration bridge.
- **Conventional Commits (1.0.0 + semver):** `type[(scope)][!]: description`
  - Blank line → body (what/why) → blank line → footer(s).
  - `feat` = MINOR, `fix` = PATCH, `!` / `BREAKING CHANGE:` = MAJOR; other types (`docs|style|refactor|perf|test|build|ci|chore|revert`) no bump unless breaking.
  - Scope `(<noun>)`; description imperative, lowercase, no period, ≤72 (50 ideal).
  - Footer `Token: value` or `Token #value`; `BREAKING CHANGE` uppercase (alias `BREAKING-CHANGE`).
  - Ex: `feat(auth): add worktree pre-merge gate` · `fix(api)!: drop legacy field` + `BREAKING CHANGE: removes field x` / `Closes #12`
- **Issue closing directives (PR body & commit footers):**
  - Use GitHub closing keywords: `Closes #NN` or `Fixes #NN` (supported: `close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved`).
  - **Standalone lines required:** Each issue must have its own keyword on its own line:
    ```
    Closes #71
    Closes #72
    ```
  - **Anti-pattern:** Never comma-separate or combine (`Closes #71, #72` or `Closes #71 and #72`) — GitHub parser only recognizes the token immediately following keyword.
  - In PR descriptions, place closing directives at the bottom. Carries into squash message and auto-closes linked issues on merge.
- **Provenance — squash loses ancestry, add `Co-authored-by: Name <email>`:**
  - AI: one trailer per model — `Co-authored-by: <model> <noreply@ai>`
  - Fork/contributor: squash must include `Co-authored-by: Original Author <email>` + `Refs: GH#<id>` / `Closes #<id>`

## 6. Safeguards

> [!warning] NEVER merge / tag / publish without approval — leave PR `OPEN` → `a:merge b:tag/release c:publish d:hold` confirm. `gh-router` pr-land is the curated landing flow — open and merge PRs only when the user asks, never proactively.
