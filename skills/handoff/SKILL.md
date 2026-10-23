---
name: handoff
description: >-
  Aggregates mission intent and artifact pointers into a phase handoff document. Use when ending a session, switching agent phases, or preparing context displacement for a peer agent.
argument-hint: |-
  What will the next session be used for?
---

# Handoff

Write a zero-detail handoff document so a fresh agent can continue the work without re-reading chat history.

## Storage Placement

Save the document to the current topic root:
`[artifact_dir]/handoff.md` (default `.lsz/{date}/{topic}/handoff.md`).

Do not save to OS temp directories. Preserving the file in the workspace maintains the mission audit trail. Save one handoff per phase directory to prevent overwrites.

## Schema (Zero-Detail Mission Pointer)

Follow ADR-0009. The handoff is a mission pointer, not a technical log:

1. **Goal & Intent**: State the primary objective and explicit user constraints.
2. **Artifact Trail**: Provide absolute file paths to `mission_manifest.json`, `design.md`, ADRs, and diffs.
3. **Suggested Skills**: Name specific skills the next agent should invoke (e.g. `eval-gate`, `code-review`).
4. **Success Criteria**: State exactly what confirms completion for the next agent.

## Invariants

- **Zero Duplication**: Do not copy technical decisions, file lists, or test results present in referenced artifacts.
- **Context Displacement**: The next agent initializes state from this handoff alone, ignoring previous conversation history.
- **Redact Secrets**: Strip API keys, passwords, and sensitive tokens.
- **Tailor to Arguments**: If arguments were provided, focus the next directive on that objective.
