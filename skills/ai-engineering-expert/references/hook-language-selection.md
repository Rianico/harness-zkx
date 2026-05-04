# Hook Language Selection

## Principles

### 1. Frequency Demands Speed
Hooks that fire on every tool use (PreToolUse, PostToolUse, Stop) execute
hundreds of times per session. Python interpreter startup (~50-100ms)
accumulates into noticeable latency. Bash starts in ~5-10ms.

**Principle:** If the hook runs >10 times per session and does simple work,
prefer bash.

### 2. Complexity Demands Clarity
Hooks that parse git config, call APIs, manage state, or require external
dependencies gain more from Python's ecosystem than they lose from startup
overhead.

**Principle:** If the hook has >50 lines of logic or needs external libs,
prefer python.

### 3. Hybrid When Both Matter
A bash entrypoint can call a python helper for complex operations while
keeping the hot path fast.

**Principle:** When frequency AND complexity both apply, split them.

---

## The Frequency Problem

**Symptoms:**
- Hook fires on PreToolUse, PostToolUse, or Stop
- Executes 50+ times per typical session
- Does simple work: JSON extraction, field logging, file append, string transform

**Solution: Bash with jq**

Bash handles stdin/stdout plumbing natively. With `jq`, JSON parsing
matches Python capability without interpreter overhead.

**Example: Event Logger Hook**
```bash
#!/usr/bin/env bash
# Logs tool invocations with scrubbed secrets
event_type="$1"
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Read JSON from stdin, extract fields, scrub secrets
jq --arg event "$event_type" --arg ts "$timestamp" '
  . + {event: $event, timestamp: $ts}
  | .input |= gsub("(sk-[a-zA-Z0-9]{20,})"; "[REDACTED]")
' >> "$CLAUDE_LOG_FILE"
```

**When NOT to use bash:**
- Need to maintain state across invocations
- Complex regex that's fragile in bash
- Error handling must be robust (bash errors are silent by default)

---

## The Complexity Problem

**Symptoms:**
- Hook needs external dependencies (requests, git parsing, crypto)
- Logic exceeds 50 lines or has deep conditionals
- State must persist or accumulate across invocations
- Error handling must be explicit and recoverable

**Solution: Python**

Python's startup cost is amortized when the work is substantial.
The ecosystem and error handling justify the overhead.

**Example: Project Detection Helper**
```python
#!/usr/bin/env python3
"""Called by bash hook for complex project ID generation."""
import subprocess
import hashlib

def get_project_id():
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return "unknown"

    # Complex hashing logic
    return hashlib.sha256(result.stdout.strip().encode()).hexdigest()[:12]

if __name__ == "__main__":
    print(get_project_id())
```

**When NOT to use python:**
- Hook fires on every tool use and only logs/transforms
- No external dependencies needed
- Startup latency would be user-visible

---

## The Hybrid Pattern

When a hook needs both frequency AND complexity, split the responsibilities:

1. **Bash entrypoint** handles the hot path (stdin/stdout, simple transforms)
2. **Python helper** handles complex operations (called only when needed)

**Architecture:**
```
Claude Code Event
       │
       ▼
┌─────────────────┐
│  observe.sh     │  ← Always fast (bash startup ~5ms)
│  (bash)         │
└────────┬────────┘
         │
         │ only when project ID needed
         ▼
┌─────────────────┐
│ detect_project  │  ← Called once per session
│ (python)        │
└─────────────────┘
```

**Example: Hybrid Observe Hook**
```bash
#!/usr/bin/env bash
# observe.sh - Fast entrypoint, delegates complexity

event_type="$1"
project_id=""  # Cached per session

# Simple logging path (fast, no python)
log_event() {
  jq --arg event "$event_type" '{event: $event, timestamp: now}'
}

# Complex project detection (calls python helper only when needed)
get_project_id() {
  if [[ -z "$project_id" ]]; then
    project_id=$(python3 "$HOOK_DIR/detect_project.py")
  fi
  echo "$project_id"
}

# Main logic - python only invoked if project context needed
if [[ "$event_type" == "session_start" ]]; then
  log_event | jq --arg proj "$(get_project_id)" '. + {project: $proj}'
else
  log_event
fi >> "$CLAUDE_LOG_FILE"
```

---

## Decision Flowchart

```
                    ┌─────────────────────┐
                    │ What does the hook  │
                    │ need to do?         │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ Simple I/O  │     │ Complex     │     │ Both        │
    │ only        │     │ logic only  │     │ needed      │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │ How often?  │     │ How big?    │     │ Hybrid      │
    │             │     │             │     │             │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
     ┌─────┴─────┐       ┌─────┴─────┐             │
     │           │       │           │             │
     ▼           ▼       ▼           ▼             ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ High    │ │ Low     │ │ <50     │ │ >50     │ │ Bash    │
│ freq    │ │ freq    │ │ lines   │ │ lines   │ │ entry   │
│ (>10/   │ │ (<10/   │ │         │ │ or deps │ │ +       │
│ session)│ │ session)│ │         │ │         │ │ Python  │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │ helper  │
     │           │           │           │     └────┬────┘
     │           │           │           │          │
     ▼           ▼           ▼           ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ BASH    │ │ Either  │ │ Either  │ │ PYTHON  │ │ HYBRID  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

**Quick Reference:**

| Scenario | Language | Reason |
|----------|----------|--------|
| Logging, simple transform, file append | Bash | Frequency wins |
| Git parsing, API calls, crypto | Python | Complexity wins |
| Both frequency and complexity | Hybrid | Split the work |
| Stateful across invocations | Python | Bash is stateless |
| Needs external libs | Python | Dependency ecosystem |

---

## Performance Testing Requirements (MANDATORY)

**Rule:** When making performance claims, benchmark with real tests first—never guess by theory.

### Why This Matters

A bash hook was assumed faster than Python for high-frequency events. Reality:
- Bash: 183ms/call
- Python: 61ms/call
- **Python was 3x faster**

Bash spawned 34 subprocesses (jq, sed, python helpers) per invocation, while Python ran in a single process.

### Mandatory Steps

1. **Measure wall-clock time** with realistic payloads, not synthetic benchmarks
2. **Count subprocess spawns** — each fork/exec has overhead that compounds
3. **Test in the actual execution context** — Claude Code spawns a new process for every hook call regardless of language
4. **Document findings** with actual numbers

### Benchmarking Template

```bash
# Test with realistic payload
time for i in {1..100}; do
  echo '{"tool":"Read","input":{"path":"/long/path/file.py"}}' | ./hook.sh pre
done

# Report: 100 calls in X seconds = Y ms/call
# Subprocess count: N (use strace -f -e trace=clone,execve)
```

### Anti-Patterns

| Assumption | Reality |
|------------|---------|
| "Bash startup is faster" | Claude Code spawns a new process anyway; startup is equal |
| "jq is faster than Python JSON" | Maybe, but jq spawn + pipe overhead may negate it |
| "Simple operations favor bash" | True only if zero subprocesses are spawned |

---

## Output Format Reference

After choosing a language, see [hook-output-format.md](hook-output-format.md) for:
- `systemMessage` vs `additionalContext` decision guide
- JSON output construction with `jq`
- Hook event names and special fields
- Real example: LSP diagnostics hook
