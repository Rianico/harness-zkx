---
name: agent-harness
description: >-
  Agent action space design, observation formatting, error recovery contracts, and context budgeting for the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Agent & Harness Design

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

## Reference

[Full details: tool-design-contracts.md](references/tool-design-contracts.md)
