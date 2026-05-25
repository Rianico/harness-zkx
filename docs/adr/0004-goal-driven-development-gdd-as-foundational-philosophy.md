# 4. Goal-Driven Development (GDD) as Foundational Philosophy

Date: 2026-05-25

## Status

Accepted

implements [3. Respect authoritative tool signals](0003-respect-authoritative-tool-signals.md)

supports [5. Manifest-Driven Orchestration and Provenance Trace](0005-manifest-driven-orchestration-and-provenance-trace.md)

## Context

LLMs are fundamentally **Probabilistic Machines** trying to operate in a **Deterministic World**. Without a structured way to anchor the AI's output to human intent and environmental truth, agents suffer from "Hallucinated Completion" and "Intent Drift." We need a root philosophy that governs all boundaries, constraints, and verification logic in the LSZ architecture.

## Decision

We will use **GDD (Goal-Driven Development)** as the foundational root of the project. This philosophy is implemented through three non-negotiable pillars:

1.  **BDD (Behavior-Driven Development) for Intent Alignment:** Forcing a Shared Contract (Given/When/Then) before any implementation begins.
2.  **EDD (Eval-Driven Development) for Empirical Truth:** Treating the auditor as an "Executioner" who only trusts fresh environmental signals generated after the implementation.
3.  **Semantic vs. Deterministic Split:** Separating "Hard Gates" (compilers, linters, tests) from "Semantic Audits" (adversarial Skeptic review).

- Rejected: Vague Prompt-based Engineering (too fragile)
- Rejected: Test-Only Verification (misses semantic intent/architecture quality)

## Consequences

- All skills and agents must now include behavioral scenarios (BDD) and success criteria (EDD).
- Orchestration becomes more rigorous, adding overhead for "Intent Locking" but significantly reducing rework caused by faked outcomes.
- Verification is decoupled into deterministic and semantic phases, allowing specialized agents/tools for each.
