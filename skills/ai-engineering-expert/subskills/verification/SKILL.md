---
name: verification
description: >-
  Eval-Driven Development (EDD) methodology for deterministic verification and eval-first loops. Use when designing an evaluation strategy; not for running the gate (eval-gate).
metadata:
  managed-by: ai-engineering-expert
---

# Verification

Verification in LSZ seeks **Empirical Truth** through the environment. It ensures the probabilistic model achieves the human goal.

## The Foundation: EDD (Eval-Driven Development)

The auditor is an **Executioner**, not a reader. Never trust model claims of completion. Trust only fresh signals generated after implementation.

### 1. Deterministic Verification (Hard Gates)

Measured by non-LLM tools. These are binary, reliable, and cost zero tokens.

- **LSP & Linters:** Check diagnostics with your language server and linters. A finished task must be clean of errors and warnings.
- **Unit & Property Tests:** Use `pytest` or native test runners. Verify logic invariants that are mathematically certain.
- **Differential Observation:** Compare output of old vs new code against identical inputs. A difference in a deterministic area fails the run.

### 2. Semantic Verification (Qualitative Alignment)

Measured by Adversarial Orchestration. We use LLMs to verify what compilers cannot: Intent.

- **The Skeptic Agent:** Dispatch a subagent with a Skeptic persona. Its only goal is finding lazy code, semantic drift, or hallucinations.
- **BDD Comparison:** Compare final code against the BDD Scenarios locked during discovery. Verify behavioral compliance rather than superficial shape.
- **Explain-to-Verify:** Ask the model to explain how complex blocks satisfy BDD scenarios. If the explanation fails to map to code, reject the result.

---

## The Core Problem

When the same model writes and reviews code, it carries identical blind spots into both steps. Only automated tests and adversarial review catch these systematic errors.

## Top AI Regression Patterns

1. **Sandbox/production path mismatch:** Hardcoding paths that only exist in the development environment.
2. **SELECT clause omission:** Forgetting to update database selectors after schema changes.
3. **Error state leakage:** Failing to reset state or clean up artifacts after a failed operation.
4. **Optimistic update without rollback:** Changing local state before remote operations succeed, without recovery handlers.

---

## Test Strategy: Test-to-Reprove

Write tests for bugs that were found, not just for code that works. Once tested, a regression cannot recur.

1. **Reproduce first:** Every bug fix starts with a failing test (Red).
2. **Isolate:** Use mocks only for external dependencies. Keep logic tests as integrated as possible.
3. **Verify via Fresh Signal:** Run tests in a fresh shell after implementation to avoid context leakage.

## Eval-First Loop

1. Define capability eval and regression eval
2. Run baseline and capture failure signatures
3. Execute implementation
4. Re-run evals and compare deltas

> **Doc/writing verification:** Agent-document output (SKILL.md, AGENTS.md, CLAUDE.md) verifies via `uv run $SKILL_DIR/../skill-authoring/scripts/validate-deps.py lint` and `context-check`. Verify prose semantically via a Skeptic subagent. Agent-facing docs use [writing-for-agents](../writing-for-agents/SKILL.md). Human-facing proposals and PR bodies use [writing-for-humans](../writing-for-humans/SKILL.md). In both cases, run the blind evals with assertions withheld.

### Skill Trigger Verification (CI Tests vs Offline Evals)

Do not make LLM API calls in CI unit tests. Reconcile trigger verification via a strict two-tier architecture:

1. **Deterministic Regression Tests (CI Floor)**:
   - Zero model calls.
   - Run in `pytest` against historical transcript records stored in the trigger ledger.
   - Verifies that recorded session facts match expectations (`assert actual_invoked == should_trigger`).
2. **Offline Routing Probes (Skill Authoring Eval)**:
   - Run on demand when authoring or revising a skill `description`.
   - Send a mini-trajectory to a fast probe model. Include the system prompt with `<available_skills>`, the `root_goal`, and the `trigger_observation`.
   - Assert that model tool calls select or reject target skills across all ledger cases.

## Runtime Trace Fixtures

For testing invocation class behavior against live Codex surfaces (manual, not in CI). Fixture design and test procedure live in `tests/context-load-fixtures/README.md`.

---

## References

- [Sandbox testing patterns](references/sandbox-testing-patterns.md)
- [Eval-first development](references/eval-first-development.md)
- [Writing sub-skill](../writing-for-agents/SKILL.md) -- Verify document output via deterministic gates, Skeptic reviews, and blind evals.
