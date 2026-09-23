# Git Convention — daily default

`topic → branch → worktree → gate → squash → PR` — never auto-merge.

## 1. Branch

- `feat|fix|doc/<slug>`; `map/<slug>` for integration. Never commit on `main`.

## 2. Repo identity

- **Inference lies.** In a multi-remote checkout (fork + upstream, two projects), `gh repo view` and every `gh` command without `--repo` may resolve to the *upstream*, not the remote you push to. `origin` is not proof of the push target — `branch.<ref>.pushRemote` is.
- **Truth, in order:** `branch.<ref>.pushRemote` → `branch.<ref>.remote` → `origin`, then `git remote get-url --push <remote>` → `owner/name`.
- **Pin it:** `--repo owner/name` on `gh run|pr|issue|release`, `gh api repos/owner/name/...`. `gh repo view` is a last-resort fallback only when no remote parses.
- **Pre-flight:** before a repo-mutating call (dispatch, release, run lookup, PR/issue write), print the resolved slug and confirm it against `git remote -v`.
- **Class fix:** when a slug/identity bug lands in one script, `rg -n 'gh repo view'` the toolchain before closing — same trap, different call site.

## 3. Worktree

- **When:** daily work — optional, when it helps (parallel / protect base). Orchestrated via `branch-worktree-pr` — mandatory: one write ticket = one worktree.
- **Target in place:** `git switch -c feat/<slug> <base>` — stays in same cwd.
- **Children isolated:** `wt switch --create <child> --base <parent> --no-cd` — sibling dir.
- **Use `wt`:** `wt switch` / `wt merge` / `wt list --format=json`. Raw `git worktree` / `git merge` bypasses hooks, `copy-ignored`, and port allocation.
- **Truth:** `.config/wt.toml` — don't restate hooks in prose.

## 4. Gate

- `.config/wt.toml [pre-merge]` runs on every `wt merge`. Merge only when green.

## 5. Commits

- **Atomic inside, declared landing outside:** atomic bisectable commits inside the topic. Landing is declared per PR in the PR body (`Landing: squash|merge`) before the changelog digest is curated: **squash** when the PR's commits are one change plus its docs and follow-up fixes, **merge** when it carries several changes. `pr-land` reads the declaration and selects the merge method; a squash destroys the subjects a multi-entry digest rests on, so the digest must be written to match what was declared (ADR-0016). `code` and `docs` MUST be separate commits — never mix code + docs in one commit, even in same PR.
- **Conventional (Conventional Commits 1.0.0 + semver):** `type[(scope)][!]: description`
  - Blank line → body (what/why) → blank line → footer(s).
  - `feat` = MINOR, `fix` = PATCH, `!` / `BREAKING CHANGE:` = MAJOR; other types (`docs|style|refactor|perf|test|build|ci|chore|revert`) no bump unless breaking.
  - Scope `(<noun>)`; description imperative, lowercase, no period, ≤72 (50 ideal).
  - Footer `Token: value` or `Token #value`; `BREAKING CHANGE` uppercase (alias `BREAKING-CHANGE`).
  - Ex: `feat(auth): add worktree pre-merge gate` · `fix(api)!: drop legacy field` + `BREAKING CHANGE: removes field x` / `Closes #12`
- **Provenance — a squash loses ancestry, add `Co-authored-by: Name <email>`:**
  - Applies to squash landing only; a merge commit preserves the authors' own commits, so no trailer is needed.
  - AI: one trailer per model — `Co-authored-by: <model> <noreply@ai>`
  - Fork: `git fetch origin pull/<id>/head && git merge --no-ff FETCH_HEAD` → squash must include `Co-authored-by: Original Author <email>` + `Refs: GH#<id>` / `Closes #<id>`

## 6. Safeguards

> [!warning] NEVER merge / tag / publish without approval — leave PR `OPEN` → `a:merge b:tag/release c:publish d:hold` confirm.

## 7. Reference

- **Fan-out / hooks:** parallel & Wayfinder → `branch-worktree-pr` skill; ports/hooks/templates → `worktrunk-guide` + `.config/wt.toml`.
- **Changelog (Keep-a-Changelog):** `# Changelog` → `## [Unreleased]` (top) → `## [X.Y.Z] - YYYY-MM-DD` newest first. Subsections `### Added | Changed | Fixed | Removed`, one imperative bullet each. Link `(owner/repo#N)` or `#N` when exists; no issue → linkless. Dates from release commit. Native toolchain priority: if the repo ships a changelog management script (e.g. `scripts/changelog-unreleased.py`), run it rather than hand-crafting markdown. Respect hidden-type rules (`style|chore|refactor|test|build|ci` do not receive section headers unless `!` or `BREAKING CHANGE`).
- **README (brooks-lint):** header (logo → h1 → tagline → lang switcher → `•` nav → shields → banner) → quote + narrative → Why (3 para) → Quick Start (read→act→result) → benchmark (table + command + `> **Scope & honesty.**`) → tools / tree / roadmap `<details>` / contributing / license. Bump version badge each release.
- **Locale:** `README.md` is English source; translations mirror structure exactly, code/JSON/Mermaid identical, reciprocal links at top. Keep in sync — stale number is bug.
