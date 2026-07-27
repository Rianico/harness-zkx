---
name: verification
description: >-
  EDD (Eval-Driven Development) methodology — deterministic vs semantic verification, AI regression patterns, test-to-reprove, eval-first loops, and environmental truth-seeking in the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Verification

Verification in LSZ is the process of seeking **Empirical Truth** through the environment to ensure the probabilistic model has achieved the human goal.

## The Foundation: EDD (Eval-Driven Development)

The auditor (Orchestrator or Verifier) is an **Executioner**, not a reader. We never trust the model's claim of completion; we only trust fresh signals generated *after* the implementation.

### 1. Deterministic Verification (Hard Gates)
Measured by non-LLM tools. These are binary, reliable, and cost zero tokens.
- **LSP & Linters:** Use `llm-lsp-cli` to check for diagnostics. A "finished" task must be clean of errors and warnings.
- **Unit & Property Tests:** Use `pytest`, `go test`, etc. These verify logic invariants that are mathematically or logically certain.
- **Differential Observation:** Compare output of old vs. new code against the same input. If they differ in a deterministic area, the implementation is failed.

### 2. Semantic Verification (Qualitative Alignment)
Measured by Adversarial Orchestration. We use LLMs to verify what compilers cannot: Intent.
- **The Skeptic Agent:** Dispatch a subagent with a "Skeptic" persona. Its only goal is to find "lazy code," "semantic drift," or "hallucinated implementation."
- **BDD Comparison:** Compare the final `code` against the **BDD Scenarios** locked in during brainstorming. Does the code *behave* like the scenario, or does it just look like it?
- **Explain-to-Verify:** Ask the model to explain how a specific complex block satisfies a BDD scenario. If the explanation fails to map to the code, reject the result.

---

## The Core Problem

When the same AI writes and reviews code, it carries the same assumptions into both steps. Systematic blind spots emerge that only automated tests and adversarial review catch.

## Top AI Regression Patterns

1. **Sandbox/production path mismatch:** Hardcoding paths that only exist in the development environment.
2. **SELECT clause omission:** Forgetting to update database selectors after schema changes.
3. **Error state leakage:** Failing to reset state or clean up artifacts after a failed operation.
4. **Optimistic update without rollback:** Changing local state/UI before a remote operation succeeds, without a way to revert on failure.

---

## Test Strategy: Test-to-Reprove

Write tests for bugs that were found, not just for code that works. AI tends to make the same category of mistakes repeatedly -- once tested, that regression cannot happen again.

1. **Reproduce first:** Every bug fix starts with a failing test (Red).
2. **Isolate:** Use mocks ONLY for external dependencies; keep logic tests as integrated as possible.
3. **Verify via Fresh Signal:** Run the test in a fresh shell after implementation to avoid context leakage.

## Eval-First Loop

1. Define capability eval and regression eval
2. Run baseline, capture failure signatures
3. Execute implementation
4. Re-run evals, compare deltas

## Runtime Trace Fixtures

For testing invocation class behavior against live Codex surfaces. See the context-load policy runtime trace fixture spec for fixture design and test procedure.

## References

[Sandbox testing patterns](references/sandbox-testing-patterns.md)
[Eval-first development](references/eval-first-development.md)
