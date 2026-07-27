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

Every tool response should include:
- `status`: success|warning|error
- `summary`: one-line result
- `next_actions`: actionable follow-ups
- `artifacts`: file paths / IDs

## Error Recovery

Every error path needs:
- Root cause hint
- Safe retry instruction
- Explicit stop condition

## Parallel Agent Execution

Maximize context efficiency and reduce latency by launching independent subagents concurrently.

- **Anti-Pattern:** Running a security review agent, waiting for it to finish, then running a performance review agent
- **LSZ Pattern:** Launching multiple subagents concurrently in a single tool call payload when their tasks do not depend on each other's outputs

## Native Agent Orchestration Constraints

Subagents operate under strict constraints. Violating them produces brittle or broken workflows.

- **No Agent-ception:** Subagents DO NOT have access to the `Agent` tool. A subagent cannot launch a new subagent. All orchestration MUST be done by the primary orchestrator in the main conversation context.
- **No Subagent UI:** Subagents do not own the interaction flow with the user. If a subagent needs approval or a branch decision, it must return a structured response to the primary agent.
- **Stateless Iteration:** When iterating on a subagent's artifact (e.g., user rejects a plan and provides feedback), do NOT resume the old subagent via `SendMessage`. Resumed agents accumulate context bloat. Instead, spawn a NEW agent and pass the file path of the previous artifact alongside the user's feedback.

## Frontmatter Requirements

### Agents

- ALWAYS include `tools:` — explicitly define tool scope as a YAML array. Omitting it defaults to full tool access, which is a security and alignment risk.
- If an agent has deterministic skill invocation, define a `skills:` header as a YAML array so those skills can be preloaded up front. Prefer this over runtime `Skill` calls when the required skills are known in advance — it reduces round-trip overhead and keeps execution predictable.

## Reference

[Full details: tool-design-contracts.md](references/tool-design-contracts.md)
