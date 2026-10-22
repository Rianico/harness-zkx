---
name: subagent-engineering
description: >-
  Subagent execution methodology — context isolation firewalls, speculative drafting, dispatch timing, fresh versus inherited context, and orchestration constraints. Use when designing agents, managing context bloat, or coordinating subagents.
metadata:
  managed-by: ai-engineering-expert
---

# Subagent Engineering

Subagent orchestration methodology, context isolation boundaries, and execution scope contracts.

## Core Mental Model: Subagents as Context Firewalls

Monolithic agents degrade over long horizons. High token churn, command logs, and large file reads dilute attention. This causes instruction drift and "Lost in the Middle" failure modes (Liu et al., 2023).

A subagent operates as an **ephemeral execution scope**. Its primary function is **Context Isolation**:
- **Token Churn Absorption:** The subagent consumes high-volume exploration, file scanning, and research in an isolated window.
- **Asymmetric Information Flow:** The subagent returns only distilled conclusions, structured schemas, or file pointers.
- **Context Preservation:** The orchestrator maintains a lean, high-signal context across multi-phase missions.

### Speculative Drafting as Context Isolation

Drafting in a subagent provides speculative execution with automatic rollback protection:
- **Scratchpad Quarantine:** Prototyping, exploratory edits, and syntax trials remain inside the subagent.
- **Zero In-Band Pollution:** Discarded trials leave no debris in the primary conversation history.
- **Stateless Revision:** Revise artifacts by spawning fresh subagents with file pointers rather than accumulating conversational scars.

### Concurrency and Throughput

Parallelism is the secondary purpose of subagents. Concurrently dispatching independent subtasks collapses sequential wall-clock latency from linear wait times into constant time.

---

## Timing & Scenarios: When to Dispatch Subagents

Knowing when to dispatch a subagent determines orchestration efficiency.

### When to Dispatch a Subagent

- **High Token Churn Research:** Broad codebase searches, reading large documentation sets, or scanning multi-megabyte logs.
- **Speculative Drafting & Prototyping:** Exploring candidate implementations or drafting complex proposals without risking the primary thread.
- **Independent Verification:** Running security audits, architectural checks, or adversarial code reviews concurrently.
- **Context Pressure Asymmetry:** Offloading high-pressure exploration from the low-pressure, strategic orchestrator.

### When NOT to Dispatch a Subagent

- **Trivial In-Band Operations:** Single-file reads, quick inspection commands, or one-line edits where subagent setup overhead exceeds execution time.
- **Interactive User Alignment:** Interactive grilling and parameter capture require direct human dialog. Subagents must never interrogate the user.
- **Shared Mutable State Without Seams:** Concurrent tasks touching the same files risk merge conflicts and broken state invariants.

---

## Context Topology: Fresh Context vs Inherited Context

Choosing context topology defines how information moves across agent boundaries.

### Fresh Context (The Default)

Fresh context provides a clean room:
- **Pristine Window:** The subagent starts with only its system prompt, role definition, and target brief.
- **Zero Baggage:** Eliminates prompt pollution, confirmation bias, and instruction drift from earlier conversational turns.
- **Pointer-First Exchange:** Pass context via file paths (file links) and structured contracts. Never copy-paste conversation transcripts.

### Inherited Context & Continuation Scopes

Inherited context passes prior session history into the subagent:
- **Use Sparingly:** Use only when the subagent requires historical conversational nuances that cannot be captured in a pointer brief.
- **The Context Rot Trap:** Resumed agents accumulate token debt rapidly.
- **Stateless Iteration Rule:** Never resume old subagents via SendMessage to iterate on rejected artifacts. Spawn a fresh subagent with the artifact pointer and critique notes.

---

## Native Orchestration Constraints

Subagents operate under strict structural boundaries:
- **No Agent-ception:** Subagents cannot access the Agent tool (depth limit 1). The primary orchestrator coordinates all agents.
- **No Subagent UI:** Subagents do not own user interaction. When blocked, the subagent returns a structured blocker to the orchestrator.
- **Principle of Least Privilege:** Explicitly declare tool scope via the frontmatter tools array. Researchers receive read-only tools. Implementers receive edit tools.
- **Passive Runtime Truth:** Rely on native execution truth (stdout, stderr, exit codes). Never force artificial JSON envelopes onto standard shell output.

---

## References

- [tool-design-contracts.md](references/tool-design-contracts.md) -- Action space granularity, observation schemas, error recovery examples, and context budgeting.
