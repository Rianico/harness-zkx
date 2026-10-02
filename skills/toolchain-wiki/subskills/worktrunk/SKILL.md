---
argument-hint: |-
  [topic]
description: >-
  Git worktree lifecycle CLI for branch-addressed parallel worktrees with hooks and templates. Use when switching, listing, removing, or merging worktrees, configuring hooks, or automating per-branch dev servers.
metadata:
  managed-by: toolchain-wiki
name: worktrunk
---

# Worktrunk

> **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk> — `wt` CLI

CLI for parallel git worktrees. Worktrees are **branch-addressed**, not path-addressed. **hooks** automate setup. `hash_port` gives deterministic ports per branch.

> Shell integration is required for `wt switch` to `cd`. Run `wt config shell install` once. Paths, env vars, and approvals: [config](references/config.md).

## Quick Start

```bash
wt config shell install           # one time; see above
wt switch --create feature-auth   # create branch and worktree, then switch
wt list                           # status overview
wt merge                          # commit → squash → rebase → merge → cleanup
```

## Core concepts

**branch-addressed** — `wt switch <branch>` computes the directory from a template. Never `cd` by path.

**hook** — ten lifecycle hooks (`pre-` blocking, `post-` background) automate deps, servers, tests, cleanup.

**hash_port** — `{{ branch | hash_port }}` gives stable port 10000–19999 per branch for isolated dev servers and DBs.

## Using `wt` in practice

### 1. Create and switch

```bash
wt switch feature-auth                         # switch to existing
wt switch --create new-feature                 # create and switch
wt switch --create hotfix --base production    # from base branch
wt switch pr:123                               # GitHub PR
wt switch -                                    # previous worktree
wt switch ^                                    # default branch
wt switch --create fix -x claude -- 'Fix bug #42'  # create and launch agent
```

Shortcuts `^` `@` `-` `pr:{N}` `mr:{N}` work with `--base`. Full table below.

### 2. Inspect

```bash
wt list                                        # human table
wt list --full                                 # add CI and summaries
wt list --format=json 2>/dev/null | jq '(.items // .) | .[] | select(.worktree.current // .is_current)'
wt list --format=json 2>/dev/null | jq '(.items // .) | .[] | select(.display.state == "integrated") | .branch'
```

Use `--format=json` in scripts. Columns, status symbols, JSON fields: [basics](references/basics.md).

### 3. Diff and commit

```bash
wt step diff                 # all changes since branching
wt step diff -- --stat       # summary
wt step commit               # stage and LLM-generated message
wt step commit --stage=tracked --dry-run
```

LLM setup: [integrations](references/integrations.md).

### 4. Keep warm

```bash
wt step copy-ignored                    # copy caches, deps, env to current
wt step copy-ignored --from main --dry-run
```

Add to project config to run on each new worktree:

```toml
# .config/wt.toml
[post-start]
copy = "wt step copy-ignored"
```

Filter with `.worktreeinclude`: [operations](references/operations.md).

### 5. Merge back

Merges current into target, like GitHub "Merge PR" locally.

```bash
wt merge                 # to default branch
wt merge develop
wt merge --no-squash     # preserve history
wt merge --no-remove     # keep worktree after merge
```

Pipeline: commit → squash → rebase → pre-merge hooks → fast-forward → cleanup. Step overrides: [operations](references/operations.md).

### 6. Cleanup

```bash
wt remove                        # current worktree
wt remove feature-branch
wt remove feature --force        # has untracked files
wt remove experimental -D        # has unmerged commits
wt step prune --dry-run          # preview
wt step prune                    # remove merged; honors --min-age
```

Branch cleanup checks (same commit → ancestor → empty diff → tree match → simulated merge → patch-id): [basics](references/basics.md).

### 7. Per-worktree dev server

```toml
# .config/wt.toml
[post-start]
server = "npm run dev -- --port {{ branch | hash_port }}"

[list]
url = "http://localhost:{{ branch | hash_port }}"

[pre-remove]
server = "lsof -ti :{{ branch | hash_port }} -sTCP:LISTEN | xargs kill 2>/dev/null || true"
```

Each worktree serves on its own stable port. Recipes: [patterns](references/patterns.md). Templates: [automation](references/automation.md).

## In-file reference

### Shortcuts

| Shortcut | Meaning                          | Works with                         |
| -------- | -------------------------------- | ---------------------------------- |
| `^`      | Default branch (`main`/`master`) | `switch`, `--base`, `merge` target |
| `@`      | Current branch                   | any branch arg                     |
| `-`      | Previous worktree                | `switch`                           |
| `pr:{N}` | GitHub PR branch                 | `switch`                           |
| `mr:{N}` | GitLab MR branch                 | `switch`                           |

### Core commands

| Command              | Shape                                    | Key flags                                                                                  |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------ |
| `wt switch [BRANCH]` | Switch or create worktree                | `--create`, `--base`, `--execute`, `--no-cd`                                               |
| `wt list`            | List worktrees and status                | `--full`, `--branches`, `--format=json`                                                    |
| `wt remove [BRANCH]` | Remove worktree; delete branch if merged | `--force`, `-D`, `--no-delete-branch`                                                      |
| `wt merge [TARGET]`  | Merge current → target, then cleanup     | `--no-squash`, `--no-remove`, `--no-ff`, `--stage`, plus `-C`/`-y`/`-v`                   |

Full flag tables: [basics](references/basics.md). Global flags `-C`, `--config-set`, `-y` apply to every `wt` command.

## Reference map

| Need                                                                  | Pointer                                    |
| --------------------------------------------------------------------- | ------------------------------------------ |
| `switch` / `list` / `remove` / `merge` — full flags, columns, symbols | [basics](references/basics.md)             |
| shell integration, worktree path, env vars, approvals, state          | [config](references/config.md)             |
| `commit` / `squash` / `copy-ignored` / `diff` / `prune` / `for-each`  | [operations](references/operations.md)     |
| hooks, template variables/filters, aliases, subcommands               | [automation](references/automation.md)     |
| LLM commits, Claude Code plugin, statusline                           | [integrations](references/integrations.md) |
| dev server, DB isolation, cold-start, recipes, FAQ                    | [patterns](references/patterns.md)         |

Raw source: `$SKILL_DIR/references/worktrunk-raw/`. If curated summary conflicts with observation, raw doc wins.

### Decision rules

| When you need to                                    | Do this                                         | Because                                             |
| --------------------------------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| create a branch with custom base                    | `wt switch --create feat --base release`        | `--base` sets the parent, not `git checkout -b`     |
| switch without shell integration                    | `wt switch --no-cd feat` and then `cd` manually | shell integration is required for auto-`cd`         |
| run a command after switch                          | `wt switch --create feat -x claude -- 'prompt'` | `--execute` replays `wt` with the command            |
| get structured output                               | `wt list --format=json 2>/dev/null`             | JSON is stable; stderr may contain schema notices   |
| squash and merge without LLM                        | `wt merge --no-commit` (pre-stage manually)     | skips auto-commit stage                             |
| skip all automation                                 | `--no-hooks` flag                               | blocks both pre- and post- hooks                    |
| approve in CI                                       | `--yes` flag                                    | skips interactive approval prompts                  |
| copy cached deps to new worktree                    | add `post-start` hook: `wt step copy-ignored`   | avoids cold installs on every new worktree          |

## Triggers

- `worktrunk`, `wt`, `git worktree`, `branch-addressed worktree`, `parallel development`
- `switch worktree`, `create worktree`, `list worktrees`, `remove worktree`, `merge` / `squash and merge`
- `hook`, `post-start`, `pre-merge`, `hash_port`, `copy-ignored`, `dev server per worktree`
- `llm commit`, `shell integration not working`, `cold start slow`, `stale worktree`