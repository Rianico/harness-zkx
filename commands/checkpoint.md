---
argument-hint: "[create|diff|list|clear] <name>"
allowed-tools:
  - Bash
  - Skill
---

# Checkpoint Command

Execute the checkpoint skill for workflow milestone management.

## Usage

```
/checkpoint create <name>  - Create named checkpoint
/checkpoint diff <name>    - Diff against checkpoint
/checkpoint list           - List all checkpoints
/checkpoint clear          - Clear old checkpoints
```

## Execution

Invoke the checkpoint skill with the provided arguments.

```
Skill: checkpoint
Args: $ARGUMENTS
```
