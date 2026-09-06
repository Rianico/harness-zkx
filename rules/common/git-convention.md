# Git Convention — daily default

`topic → branch → worktree → gate → squash → PR` — never auto-merge.

## 1. Branch

- `feat|fix|doc/<slug>`; `map/<slug>` for integration. Never commit on `main`.

## 2. Worktree

- **When:** daily work — optional, when it helps (parallel / protect base). Orchestrated via `branch-worktree-pr` — mandatory: one write ticket = one worktree.
- **Target in place:** `git switch -c feat/<slug> <base>` — stays in same cwd.
- **Children isolated:** `wt switch --create <child> --base <parent> --no-cd` — sibling dir.
- **Use `wt`:** `wt switch` / `wt merge` / `wt list --format=json`. Raw `git worktree` / `git merge` bypasses hooks, `copy-ignored`, and port allocation.
- **Truth:** `.config/wt.toml` — don't restate hooks in prose.

## 3. Gate

- `.config/wt.toml [pre-merge]` runs on every `wt merge`. Merge only when green.

## 4. Commits

- **Atomic inside, squash outside:** atomic bisectable commits inside topic; squash fixup/typo churn on merge to base. `code` and `docs` MUST be separate commits — never mix code + docs in one commit, even in same PR.
- **Conventional (Conventional Commits 1.0.0 + semver):** `type[(scope)][!]: description`
  - Blank line → body (what/why) → blank line → footer(s).
  - `feat` = MINOR, `fix` = PATCH, `!` / `BREAKING CHANGE:` = MAJOR; other types (`docs|style|refactor|perf|test|build|ci|chore|revert`) no bump unless breaking.
  - Scope `(<noun>)`; description imperative, lowercase, no period, ≤72 (50 ideal).
  - Footer `Token: value` or `Token #value`; `BREAKING CHANGE` uppercase (alias `BREAKING-CHANGE`).
  - Ex: `feat(auth): add worktree pre-merge gate` · `fix(api)!: drop legacy field` + `BREAKING CHANGE: removes field x` / `Closes #12`
- **Provenance — squash loses ancestry, add `Co-authored-by: Name <email>`:**
  - AI: one trailer per model — `Co-authored-by: <model> <noreply@ai>`
  - Fork: `git fetch origin pull/<id>/head && git merge --no-ff FETCH_HEAD` → squash must include `Co-authored-by: Original Author <email>` + `Refs: GH#<id>` / `Closes #<id>`

## 5. Safeguards

> [!warning] NEVER merge / tag / publish without approval — leave PR `OPEN` → `a:merge b:tag/release c:publish d:hold` confirm.

## 6. Reference

- **Fan-out / hooks:** parallel & Wayfinder → `branch-worktree-pr` skill; ports/hooks/templates → `worktrunk-guide` + `.config/wt.toml`.
- **Changelog (Keep-a-Changelog):** `# Changelog` → `## [Unreleased]` (top) → `## [X.Y.Z] - YYYY-MM-DD` newest first. Subsections `### Added | Changed | Fixed | Removed`, one imperative bullet each. Link `(owner/repo#N)` or `#N` when exists; no issue → linkless. Dates from release commit.
- **README (brooks-lint):** header (logo → h1 → tagline → lang switcher → `•` nav → shields → banner) → quote + narrative → Why (3 para) → Quick Start (read→act→result) → benchmark (table + command + `> **Scope & honesty.**`) → tools / tree / roadmap `<details>` / contributing / license. Bump version badge each release.
- **Locale:** `README.md` is English source; translations mirror structure exactly, code/JSON/Mermaid identical, reciprocal links at top. Keep in sync — stale number is bug.
