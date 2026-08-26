---
name: worktrunk-guide
description: >-
  Git worktree lifecycle reference for branch-addressed worktrees with hooks, templates, and LLM commits. Use when managing parallel worktrees, configuring worktrunk, or debugging shell integration. TRIGGER: worktrunk, wt, git worktree, hash_port
argument-hint: |-
  [topic]
---

# Worktrunk Guide

> **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk> — `wt` CLI

CLI for parallel git worktrees. Worktrees are **branch-addressed** (not path-addressed); **hooks** automate setup; `hash_port` gives deterministic ports per branch.

> **Prerequisite:** `wt switch` needs shell integration to `cd`. One-time setup: `wt config shell install` — details, worktree paths, env overrides and approvals live in [config](references/config.md).

## Quick Start

```bash
wt config shell install           # one-time, see above for env details
wt switch --create feature-auth   # create branch + worktree, then switch
wt list                           # status overview
wt merge                          # squash → rebase → merge to default → cleanup
```

## Core concepts

- **branch-addressed** — `wt switch <branch>` computes the directory from a template; never `cd` by path.
- **hook** — ten lifecycle hooks (`pre-` blocking, `post-` background) automate deps, servers, tests, cleanup.
- **hash_port** — `{{ branch | hash_port }}` → stable 10000–19999 port per branch for isolated dev servers/DBs.

## Using `wt` in practice

### 1. Create and switch

```bash
wt switch feature-auth                         # switch to existing
wt switch --create new-feature                 # create + switch
wt switch --create hotfix --base production    # from specific base
wt switch pr:123                               # GitHub PR #123
wt switch -                                    # previous worktree (like cd -)
wt switch ^                                    # default branch (main/master)
wt switch --create fix -x claude -- 'Fix bug #42'  # create + launch agent
```

Shortcuts (`^` `@` `-` `pr:{N}` `mr:{N}`) also work with `--base`. Full table in [In-file reference](#in-file-reference--the-80-surface) below.

**Done when:** `pwd` is the new worktree and `wt list` shows it as current.

### 2. Inspect — `wt list`

```bash
wt list                                        # human table (progressive)
wt list --full                                 # + CI, diff stats, LLM summaries
wt list --format=json | jq '.[] | select(.is_current)'
wt list --format=json | jq '.[] | select(.main_state=="integrated") | .branch'  # safe to prune
```

Use `--format=json` in scripts and agents. Columns, status symbols and JSON fields: [basics](references/basics.md).

**Done when:** you can tell ahead/behind, staged/modified, and which branches are safe to delete.

### 3. Work — diff and commit

```bash
wt step diff                 # all changes since branching (what merge would include)
wt step diff -- --stat       # summary
wt step commit               # stage + LLM-generated message (see [integrations](references/integrations.md))
wt step commit --stage=tracked --dry-run
```

**Done when:** diff matches expected scope and commit message is generated or deterministic fallback.

### 4. Keep warm — avoid cold starts

```bash
wt step copy-ignored                    # copy caches/deps/env to current worktree
wt step copy-ignored --from main --dry-run
```

Add to project config to run automatically on each new worktree:

```toml
# .config/wt.toml
[post-start]
copy = "wt step copy-ignored"
```

Filter with `.worktreeinclude` and language notes: [operations](references/operations.md).

**Done when:** new worktree has `node_modules`/`target`/`.env` without reinstall.

### 5. Merge back — `wt merge`

Merges current → target (inverse of `git merge`), like GitHub "Merge PR" locally.

```bash
wt merge                 # to default branch: commit → squash → rebase → merge → cleanup
wt merge develop        # to specific target
wt merge --no-squash    # preserve history
wt merge --no-remove    # keep worktree after merge
```

Pipeline details and flags (including `-C <path>` / `--yes` / `--verbose`): [basics](references/basics.md). Step-level overrides (`wt step squash`/`rebase`): [operations](references/operations.md).

**Done when:** target branch contains the squashed commit and worktree is removed (unless `--no-remove`).

### 6. Cleanup — `wt remove` and `prune`

```bash
wt remove                        # current worktree (background)
wt remove feature-branch
wt remove feature --force        # has untracked files
wt remove experimental -D        # has unmerged commits
wt step prune --dry-run          # preview merged worktrees
wt step prune                    # remove all merged (honors --min-age=1h guard)
```

Branch cleanup checks (same commit → ancestor → empty diff → tree match → simulated merge → patch-id): [basics](references/basics.md).

**Done when:** `wt list` no longer shows the worktree and branch is deleted only if merged.

### 7. Automate per worktree — dev server recipe

```toml
# .config/wt.toml
[post-start]
server = "npm run dev -- --port {{ branch | hash_port }}"

[list]
url = "http://localhost:{{ branch | hash_port }}"

[pre-remove]
server = "lsof -ti :{{ branch | hash_port }} -sTCP:LISTEN | xargs kill 2>/dev/null || true"
```

`wt list` shows URL dimmed when not listening. `fix-auth` always maps to the same port. More recipes (DB per worktree, Caddy, tmux): [patterns](references/patterns.md). Template variables/filters/functions: [automation](references/automation.md).

**Done when:** each worktree serves on its own stable port and stops on `wt remove`.

## In-file reference — the 80% surface

### Shortcuts

| Shortcut | Meaning                          | Works with                         |
| -------- | -------------------------------- | ---------------------------------- |
| `^`      | Default branch (`main`/`master`) | `switch`, `--base`, `merge` target |
| `@`      | Current branch/worktree          | any branch arg                     |
| `-`      | Previous worktree (`cd -` style) | `switch`                           |
| `pr:{N}` | GitHub PR #N branch              | `switch`                           |
| `mr:{N}` | GitLab MR !N branch              | `switch`                           |

### Core commands

| Command              | Shape                                    | Key flags                                                                                                                |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `wt switch [BRANCH]` | Switch or create worktree                | `--create`, `--base <BASE>`, `--execute <CMD>`, `--no-cd`                                                                |
| `wt list`            | List worktrees + status                  | `--full`, `--branches`, `--format=json`                                                                                  |
| `wt remove [BRANCH]` | Remove worktree; delete branch if merged | `--force` (untracked), `-D` (unmerged), `--no-delete-branch`                                                             |
| `wt merge [TARGET]`  | Merge current → target, then cleanup     | `--no-squash`, `--no-remove`, `--no-ff`, `--stage`, `--no-commit`, `--no-rebase`, `--format`, plus global `-C`/`-y`/`-v` |

Full flag tables (including global `-C`/`--config-set`/`--yes`): [basics](references/basics.md).

> Global flags `-C <path>` / `--config-set <toml>` / `-y` apply to every `wt` command — use `-C <worktree-path>` in scripts instead of `cd`.

## Reference map — deeper detail lives in files

Environment-related setup (shell, paths, env vars, approvals, state) is deliberately not inlined here — it lives in referenced files:

| Need                                                                  | Leading word | Pointer                                    |
| --------------------------------------------------------------------- | ------------ | ------------------------------------------ |
| `switch` / `list` / `remove` / `merge` — full flags, columns, symbols | `switch`     | [basics](references/basics.md)             |
| shell integration, worktree path, env vars, approvals, state          | `config`     | [config](references/config.md)             |
| `commit` / `squash` / `copy-ignored` / `diff` / `prune` / `for-each`  | `step`       | [operations](references/operations.md)     |
| hooks, template variables/filters/functions, aliases, subcommands     | `hook`       | [automation](references/automation.md)     |
| LLM commits, Claude Code plugin, statusline                           | `llm`        | [integrations](references/integrations.md) |
| dev server, DB isolation, cold-start, recipes, FAQ                    | `pattern`    | [patterns](references/patterns.md)         |

Raw source (authoritative for flag-level detail): `$SKILL_DIR/worktrunk-guide-raw/`

- Prose pointer: `$SKILL_DIR/worktrunk-guide-raw/<file>.md` (cwd unknown)
- Markdown link: `[001-switch.md](worktrunk-guide-raw/001-switch.md)` from SKILL.md; `[../worktrunk-guide-raw/001-switch.md](../worktrunk-guide-raw/001-switch.md)` from `references/`
- If curated summary conflicts with observation, raw doc wins

## When writing code

1. Use absolute paths for worktree operations (cwd resets between shell calls).
2. Use `--format=json` for scripting and automation.
3. Use `pre-*` hooks for blocking checks; `post-*` run in background and log only.

**Done when:** worktree operation succeeds from any cwd, JSON parses, and hook blocking matches intent.

## When answering questions

1. Answer from the practical workflows and in-file reference above first.
2. For branch-specific detail, read `$SKILL_DIR/references/<module>.md` per the reference map.
3. For flag-level or edge-case behavior, read `$SKILL_DIR/worktrunk-guide-raw/<file>.md`.

**Done when:** every cited flag or behavior is traced to a curated reference or raw doc, not memory.

## Triggers

- `worktrunk`, `wt`, `git worktree`, `branch-addressed worktree`, `parallel development`
- `switch worktree`, `create worktree`, `list worktrees`, `remove worktree`, `merge` / `squash and merge`
- `hook`, `post-start`, `pre-merge`, `hash_port`, `copy-ignored`, `dev server per worktree`
- `llm commit`, `shell integration not working`, `cold start slow`, `stale worktree`
