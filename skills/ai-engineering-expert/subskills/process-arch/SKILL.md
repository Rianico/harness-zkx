---
name: process-arch
description: >-
  Eval-first development loop, model routing, session strategy, and team operating model for AI-assisted engineering in the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Process & Architecture

Operating models for teams and individuals doing AI-assisted development.

## Team Operating Model (GDD)

The LSZ operating model follows **GDD (Goal-Driven Development)**:
- Planning quality > typing speed (BDD Scenarios first)
- Eval coverage > anecdotal confidence (EDD verification)
- Review focus: behavior and invariants (Semantic vs. Deterministic split), not style

## Eval-First Loop

1. Define capability eval and regression eval
2. Run baseline, capture failure signatures
3. Execute implementation
4. Re-run evals, compare deltas

## Model Routing

- Fast/cheap: classification, boilerplate, narrow edits
- Balanced: implementation, refactors, multi-file work
- Strong: architecture, root-cause analysis, complex invariants

## Session Strategy

- Continue for closely-coupled units
- Fresh session after major phase transitions
- Compact at milestones using the **High-Fidelity Handoff** pattern
- Use `handoff.md` to displace history and re-initialize context with 100% fidelity

## Reference

[Full details: eval-first-development.md](references/eval-first-development.md)
