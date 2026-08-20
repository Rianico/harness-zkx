# 2. Rewrite observe.py to Bash for High-Frequency Hook Performance

Date: 2026-05-01

## Status

Superseded — Bash rewrite was reversed (2026-05-01) due to performance regression.

## Context

The `observe.py` hook executes on every `PreToolUse` and `PostToolUse` event—potentially hundreds of times per session. Python startup overhead (~50-100ms per invocation) creates latency in the critical path of tool execution. The hook performs simple operations: JSON parsing, field extraction, secret scrubbing, and file appending—all operations where Bash with `jq` could match or exceed Python performance without the interpreter startup cost.

Complex logic like git remote hashing for project detection remains better suited to Python due to regex complexity and maintainability.

## Decision

We will keep Python (`observe.py`) as the hook entrypoint; the Bash rewrite (`observe.sh`) is reversed. The hook stays single-language with Python helpers retained only for complex operations.

### Considered Options

- **Rejected: Bash rewrite (original decision)** — rewrote the entrypoint to Bash while retaining Python helpers for git hashing. Rejected after measurement:
  - Pros: assumed faster startup than Python
  - Cons: 183ms/call vs Python 61ms/call (3x slower); spawned 34 subprocesses per invocation
  - Why not: Claude Code spawns a new process for every hook call regardless of language, so startup overhead is equal — Bash then adds substantial subprocess overhead

  #### Performance Comparison

  | Metric | Python | Bash |
  |--------|--------|------|
  | Time per call | 61ms | 183ms |
  | Process spawns | 0 | 34 |
  | Winner | ✓ | |

  #### Bash Subprocess Breakdown

  | Subprocess | Count | Purpose |
  |------------|-------|---------|
  | jq | 13 | JSON parsing |
  | sed | 16 | Secret scrubbing |
  | python3 | 3 | Project detection |
  | date/xxd | 2 | Timestamp/ID generation |

## Consequences

- Keep Python as hook entrypoint for optimal performance
- Single language for hook logic (simpler maintenance)
- No jq dependency required
- Tests restored to original Python-based tests
- **Load-bearing assumption (Lessons Learned):** Assumption validation is critical — the original assumption was "bash startup is faster than Python." Reality: Claude Code spawns a new process for every hook call regardless, so startup is equal and Bash-spawned subprocesses make it slower. When comparing languages for hooks, measure:
  1. Process spawn overhead (fork + exec)
  2. Subprocess count in each implementation
  3. Total wall-clock time with realistic payloads
