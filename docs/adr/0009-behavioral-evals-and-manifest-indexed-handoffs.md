# 9. Behavioral Evals and Manifest-Indexed Handoffs

Date: 2026-05-25

## Status

Accepted
Amends [ADR-0004](0004-goal-driven-development-gdd-as-foundational-philosophy.md), [ADR-0008](0008-goal-locking-and-aggregated-manifest-hierarchy.md)

refines [4. Goal-Driven Development (GDD) as Foundational Philosophy](0004-goal-driven-development-gdd-as-foundational-philosophy.md)

enforces [8. Goal Locking and Aggregated Manifest Hierarchy](0008-goal-locking-and-aggregated-manifest-hierarchy.md)

## Context

Audit of the `daemon-socket-redesign` mission revealed three systemic weaknesses in the initial GDD implementation:
1.  **Weak Evals:** Eval scripts were performing static "Grep" checks on source code instead of behavioral verification in the environment.
2.  **SOT Drift:** The `design.md` (Source of Truth) drifted from the actual implementation decisions.
3.  **Handoff Redundancy:** Multiple handoff and summary files repeated the same technical details, bloating context.

## Decision

We will refine the GDD architecture with "Second-Generation" patterns:

### 1. Behavioral-First Evals (Executable Assertions)
- **Rule:** Every `Capability` eval MUST be an **Executable Assertion** (e.g., `pytest`, `curl`, `cli --status` check).
- **Ban:** Eval scripts are strictly forbidden from using static analysis (grepping strings in `.py` files) to verify behavioral goals.
- **Purpose:** Ensure the environment—not the code text—proves success.

### 2. Design-Implementation Sync (Semantic Guardrail)
- **Rule:** The Semantic Audit (`code-review`) MUST verify that any architectural or path-level changes made during implementation are back-propagated as amendments to `design.md`.
- **Purpose:** Maintain `design.md` as the durable Mission-level Source of Truth.

### 3. Manifest-Indexed Handoffs (Zero-Detail Handoffs)
- **Rule:** The `handoff.md` document is refactored into a **Mission Pointer**. It should contain:
  1. The high-level **Goal**.
  2. A pointer to the **`mission_manifest.json`** for technical status and artifact index.
  3. A pointer to **`design.md`** for intent.
- **Ban:** Handoffs MUST NOT repeat technical decisions, file lists, or test results already present in the Manifest or Design.

### 4. Explicit Goal Locking (Pre-population)
- **Rule:** The Orchestrator MUST run `manifest-manager add-unit` for every BDD Scenario discovered in Brainstorming *before* dispatching implementation.

### Considered Options

- **Rejected: Static grep-based evals** — text search in `.py` files performs Paper Tiger verification; environment proves nothing.
- **Rejected: Detail-rich handoffs repeating manifest/design** — bloats context and creates a second source of truth that drifts.

## Consequences

- Missions produce fewer, higher-signal documents.
- Context is preserved by pointing to structured data (JSON) rather than repeating prose.
- Evals become robust against "Paper Tigers" and actually prove product behavior.
