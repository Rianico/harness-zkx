# 8. Goal Locking and Aggregated Manifest Hierarchy

Date: 2026-05-25

## Status

Accepted
Amends [ADR-0007](0007-mission-manifest-schema-and-update-contract.md)

amends [7. Mission Manifest Schema and Update Contract](0007-mission-manifest-schema-and-update-contract.md)

enforced by [9. Behavioral Evals and Manifest-Indexed Handoffs](0009-behavioral-evals-and-manifest-indexed-handoffs.md)

## Context

To scale manifest-driven orchestration without bloating the mission-level context, we need a way to decompose the manifest record. We also need to prevent "Scope Shrinkage," where the model omits difficult sub-tasks from its reports.

## Decision

We will implement an **Aggregated Manifest Hierarchy** and a **Goal Locking** pattern.

### 1. The Manifest Hierarchy
- **Mission Manifest (`mission_manifest.json`)**: The root authority for the mission. It tracks phase-level status and stores pointers + hashes for Skill Manifests.
- **Skill Manifest (`[skill]_manifest.json`)**: Local to a skill. Used when a skill meets the **IPS Criteria**:
  - **Iterative**: The task involves looped sub-units (e.g., TDD scenarios).
  - **Parallel**: The task involves concurrent workers.
  - **State-Dependent**: The task requires tracking intermediate verification states.

### 2. The Goal Locking Pattern
- Before dispatching a skill, the Orchestrator MUST "Lock the Goal" by pre-allocating the expected **Work Units** (e.g., specific BDD scenarios) in the `mission_manifest.json`.
- The skill is then strictly constrained to complete the pre-allocated units. It cannot "move the goalposts" by omitting units from its local manifest.

### 3. Environmental Supremacy (The Tie-Breaker)
- **Environmental Truth (EDD) is the Supreme Authority.**
- In any conflict between a manifest claim ("Passed") and a fresh environmental signal (e.g., failing test, mismatched hash), the Orchestrator MUST overwrite the manifest to reflect the environmental reality.

- Rejected: Fluid Goal Discovery (allows models to skip hard tasks).
- Rejected: Subagent-Only Manifests (fragmented audit trail).

## Consequences

- Orchestrators become more proactive in defining the implementation sequence.
- Scope shrinkage is detected early through pre-allocated unit checks.
- Auditability scales to complex, multi-unit missions without exceeding context limits.
