# 6. Consolidated Orchestration Pipeline

Date: 2026-05-25

## Status

Accepted

refines [5. Manifest-Driven Orchestration and Provenance Trace](0005-manifest-driven-orchestration-and-provenance-trace.md)

## Context

The previous orchestration pipeline used a standalone `plan` phase. With the introduction of **BDD scenarios** in the Brainstorming phase and **Behavior Sequence Mapping** in the TDD-Cycle phase, the middle `plan` phase became redundant and introduced unnecessary context switches.

## Decision

We will remove the standalone `plan` phase and consolidate its responsibilities into the Architect and TDD-Cycle phases.

1.  **Architect** absorbs the **High-Level Strategy**: identifying affected modules, cross-module dependencies, and high-level execution sequencing.
2.  **TDD-Cycle** absorbs the **Granular Execution Plan**: mapping BDD scenarios directly into a linear Behavior Sequence Map for implementation.
3.  **Refined Pipeline:** The "Heavy" track is reduced to a 6-phase flow: Brainstorming → Architect → Eval-Gate Define → TDD-Cycle → Eval-Gate Check → Code Review.

- Rejected: Keeping the standalone `plan` phase (redundant planning effort).
- Rejected: Moving all planning to Brainstorming (bloats the design phase with implementation details).

## Consequences

- Orchestration is faster and has fewer context resets.
- The `architect` skill must be updated to produce strategy artifacts.
- The `tdd-cycle` skill becomes the primary owner of implementation-level sequencing.
