# Git Convention — daily default

Topic → branch → worktree (when helps) → pre-merge gate → squash fixups → conventional commit → PR (no auto-merge).

## 1. Branch

- Create `feat|fix|doc/<slug>` (`map/<slug>` for integrations). Never on default branch.

## 2. Worktree isolation

- Use `wt` siblings when it helps — daily parallel work or protecting base. Target stays in place: `git switch -c feat/<slug> <base>` (same cwd); children isolated: `wt switch --create <child> --base <parent> --no-cd`. Project truth is `.config/wt.toml` — don't restate hooks in prose.

## 3. Pre-merge gate

- `.config/wt.toml [pre-merge]` runs before every `wt merge` — verification / linter / LSP. Merge only when green. Prefer `wt switch` / `wt merge` / `wt list --format=json` over raw `git worktree` / `git merge` (raw bypasses hooks and `copy-ignored`).

## 4. Commits

- **Squash trivial on merge:** fixup/typo churn may stay scattered while iterating; squash to one clean history when merging to base so target stays reviewable. Inside the topic branch keep commits atomic if it helps bisect; outside the merge — single squash. Docs vs code in separate commits.
- **Conventional commits (Conventional Commits 1.0.0 + semantic):** `type[(scope)][!]: description` — blank line — body — blank line — footer(s). `feat`=MINOR, `fix`=PATCH, `!` or `BREAKING CHANGE:`=MAJOR; others `docs|style|refactor|perf|test|build|ci|chore|revert` have no bump unless breaking. Scope `(<noun>)`; description imperative present, lowercase, no period, ≤72 (50 ideal). Body free-form — explain what/why not how, paragraphs separated by blank lines. Footer `Token: value` or `Token #value` (`-` for spaces, e.g. `Acked-by`); `BREAKING CHANGE` uppercase (alias `BREAKING-CHANGE`); types case-insensitive except it. e.g. `feat(auth): add worktree pre-merge gate` ; `fix(api)!: drop legacy field` + body `Migrate callers to v2.` + footers `BREAKING CHANGE: removes field x` / `Closes #12` / `Co-authored-by:` ; `revert: let us never…` + `Refs: 676104e`.
- **Provenance trailers — squash loses ancestry:** add `Co-authored-by: Name <email>` footer(s) so history survives the squash. AI-assisted → `Co-authored-by: <AI model name> <noreply@ai>` (e.g. `Muse Spark 1.2`, `opencode-go/gpt-5.6-luna`) — one trailer per model that wrote code. Fork refinement → when you `git fetch origin pull/<id>/head && git merge --no-ff FETCH_HEAD` into a new `fix/<slug>` branch, modify, and open a clean PR, the squash commit MUST include `Co-authored-by: Original Author <original@email>` and `Refs: GH#<folkPR>` / `Closes #<folkPR>` — don't let the folk's commits disappear behind your squash.

## 5. Safeguards

> [!warning] NEVER merge, tag, or publish without approval — leave PR `OPEN` → `a:merge b:tag/release c:publish d:hold` confirm.

Full fan-out / Wayfinder maps / parallel worktrees → `branch-worktree-pr` skill. Hook/port/template mechanics → `worktrunk-guide` / `.config/wt.toml` template.

## 6. Changelog — Keep-a-Changelog (reference)

- `# Changelog` + one-line intro.
- `## [Unreleased]` at top (accumulation point); `## [X.Y.Z] - YYYY-MM-DD` newest first.
- Subsections `### Added / Changed / Fixed / Removed`; one change per bullet, imperative, no padding.
- Link issues/PRs inline where they exist: `([owner/repo#N](...))` at bullet end; cross-repo explicit markdown, same-repo `#N` auto-links. No issue → linkless.
- Dates/versions from release commit, not PR date.

## 7. Docs & Locale (reference)

**README — brooks-lint layout:** centered image-led example-driven. Facts > marketing; numbers match reproducible output at commit. Header block (logo → centered `h1` → tagline → language switcher → nav `•` anchors → shields row → banner) → pull-quote + narrative → "Why you need this" (3 para) → example Quick Start (read→act→result, no screenshots) → reproducible benchmark (criterion table + numbers + exact command + `> **Scope & honesty.**` blockquote) → tools table, structure tree, roadmap `<details>`, contributing, license, lineage, star chart, CTA. Static version badge must bump every version.

**Locale:** default English `README.md`. Reciprocal language links at top of every locale file. Structure mirrors exactly; code/JSON/Mermaid/code columns stay byte-identical, prose only translated. Keep locales in sync — stale number = bug.
