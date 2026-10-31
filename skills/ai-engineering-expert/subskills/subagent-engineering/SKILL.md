---
name: subagent-engineering
description: >-
  Subagent execution methodology: context firewalls, speculative drafting, and action scoping. Use when designing multi-agent workflows, fixing context bloat, or diagnosing a failed subagent.
metadata:
  managed-by: ai-engineering-expert
---

# Subagent Engineering

Subagent orchestration methodology, context isolation firewalls, and execution scope contracts.

## 1. Core Mental Model: Subagents as Context Firewalls

Monolithic agents degrade over long horizons. Token churn, command logs, and large file reads dilute attention. This causes instruction drift and attention dilution (Liu et al., 2023).

A subagent operates as an ephemeral execution scope. Its primary purpose is **Context Isolation**:
- **Absorb Exploratory Token Churn:** The subagent consumes high-volume exploration, file scanning, and research in an isolated window.
- **Quarantine Speculative Drafts:** Exploratory edits and syntax trials stay inside the subagent scratchpad. Discarded drafts leave zero debris in the orchestrator history.
- **Eliminate Attention Dilution:** The orchestrator maintains a lean, focused context across multi-phase tasks.

Its secondary purpose is **Parallelism**:
- **Collapse Wall-Clock Latency:** Concurrent subagents execute independent subtasks in parallel.

### Terminology Boundary: Peer Agent vs Subagent

Distinguish peer agents from subagents before choosing an execution topology.

#### Peer Agent (Horizontal Orchestration)

A peer agent coordinates horizontal workflows across independent environments:
- **Independent Lifecycle:** Operates as an independent, long-lived process or session (such as a PI agent, Codex agent, or Claude in Herdr panes).
- **Autonomous Identity:** Maintains dedicated context, separate credentials, and direct user interface capability.
- **Out-of-Band Coordination:** Coordinates asynchronously through IPC, dispatch tickets, or the `herdr` skill's scripts. If the session runs under Herdr, then run those scripts. Otherwise use IPC or dispatch tickets.

#### Subagent (Vertical Context Firewall)

A subagent enforces vertical context isolation under a single orchestrator:
- **Ephemeral Scope:** Spawns via an internal subagent dispatch tool call to create a subordinate execution scope.
- **Clean-Room Scratchpad:** Absorbs exploratory token churn and quarantines speculative drafts away from orchestrator context.
- **Masked Authority:** Operates under strict depth = 1 and tool masking (no recursive delegation).
- **In-Band Summaries:** Returns structured in-band summaries and file pointers to the parent orchestrator.

#### Architectural Comparison

| Dimension | Peer Agent | Subagent |
| --- | --- | --- |
| Topology | Horizontal peer network | Vertical context firewall |
| Lifecycle | Long-lived process | Ephemeral execution scope |
| Identity | Autonomous identity and user session | Ephemeral role scoped by parent brief |
| User Interface | Direct user interaction permitted | Direct user interaction forbidden |
| Communication | Asynchronous out-of-band IPC or tickets | Synchronous in-band tool call summaries |

#### Operational Boundary Rules

- **Local Scratchpad Isolation:** If isolating exploratory churn or speculative drafts, spawn a subagent. Do not use distributed peer-agent queues for local scratchpad work.
- **Long-Lived Coordination:** If coordinating long-lived peer agents, dispatch out-of-band tickets or use IPC. Do not coordinate long-lived peer agents via fragile parent-child prompts.

## 2. Dispatch Gates: When to Dispatch vs Keep In-Band

Evaluate tasks against concrete dispatch gates before execution.

### When to Dispatch a Subagent

- **High-Churn Research:** If operations produce >3,000 raw output tokens, dispatch a subagent.
- **Speculative Drafting:** If exploring candidate implementations or prototypes, quarantine scratchpad work inside a subagent.
- **Context Pressure Asymmetry:** If executing adversarial review, dispatch a subagent with clean-room standards and diff-only context.
- **Parallel Decomposed Tasks:** If independent tasks touch separate architectural seams, dispatch concurrent subagents.
- **Least-Privilege Isolation:** If a task requires restricted permissions, dispatch a subagent with a scoped action space.

### When to Keep In-Band

- **Trivial Operations:** If tasks touch <100 lines or run single commands, execute in-band. Subagent setup overhead exceeds execution time.
- **Direct User Alignment (IDD):** If probing user intent or clarifying requirements, keep execution in-band. Subagents must never interrogate the user.
- **Shared Mutable State:** If tasks modify identical files without clean seams, keep execution in-band. Concurrent edits risk merge conflicts and broken state invariants.
- **Nested Hierarchies:** If execution is already inside a subagent, keep execution in-band. Enforce a strict depth limit of 1.

## 3. Context Topology: Fresh vs Inherited Context

Choose context topology based on task isolation needs.

### Fresh Context (The Default)

Fresh context provides a clean room:
- **Pristine Window:** The subagent starts with only its system prompt, role definition, and target brief.
- **Zero Baggage:** Fresh context eliminates prompt pollution, confirmation bias, and instruction drift.
- **Stateless Iteration:** If revising an artifact, spawn a fresh subagent with the artifact pointer and critique notes. Never resume stale subagents to iterate on rejected work.

### Inherited Context

Inherited context passes prior session history into the subagent:
- **Use Sparingly:** If a task requires conversational nuances that a brief cannot capture, use inherited context.
- **Avoid Context Rot:** Resumed subagents accumulate token debt rapidly.

## 4. Pointer-First State Passing

Subagents exchange state through file paths, never through inlined text blobs.

- **Pass Pointers in Prompts:** If directing a subagent, pass absolute file paths to input specifications or plans.
- **Quarantine Artifact Bodies:** Subagents write outputs directly to disk. The orchestrator reads summaries, never full artifacts.
- **Use Topic Roots:** If coordinating multi-phase workflows, establish a shared topic root under `.lsz/` with phase subdirectories.
- **Preserve Orchestrator Budget:** Downstream subagents inspect full artifacts on demand via file links.

## 5. Action Space Permissions & Scoping

Declare explicit tool boundaries for every subagent. Define action spaces by functional capability classes: inspection, workspace mutation, verification, and delegation.

### Least-Privilege Scoping

- **Read-Only Scopes:** If dispatching researchers or reviewers, grant only inspection and search tools. Strip all workspace mutation and execution tools.
- **Implementer Scopes:** If dispatching implementers, grant workspace mutation, patch, and verification tools. Strip subagent dispatch tools.

### Tool Masking

- **Strip Recursive Delegation:** If configuring subagents, mask out subagent dispatch tools. Enforce depth = 1.
- **Return Structured Blockers:** If a subagent encounters an impasse, return a structured blocker to the orchestrator.

### Skeptic Reviewer Archetype

- **Purpose**: Clean-room adversarial review against invariants, anti-laziness, and Clean Architecture.
- **Action space**: Read-only inspection tools (`read_file`, `grep_search`). Grant zero mutation tools and zero delegation tools.
- **Context**: Fresh context only. Include diff and intent contract or spec only. Exclude exploratory history.
- **Authority & Implementation**: Follow [`code-review`](../../../code-review/SKILL.md) for gate execution.

## 6. Inter-Agent Return Protocol

Subagents, peer agents, and workflow callbacks return through the canonical dual-mode envelope in [inter-agent-message-contract.md](references/inter-agent-message-contract.md). The reference carries the prose template, the JSON schema, the route decision matrix, and the severity taxonomy.

## References

- [inter-agent-message-contract.md](references/inter-agent-message-contract.md) -- Inter-agent return protocol, dual-mode envelope, and state routing contract.
- [tool-design-contracts.md](../../references/tool-design-contracts.md) -- Tool action spaces, passive runtime truth, structured envelopes, and error recovery.
- [arXiv:2307.03172](https://arxiv.org/abs/2307.03172) -- Lost in the middle: how language models use long contexts.
- [arXiv:2603.20324](https://arxiv.org/abs/2603.20324) -- The selection bottleneck in multi-agent LLM pipelines.
- [arXiv:2609.35928](https://arxiv.org/abs/2609.35928) -- Prompted identity degrades cooperation in multi-agent LLM systems.
