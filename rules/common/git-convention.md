# Git Convention — Daily Default

Follow the staged workflow. Branch a task sub-worktree from `dev`. Squash into `dev`, curate the changelog, and PR to `main`. Never auto-merge.

## 1. Branch

- Use `dev` or `dev/<milestone>` for integration and staging.
- Use `feat|fix|doc/<slug>` for task branches.
- Never commit directly on `main`.

## 2. Repo identity

- Avoid multi-remote traps: bare `gh` commands resolve to upstream instead of your push target.
- Determine repository identity in order: `branch.<ref>.pushRemote` → `branch.<ref>.remote` → `origin`.
- Always pass `--repo <owner/repo>` to `gh` commands.
- Before mutating calls, confirm the resolved slug against `git remote -v`.

## 3. Worktree & Hierarchy

- Use the `dev` worktree as the integration anchor.
- Branch task sub-worktrees off `dev`: `wt switch --create <task> --base dev --no-cd`.
- Squash-merge task worktrees into `dev`: `wt merge --squash`.
- Always use `wt` commands (`wt switch`, `wt merge`). Raw `git worktree` and `git merge` bypass `.config/wt.toml` hooks.
- Land `dev` to `main` via PR using squash merge or merge commit.

## 4. Gate

- The `.config/wt.toml [pre-merge]` hook runs on every `wt merge`.
- Merge only after all checks pass green.

## 5. Commits & Changelog Ledger

- Put each closing key on its own line (`Closes #NN`).
- Preserve `Co-authored-by: Name <email>` trailers for human and AI contributors across squashes.
- PR lifecycle, changelog ledger curation under `## [Unreleased]`, and waivers belong to `skills/gh-router`.

## 6. Safeguards

> [!warning]
> Open, merge, tag, or publish only with explicit approval. Leave PR open until user confirms (`a:merge b:tag/release c:publish d:hold`).
