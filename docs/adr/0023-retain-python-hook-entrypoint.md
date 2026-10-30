# 23. Retain Python hook entrypoint

Date: 2026-05-01

## Status

Accepted

<!-- Lifecycle: Proposed | Accepted | Rejected | Deprecated | Superseded. Keep this section to the status word plus relationship lines (Supercedes, Superceded by, Amends, Amended by, Clarifies, Clarified by, Relates to) inserted by `adr new -s` / `adr link`. Rationale belongs in Context/Decision, never here. -->
Supercedes [2. Rewrite observe.py to Bash for High-Frequency Hook Performance](0002-rewrite-observe-py-to-bash-for-high-frequency-hook-performance.md)

## Context

The `observe.py` hook executes on every `PreToolUse` and `PostToolUse` event — potentially hundreds of times per session — so interpreter startup cost sits in the critical path. The working assumption was that a Bash + `jq` rewrite would beat Python startup for the hook's simple operations (JSON parsing, field extraction, secret scrubbing, file appending).

Measurement falsified the assumption: Python 61ms/call with no spawned subprocesses versus Bash 183ms/call with 34 subprocesses per invocation (`jq` 13, `sed` 16, `python3` 3 for git hashing, `date`/`xxd` 2). Claude Code spawns a new process for every hook call regardless of language, so startup cost is equal and Bash only adds subprocess overhead.

Note: recorded retroactively on 2026-10-30 from the account preserved in ADR-0002; the decision itself dates to 2026-05-01.

## Decision

We will keep Python (`observe.py`) as the hook entrypoint; the Bash rewrite (`observe.sh`) is reversed. Complex operations such as git remote hashing stay in Python helpers.

### Considered Options

- **Bash rewrite (the original ADR-0002 decision)** — rejected: assumed faster startup than Python. Cons: 183ms/call vs 61ms/call (3x slower); 34 subprocesses per invocation. Why not: process-spawn cost is equal across languages at this seam, so Bash only adds overhead.
## Consequences

- Keep Python as the hook entrypoint; no `jq` dependency.
- Tests stay on the original Python-based suite.
- Load-bearing assumption: validate language-performance claims with wall-clock measurement that includes spawn overhead and subprocess count — never startup time alone.

