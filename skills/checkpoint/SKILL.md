---
name: checkpoint
description: Manage workflow checkpoints for milestone tracking and state comparison. Use when creating named savepoints, comparing current state against saved checkpoints, or tracking progress through multi-phase work. TRIGGER when: user mentions "checkpoint", "savepoint", "milestone", "before/after comparison", "track progress", or asks to save/restore state during refactors or feature work.
argument-hint: "[create|diff|list|clear] <name>"
---

# Checkpoint Skill

Manage workflow checkpoints for tracking progress through multi-phase work.

## Purpose

Create named savepoints at key moments, then diff current state against them to understand what changed. Useful for refactors, feature development, and any work where you want to measure progress.

## Execution Contract

```
/checkpoint create <name>  - Save current state as named checkpoint
/checkpoint diff <name>    - Show changes since checkpoint
/checkpoint list           - Show all checkpoints with status
/checkpoint clear          - Remove old checkpoints (keeps last 5)
```

## Workflow Phases

### Create Checkpoint

1. Run `/verify quick` to ensure current state is clean
2. Commit or stash any pending changes
3. Log checkpoint to `.claude/checkpoints.log`:
   ```bash
   echo "$(date +%Y-%m-%d-%H:%M) | $NAME | $(git rev-parse --short HEAD)" >> .claude/checkpoints.log
   ```
4. Report: name, timestamp, git SHA

### Diff Checkpoint

1. Read checkpoint entry from log
2. Diff current HEAD against checkpoint SHA:
   - Commits added since checkpoint
   - Files changed with stats
   - Any uncommitted changes
3. Report in structured format

### List Checkpoints

Show all checkpoints with:
- Name
- Timestamp
- Git SHA
- Status (current, behind X commits, ahead X commits)

### Clear Checkpoints

Remove old entries, keeping last 5.

## Output Formats

### Create Output
```
CHECKPOINT CREATED: <name>
=================================
Timestamp: YYYY-MM-DD-HH:MM
Git SHA:  <sha>
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

Untracked:
  path/to/untracked/
```

### List Output
```
CHECKPOINTS
===========
Name          | Timestamp        | SHA     | Status
--------------|------------------|---------|--------
<name1>       | YYYY-MM-DD-HH:MM | <sha>   | behind (X commits)
<name2>       | YYYY-MM-DD-HH:MM | <sha>   | current
```

## Gotchas

- Checkpoints reference git SHAs; rebasing or force-pushing invalidates them
- Checkpoint log is local-only (`.claude/checkpoints.log`)
- Running `create` on dirty state will commit changes first

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
