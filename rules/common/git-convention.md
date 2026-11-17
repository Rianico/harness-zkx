# Git Convention — Daily Default

Follow the staged workflow. Branch a feature branch off `dev`. Branch task sub-worktrees off the feature branch. Squash task work into the feature branch, curate the changelog, and PR to `main`. Never auto-merge.

## 1. Branch

- Use `dev` or `dev/<milestone>` for integration and staging.
- Use `feat/<slug>` (or `fix/<slug>`, `doc/<slug>`) for the feature branch. The feature branch is the final branch pushed to git.
- Branch task sub-worktrees off the feature branch: `wt switch --create <task> --base feat/<slug> --no-cd`.
- Never commit directly on `main`.

## 2. Repo identity

- Avoid multi-remote traps: bare `gh` commands resolve to upstream instead of your push target.
- Determine repository identity in order: `branch.<ref>.pushRemote` → `branch.<ref>.remote` → `origin`.
- Always pass `--repo <owner/repo>` to `gh` commands.
- Before mutating calls, confirm the resolved slug against `git remote -v`.

## 3. Worktree & Hierarchy

- Use the `dev` worktree as the integration anchor.
- Branch task sub-worktrees off the feature branch (`wt switch --create <task> --base feat/<slug>`).
- Squash-merge task worktrees into the feature branch (`wt merge --squash`). The squash is intent-bounded: incidental bugs introduced and fixed during development fold into the feature's intent boundary, never into `dev` directly.
- Save micro-commits inside task worktrees as save points. The feature branch history stays clean because only the squash lands.
- No rigid line caps (~100 lines). Intent cohesion governs what a squash holds, not a line budget.
- Always use `wt` commands (`wt switch`, `wt merge`). Raw `git worktree` and `git merge` bypass `.config/wt.toml` hooks.
- Land the feature branch to `dev`, then `dev` to `main` via PR using squash merge or merge commit.

## 4. Gate

- The `.config/wt.toml [pre-merge]` hook runs on every `wt merge`.
- Merge only after all checks pass green.

## 5. Commits, Changelog Ledger & Squash Message

- Put each closing key on its own line (`Closes #NN`).
- Preserve `Co-authored-by: Name <email>` trailers for human and AI contributors across squashes.
- PR lifecycle, changelog ledger curation under `## [Unreleased]`, and waivers belong to `skills/gh-router`.
- Squash commit message template — lead with intent (`Why`), then invariants (`What`), never mechanics (`How`):

```text
<type>(<scope>): <summary>

### Why (Intent)

### What (Invariants)

### Things Intentionally Not Touched

Closes #NN
```

## 6. Safeguards

> [!warning]
> Open, merge, tag, or publish only with explicit approval. Leave PR open until user confirms (`a:merge b:tag/release c:publish d:hold`).
