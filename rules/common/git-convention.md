# Git Convention — daily default

`dev worktree → task sub-worktree → squash to dev → curated [Unreleased] → PR → squash or merge commit to main` — never auto-merge.

## 1. Branch

- Use `dev` or `dev/<milestone>` for integration and staging.
- Use `feat|fix|doc/<slug>` for task branches.
- Never commit directly on `main`.

## 2. Repo identity

- Multi-remote trap: bare `gh` commands resolve to upstream, not your push target.
- Truth order: `branch.<ref>.pushRemote` → `branch.<ref>.remote` → `origin`.
- Always pass `--repo <owner/repo>` to `gh` commands.
- Confirm resolved slug against `git remote -v` before mutating calls.

## 3. Worktree & Hierarchy

- Use `dev` worktree as the integration anchor.
- Branch task sub-worktrees off `dev`: `wt switch --create <task> --base dev --no-cd`.
- Squash-merge task worktrees into `dev`: `wt merge --squash`.
- Always use `wt` commands (`wt switch`, `wt merge`).
- Never use raw `git worktree` or raw `git merge`. Raw commands bypass `.config/wt.toml` hooks.
- Land `dev` to `main` via PR using squash merge or merge commit.

## 4. Gate

- `.config/wt.toml [pre-merge]` executes on every `wt merge`.
- Merge only when green.

## 5. Commits & Changelog Ledger

- Format issue closing on standalone lines (`Closes #NN`). Never comma-separate multiple issue keys.
- Preserve `Co-authored-by: Name <email>` trailers for human and AI contributors across squashes.
- PR lifecycle, changelog ledger curation under `## [Unreleased]`, and waivers belong to `skills/gh-router`.

## 6. Safeguards

> [!warning]
> NEVER merge, tag, or publish without explicit approval. Leave PR open until user confirms (`a:merge b:tag/release c:publish d:hold`). Never open or merge PRs proactively. Use `skills/gh-router` for landing workflows.
