# 2. Rewrite observe.py to Bash for High-Frequency Hook Performance

Date: 2026-05-01

## Status

**Superseded** — Bash rewrite was reversed (2026-05-01) due to performance regression.

## Context

The `observe.py` hook executes on every `PreToolUse` and `PostToolUse` event—potentially hundreds of times per session. Python startup overhead (~50-100ms per invocation) creates latency in the critical path of tool execution. The hook performs simple operations: JSON parsing, field extraction, secret scrubbing, and file appending—all operations where Bash with `jq` could match or exceed Python performance without the interpreter startup cost.

Complex logic like git remote hashing for project detection remains better suited to Python due to regex complexity and maintainability.

## Decision (Original)

We rewrote the hook entrypoint from Python (`observe.py`) to Bash (`observe.sh`) while retaining Python helpers for complex operations.

## Decision (Reversed)

**Bash was reverted to Python** because:

1. **Performance regression**: Bash (183ms/call) was 3x slower than Python (61ms/call)
2. **Root cause**: Bash spawned 34 subprocesses per invocation (13× jq, 16× sed, 3× python3, 2× date/xxd)
3. **Wrong assumption**: Claude Code spawns a new process for every hook call regardless of language, so startup overhead is equal. Bash then adds 34 more processes.

### Performance Comparison

| Metric | Python | Bash |
|--------|--------|------|
| Time per call | 61ms | 183ms |
| Process spawns | 0 | 34 |
| Winner | ✓ | |

### Bash Subprocess Breakdown

| Subprocess | Count | Purpose |
|------------|-------|---------|
| jq | 13 | JSON parsing |
| sed | 16 | Secret scrubbing |
| python3 | 3 | Project detection |
| date/xxd | 2 | Timestamp/ID generation |

## Consequences

- **Keep Python** as hook entrypoint for optimal performance
- **Single language** for hook logic (simpler maintenance)
- **No jq dependency** required
- **Tests restored** to original Python-based tests

## Lessons Learned

> **Assumption validation is critical.** The original assumption was "bash startup is faster than Python." Reality: Claude Code spawns a new process for every hook call regardless, so startup is equal. Bash then spawns many subprocesses, making it slower.

When comparing languages for hooks, measure:
1. Process spawn overhead (fork + exec)
2. Subprocess count in each implementation
3. Total wall-clock time with realistic payloads
