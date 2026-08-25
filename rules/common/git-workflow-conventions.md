# Git Workflow Conventions

Rules extracted from git history analysis to prevent common mistakes. Flow is `ticket/spec → branch+worktree → commit hygiene → PR → release`.

## 1 Branch + Worktree + PR — ==tight worktree== entry

Must not submit code on the default branch. Every change goes `ticket/spec → branch → isolated worktree → PR`.

- **Branch + worktree:** `feat|fix|doc/<ticket-slug>` or `map/<slug>` (integration, replaces `dev`) from ticket/spec. Prefer `wt` (worktrunk) over raw `git worktree` — `wt switch --create <branch> --base <parent>`, `wt list --format=json`, `wt merge <parent>` (`pre-merge` gate), `wt remove`, `wt step copy-ignored` + `{{ branch | hash_port }}` — preserves hooks/cold-start/port allocation. Raw `git worktree add`/`git merge` is fallback only.
- **Tracker is pluggable:** anchor is always the `ticket/spec` (`docs/agents/issue-tracker.md` — GitHub `gh` default, `.scratch/*.md` or Linear/Jira via freeform). GitHub binding is `Closes #NN` / `Part of #<map>` last line of PR body.
- **PR hygiene:** one intent per PR, `gh pr create --fill` with `Closes`/`Part of` + `Co-authored-by` when ticket author ≠ merger (squash loses ancestry — trailer is provenance).

> [!warning] NEVER without approval
> Never merge a PR (`gh pr merge` / `wt merge <main>`) or create/push a tag (`npm run release -- X.Y.Z` / `cargo publish`) without explicit user approval. Leave PR `OPEN` and present `a:merge b:tag/release c:publish d:hold` confirm dialog.

---

## 2 Commit Hygiene

### Atomic Commit Separation

Implementation changes and documentation updates must be separate commits. Task-orientation is always a good perspective to identify the boundary.

### Reset Safety Protocol

**Never use `git reset --hard`.** Always reset in soft mode and explicitly discard changes if needed.

**Rationale:** `git reset --hard` is a destructive operation that can silently lose uncommitted work. During session, `--hard` was used when soft reset would have preserved changes for re-commit.

**Pattern:**

```bash
# Step 1: Undo commit(s), keep all changes staged
git reset HEAD~N

# Step 2: Check and confirm if you really need to discard changes
git restore <file>           # Discard working directory changes
git restore --staged <file>  # Unstage only
git restore .                # Discard all changes in working directory
```

**Why two steps:**

- Soft reset is always safe — changes remain in working directory and has the chance for confirmation
- `git restore` is explicit about what you're discarding
- No accidental data loss from a single destructive command

**Forbidden:**

```bash
git reset --hard HEAD~N  # NEVER use
```

### Pre-Commit File Audit

Before committing, audit staged files for cross-cutting concerns.

**Audit checklist:**

1. Are there both code files and documentation files staged?
2. Does CLAUDE.md/Agents.md appear alongside skill/command changes?
3. Any files out of current task is added?

**If cross-cutting detected:**

```bash
# Split into separate commits
git reset HEAD  # Unstage all
git add <code-files> && git commit
git add <doc-files> && git commit
```

---

## 3 Release — Tag, Release, Publish

The release shape is language-agnostic — the examples below are per-ecosystem stand-ins (npm → TypeScript/JavaScript, cargo → Rust, uv/pip → Python). Use your project's native tooling.

### Release procedure — tag first, publish second

The loop is **develop → release → publish**. Never publish a version before its tag exists.

1. **Develop.** Commits land on the default branch; each user-visible change gets an entry under
   `## [Unreleased]` in CHANGELOG.md as it lands.
2. **Release** — one orchestrated command (e.g., `npm run release -- X.Y.Z`):
   - validate semver; require a **clean working tree**; refuse an existing `vX.Y.Z` tag and any
     non-increasing version;
   - bump the version in the manifest **and** the lockfile (both, or they diverge);
   - move CHANGELOG `## [Unreleased]` → `## [X.Y.Z] - <date>` (entries preserved), re-add an
     empty `## [Unreleased]` for the next cycle;
   - commit (`chore: release vX.Y.Z`), create an **annotated** tag `vX.Y.Z`, push branch + tag;
   - the tag push triggers a workflow that creates the GitHub release with the changelog section
     as the body (extract `## [X.Y.Z]` → next `## [`, fall back to generated notes if missing).
3. **Publish** to the registry, guarded: a pre-publish hook refuses to run unless the current
   version is tagged (e.g., an assert-tagged check wired into the publish path).
4. **Publish Body File**, when need to publish long content, write them to a file first rather
   than writing them in bash command.

Consequences: every published version is by construction tagged, released, and present in the
changelog; the registry can never get ahead of GitHub; a release page can never be an empty stub
(no more near-blank `--generate-notes` output for docs-only releases).

Ecosystem mapping (examples — replace with your stack): `npm publish` → TypeScript/JavaScript
(npm registry); `cargo publish` → Rust (crates.io); `uv publish`/twine → Python (PyPI); other
ecosystems map to their registry. The pre-publish gate → any hook the publish path runs
(`prepublishOnly`, `predeploy`, CI step). The shape is the standard; the tooling is a per-project
implementation.

### Changelog standard

Keep-a-Changelog, layout after pi-interactive-shell:

- `# Changelog` + a one-line intro ("All notable changes … will be documented in this file.").
- `## [Unreleased]` **at the top** — the accumulation point during development.
- `## [X.Y.Z] - YYYY-MM-DD`, **newest first**, date = the release date.
- Subsections `### Added / Changed / Fixed / Removed`; each bullet one change, imperative or
  descriptive, no prose padding.
- **Link related issues/PRs inline** where they exist: `([owner/repo#N](https://github.com/owner/repo/issues/N))`
  at the end of the bullet. Cross-repo links are explicit markdown; same-repo `#N` auto-links.
  Entries with no tracked issue stay linkless — never invent references. A header line documents
  the convention.
- Dates and versions are real: taken from the release commit, not the PR date.

---

## 4 Docs & Locale — release-adjacent reference

> [!note] Disclosure
> This section is reference, not daily gate. Loaded every turn but consulted only when cutting docs/release. Keep tight; deep examples live in project `README.md` / `docs/` — not here.

### README style — brooks-lint layout

Centered, image-led, example-driven. Facts over marketing; every number must match the
reproducible output at the current commit (a stale benchmark figure is a bug, not a rounding).

- **Header block**: logo → `<h1 align="center">` → one-line tagline → language-switcher row →
  nav row (`•`-separated anchors) → shields.io badge row (version, license, platform, package
  v/downloads, stars) → banner image. The static version badge **must be updated on every
  version bump** — it drifts silently otherwise.
- **Pull-quote + narrative**: a quote from the founding idea, then 1–2 paragraphs making the
  case. No claims without numbers or references.
- **Short "Why you need this" before Quick Start**: pain → fix → honest scope, 3 tight
  paragraphs, so users reach the demo immediately.
- **Example-driven Quick Start**: read → act → result code blocks; no screenshots required.
- **Reproducible benchmark section**: criterion table, then the deterministic numbers with the
  exact run command, then a `> **Scope & honesty.**` blockquote stating what the numbers do and
  don't measure. Numbers come from the committed script, not from memory.
- Then: tools table, project structure tree, roadmap (`<details>`), contributing, license,
  acknowledgments/lineage, star-history chart, closing centered CTA.

### Locale

- Default : English (`README.md`).
- **Reciprocal language links** at the top of every locale file.
- Structure mirrors exactly between locales. Code, JSON, Mermaid diagrams, and the code columns
  of tables stay **byte-identical**; only prose is translated.
- Keep all locales in sync on every README change — a stale number in one locale is a bug equal
  to a stale number in the default.
