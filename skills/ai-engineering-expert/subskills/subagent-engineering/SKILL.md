---
name: subagent-engineering
description: >-
  Subagent design and execution methodology — action space design, observation formatting, error recovery, parallel execution, orchestration constraints, and agent frontmatter for the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Subagent Engineering

Designing agent action spaces, tool definitions, and observation formatting for reliable completion.

## Action Space Rules

- Stable, explicit tool names
- Schema-first, narrow inputs
- Deterministic output shapes
- Avoid catch-all tools unless isolation impossible

## Observation Design

Deliver runtime truth passively (tee server logs or pipes) rather than forcing blind query loops. Standard commands and scripts return native execution truth (stdout, stderr, exit codes). Do not force artificial JSON envelopes onto standard shell output. Reserve structured envelopes for specialized RPC or MCP agent endpoints.

## Error Recovery

Every error path needs:

- Root cause hint
- Safe retry instruction
- Explicit stop condition

## Parallel Agent Execution

Maximize context efficiency and reduce latency by launching independent subagents concurrently.

- **Anti-Pattern:** Running a security review agent, waiting for it to finish, then running a performance review agent
- **LSZ Pattern:** Launch independent subagents concurrently in one payload when outputs do not depend on each other.

## Intent vs Execution

Orchestrator owns intent. Subagents own execution. The orchestrator grills the user to capture parameters and pointers as a settled design tree. The subagent executes generation and verification. It must not re-grill the user. It returns a structured result. This division prevents hero-mode and preserves execution fidelity.

## Native Agent Orchestration Constraints

Subagents operate under strict constraints. Violating them produces brittle or broken workflows.

- **No Agent-ception:** Subagents DO NOT have access to the `Agent` tool. A subagent cannot launch a new subagent. All orchestration MUST be done by the primary orchestrator in the main conversation context.
- **No Subagent UI:** Subagents do not own the interaction flow with the user. If a subagent needs approval or a branch decision, it must return a structured response to the primary agent.
- **Stateless Iteration:** When iterating on a subagent's artifact (e.g. user rejects a plan and provides feedback), do not resume the old subagent via `SendMessage`. Resumed agents accumulate context bloat. Instead, spawn a new agent and pass the file path of the previous artifact alongside the user's feedback.

## Frontmatter Requirements

### Agents

- Always include `tools:` to define tool scope as a YAML array. Omitting it defaults to full tool access, which is a security and alignment risk.
- For deterministic skill invocation, declare skills as a YAML array in frontmatter. Preloading skills avoids runtime `Skill` calls, reduces latency, and keeps execution predictable.

## Reference

[Full details: tool-design-contracts.md](references/tool-design-contracts.md)
