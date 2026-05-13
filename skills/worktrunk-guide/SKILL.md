---
name: worktrunk-guide
description: |
  CLI for git worktree management with parallel development, hooks, and LLM integration. TRIGGER when: switching worktrees, creating isolated branches, managing parallel development, setting up dev servers per worktree, configuring hooks, generating LLM commit messages, eliminating cold starts, agent handoff workflows.
argument-hint: "[topic]"
---

# Worktrunk Guide

> **Version:** v0.49.0 | **Last Updated:** 2026-05-12
>
> Check for updates: https://github.com/max-sixty/worktrunk

CLI for git worktree management with parallel development, hooks, and LLM integration.

## Quick Start

```bash
# Install shell integration (required for directory switching)
wt config shell install

# Create and switch to new worktree
wt switch --create feature-auth

# List all worktrees with status
wt list

# Merge to default branch and cleanup
wt merge
```

## Core Concepts

1. **Worktrees as branches** - Address worktrees by branch name, not path
2. **Hooks for automation** - Run commands at lifecycle events (switch, merge, remove)
3. **LLM integration** - Generate commit messages with Claude, Codex, or other tools
4. **Parallel development** - Each worktree has independent files, index, and dev server

## Essential Patterns

### Navigation

```bash
wt switch feature-auth           # Switch to existing worktree
wt switch --create new-feature   # Create new branch and worktree
wt switch -                      # Previous worktree (like cd -)
wt switch ^                      # Default branch (main/master)
wt switch pr:123                 # GitHub PR #123's branch
```

### Shortcuts

| Shortcut | Meaning |
|----------|---------|
| `^` | Default branch |
| `@` | Current branch/worktree |
| `-` | Previous worktree |
| `pr:{N}` | GitHub PR #N |
| `mr:{N}` | GitLab MR !N |

### Status Overview

```bash
wt list                    # Worktrees with status, divergence, CI
wt list --full             # Add CI status, line diffs, LLM summaries
wt list --branches         # Include branches without worktrees
wt list --format=json      # JSON output for scripting
```

### Merge Workflow

```bash
wt merge                   # Squash, rebase, merge to default, cleanup
wt merge --no-squash       # Preserve commit history
wt merge --no-remove       # Keep worktree after merge
wt merge develop           # Merge to specific branch
```

### Hooks Setup

```toml
# .config/wt.toml
[post-start]
dev = "npm run dev -- --port {{ branch | hash_port }}"
copy = "wt step copy-ignored"

[pre-merge]
test = "npm test"
```

### Dev Server Per Worktree

```toml
# .config/wt.toml
[post-start]
server = "npm run dev -- --port {{ branch | hash_port }}"

[list]
url = "http://localhost:{{ branch | hash_port }}"

[pre-remove]
cleanup = "lsof -ti :{{ branch | hash_port }} | xargs kill 2>/dev/null || true"
```

### Cold Start Elimination

```toml
# .config/wt.toml
[post-start]
copy = "wt step copy-ignored"
```

Copies gitignored files (node_modules, target, .cache) between worktrees.

### LLM Commit Messages

```toml
# ~/.config/worktrunk/config.toml
[commit.generation]
command = "claude -p --no-session-persistence --model=haiku --tools=''"
```

## API Reference

### Core Commands

| Command | Description | Key Flags |
|---------|-------------|-----------|
| `wt switch [BRANCH]` | Switch to worktree; create if needed | `--create`, `--base`, `--execute` |
| `wt list` | List worktrees with status | `--full`, `--branches`, `--format=json` |
| `wt remove [BRANCH]` | Remove worktree; delete branch if merged | `--force`, `-D`, `--no-delete-branch` |
| `wt merge [TARGET]` | Merge to target, cleanup worktree | `--no-squash`, `--no-remove`, `--no-ff` |

### Config Commands

| Command | Description |
|---------|-------------|
| `wt config shell install` | Install shell integration |
| `wt config create` | Create user config file |
| `wt config create --project` | Create project config |
| `wt config show` | Show configuration and locations |
| `wt config state default-branch` | Get/set default branch |

### Step Operations

| Command | Description |
|---------|-------------|
| `wt step commit` | Commit with LLM-generated message |
| `wt step squash` | Squash commits with LLM message |
| `wt step copy-ignored` | Copy gitignored files between worktrees |
| `wt step diff` | Show all changes since branching |
| `wt step prune` | Remove merged worktrees |
| `wt step for-each -- CMD` | Run command in every worktree |

### Hook Types

| Hook | When | Blocking |
|------|------|----------|
| `pre-switch` | Before worktree creation/switch | Yes |
| `post-switch` | After switch (all cases) | No |
| `pre-start` | New worktree creation, before `--execute` | Yes |
| `post-start` | New worktree, background tasks | No |
| `pre-merge` | After rebase, before merge | Yes |
| `post-merge` | After successful merge | No |
| `pre-remove` | Before worktree deletion | Yes |
| `post-remove` | After worktree removed | No |

### Template Variables

| Variable | Description |
|----------|-------------|
| `{{ branch }}` | Branch name |
| `{{ worktree_path }}` | Worktree directory path |
| `{{ default_branch }}` | Default branch (main/master) |
| `{{ repo }}` | Repository directory name |
| `{{ target }}` | Merge target branch |
| `{{ vars.key }}` | Per-branch custom variables |

### Template Filters

| Filter | Example | Description |
|--------|---------|-------------|
| `sanitize` | `{{ branch \| sanitize }}` | Replace `/` with `-` |
| `hash_port` | `{{ branch \| hash_port }}` | Port 10000-19999 from hash |
| `sanitize_db` | `{{ branch \| sanitize_db }}` | Database-safe identifier |
| `codename(n)` | `{{ branch \| codename(2) }}` | Friendly name (adjective-noun) |

## References

| Module | File | Source | Topics |
|--------|------|--------|--------|
| basics | `$SKILL_DIR/references/basics.md` | `worktrunk-guide-raw/001-switch.md`, `002-list.md`, `003-remove.md`, `004-merge.md` | switch, list, remove, merge, shortcuts |
| config | `$SKILL_DIR/references/config.md` | `worktrunk-guide-raw/005-config.md` | user config, project config, shell integration, state management |
| operations | `$SKILL_DIR/references/operations.md` | `worktrunk-guide-raw/006-step.md` | commit, squash, copy-ignored, diff, prune, for-each |
| automation | `$SKILL_DIR/references/automation.md` | `worktrunk-guide-raw/007-hook.md`, `008-extending.md` | hooks, aliases, custom subcommands |
| integrations | `$SKILL_DIR/references/integrations.md` | `worktrunk-guide-raw/009-llm-commits.md`, `010-claude-code.md` | LLM commits, Claude Code plugin |
| patterns | `$SKILL_DIR/references/patterns.md` | `worktrunk-guide-raw/011-tips-patterns.md`, `012-faq.md` | dev server per worktree, database isolation, agent handoffs, FAQ |

## When to Use Raw Docs

Read `$SKILL_DIR/references/worktrunk-guide-raw/` when:
- Curated references lack the exact flag, option, or behavior you need
- You need the complete API surface for an uncommon command variant
- The curated summary conflicts with your observation — raw docs are authoritative

## Path Convention

- **Prose references** use `$SKILL_DIR/references/...` — cwd is unknown to the reader
- **Markdown links** use relative paths like `[text](worktrunk-guide-raw/file.md)` — standard relative-to-file convention

## When Writing Code

1. Use absolute paths for worktree operations (cwd resets between shell calls)
2. Shell integration required for `wt switch` to change directory
3. Use `--format=json` for scripting and automation
4. Hooks run in background by default - use `pre-*` for blocking behavior

## When Answering Questions

1. Answer from patterns and tables above first
2. If the question involves deeper details, read `$SKILL_DIR/references/<module>.md`
3. For edge cases, read `$SKILL_DIR/references/worktrunk-guide-raw/`
4. If still insufficient, inform user and answer from built-in knowledge

## Triggers

### Domain Terms
- worktrunk, wt, git worktree, branch management, parallel development, agent worktree

### Task Phrases
- switch worktree, create worktree, list worktrees, remove worktree, merge worktree branch
- set up hooks, dev server per worktree, configure worktrunk, shell integration
- llm commit messages, copy ignored files, squash and rebase

### Problem Keywords
- worktree not found, merge conflicts, shell integration not working
- branch already exists, port conflicts, cold start slow, stale worktree
