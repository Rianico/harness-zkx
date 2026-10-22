---
name: subagent-engineering
description: >-
  Subagent execution methodology — context isolation firewalls, speculative drafting, dispatch timing, fresh versus inherited context, model selection, and orchestration constraints. Use when designing agents, managing context bloat, or coordinating subagents.
metadata:
  managed-by: ai-engineering-expert
  credits:
    - source: https://arxiv.org/abs/2609.35928
      author: arXiv:2609.35928
      note: Prompted Identity Degrades Cooperation in Multi-Agent LLM Systems
    - source: https://arxiv.org/abs/2307.03172
      author: Liu et al. (2023)
      note: Lost in the Middle - How Language Models Use Long Contexts
    - source: https://arxiv.org/abs/2603.20324
      author: arXiv:2603.20324
      note: The Selection Bottleneck in Multi-Agent LLM Pipelines
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

## Model Selection & Tier Allocation

Matching model capability to subagent responsibility prevents toxic premise failures and syntax thrashing.

### The Selection Bottleneck

The orchestrator reasoning capacity must match or exceed its subagents. A weaker orchestrator cannot evaluate, reconcile, or verify conflicting subagent outputs.

### The Toxic Premise Risk

Smaller models suffer premature convergence during research. Hallucinated facts returned to the orchestrator corrupt downstream architecture. Keep subagents on the frontier model (inherit) for research, drafting, and adversarial review.

### Model Anonymity

Never prompt subagents with model names. Prompt strictly by task role and contract to avoid model factionalism (arXiv:2609.35928).

### The Three Guardrails for Lighter Subagents

For subagent dispatch, downgrade to lighter models (e.g. Flash or Haiku) only when all three conditions hold. In-band execution follows the parent Model Routing table:
1. **Read-Only Action Space:** Grant only read tools. Smaller subagents must never hold mutation permissions.
2. **Schema-First Contracts:** Force rigid JSON or YAML schemas. Never request free-form prose.
3. **Deterministic Environmental Backstops:** Verify all outputs via compilers, linters, or regex gates rather than orchestrator trust.

---

## Native Orchestration Constraints

Subagents operate under strict structural boundaries:
- **No Agent-ception:** Subagents cannot access the Agent tool (depth limit 1). The primary orchestrator coordinates all agents.
- **No Subagent UI:** Subagents do not own user interaction. When blocked, the subagent returns a structured blocker to the orchestrator.
- **Principle of Least Privilege:** Explicitly declare tool scope via the frontmatter tools array. Researchers receive read-only tools. Implementers receive edit tools.
- **Passive Runtime Truth:** Capture runtime truth passively (`tee` logs, pipes) instead of polling with blind query loops. Rely on native execution truth (stdout, stderr, exit codes). Never force artificial JSON envelopes onto standard shell output. Reserve structured envelopes for specialized RPC or MCP agent endpoints.

---

## References

- [tool-design-contracts.md](references/tool-design-contracts.md) -- Action space granularity, observation schemas, error recovery examples, and context budgeting.
- [arXiv:2609.35928](https://arxiv.org/abs/2609.35928) -- Prompted identity degrades cooperation in multi-agent LLM systems.
- [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) -- Lost in the middle: how language models use long contexts.
- [arXiv:2603.20324](https://arxiv.org/abs/2603.20324) -- The selection bottleneck in multi-agent LLM pipelines.
