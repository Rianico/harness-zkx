---
name: checkpoint
description: Manage workflow checkpoints for milestone tracking and state comparison. Use when creating named savepoints, comparing current state against saved checkpoints, or tracking progress through multi-phase work. TRIGGER when: user mentions "checkpoint", "savepoint", "milestone", "before/after comparison", "track progress", or asks to save/restore state during refactors or feature work.
argument-hint: "[create|diff|list|clear] <name>"
---

# Checkpoint Skill

Manage workflow checkpoints for tracking progress across tasks and sessions. Checkpoints are project-level artifacts shared across all work.

## Purpose

Create named savepoints at key moments, then diff current state against them to understand what changed. Checkpoints persist across sessions and are shared across tasks, enabling long-running workflow tracking.

## Execution Contract

```
/checkpoint create <name>  - Save current state as named checkpoint
/checkpoint diff <name>    - Show changes since checkpoint
/checkpoint list           - Show all checkpoints with status
/checkpoint clear          - Remove old checkpoints (keeps last 10)
```

## Artifact Storage

Checkpoints are stored in `.lsz/checkpoints/` at the project root:

```
.lsz/
└── checkpoints/
    ├── {name1}.json
    ├── {name2}.json
    └── registry.json       # Optional: metadata index
```

Each checkpoint is a standalone JSON file, enabling easy inspection, diffing, and cleanup.

## Workflow Phases

### Create Checkpoint

1. Ensure checkpoint directory exists:
   ```bash
   mkdir -p .lsz/checkpoints
   ```
2. Capture current state:
   ```bash
   git rev-parse HEAD
   git status --porcelain
   git branch --show-current
   ```
3. Write checkpoint file to `.lsz/checkpoints/{name}.json`:
   ```json
   {
     "name": "<name>",
     "created_at": "<ISO8601 timestamp>",
     "git_sha": "<full SHA>",
     "git_sha_short": "<short SHA>",
     "branch": "<current branch>",
     "dirty": <true|false>,
     "untracked": ["<file paths>"],
     "modified": ["<file paths>"]
   }
   ```
4. Report: name, timestamp, git SHA, dirty state

### Diff Checkpoint

1. Read checkpoint file from `.lsz/checkpoints/{name}.json`
2. Compare current HEAD against checkpoint SHA:
   ```bash
   git log --oneline <checkpoint_sha>..HEAD
   git diff --stat <checkpoint_sha> HEAD
   git status --porcelain
   ```
3. Report structured diff (commits, files changed, uncommitted changes)

### List Checkpoints

1. List all `*.json` files in `.lsz/checkpoints/`
2. For each checkpoint, compute status:
   - `current`: HEAD matches checkpoint SHA
   - `behind X commits`: checkpoint SHA is ahead of HEAD
   - `ahead X commits`: HEAD is ahead of checkpoint SHA
3. Output formatted table

### Clear Checkpoints

1. List all checkpoint files sorted by creation timestamp
2. Keep last 10, delete older ones
3. Report deleted checkpoints

## Output Formats

### Create Output
```
CHECKPOINT CREATED: <name>
=================================
Timestamp: <ISO8601>
Git SHA:   <sha>
Branch:    <branch>
State:     clean | dirty (X uncommitted)
```

### Diff Output
```
CHECKPOINT DIFF: <name>
=============================
Commits:    +X (<from_sha> → <to_sha>)
Files:      X changed
Insertions: +X
Deletions:  -X

Changed files:
  path/to/file1
  path/to/file2

Commit(s):
  <sha> <message>

Uncommitted:
  M path/to/modified
  ?? path/to/untracked
```

### List Output
```
CHECKPOINTS
===================================
Name          | Created           | SHA     | Status
--------------|-------------------|---------|--------
<name1>       | <ISO8601>         | <sha>   | behind (X commits)
<name2>       | <ISO8601>         | <sha>   | current
```

## Gotchas

- Checkpoints reference git SHAs; rebasing or force-pushing invalidates them
- Checkpoint files are local-only (in `.lsz/checkpoints/`)
- Creating a checkpoint on dirty state records dirty files but references HEAD SHA
- Checkpoints persist across sessions - use meaningful names to avoid confusion

## Example Workflow

```
[Start] --> /checkpoint create "feature-start"
   |
[Implement] --> /checkpoint create "core-done"
   |
[Test] --> /checkpoint diff "core-done"
   |
[Refactor] --> /checkpoint create "refactor-done"
   |
[PR] --> /checkpoint diff "feature-start"
```
