# 15. Goal Gate and Convergence Loop Architecture for Autonomous Agent Sessions

Date: 2026-09-10

## Status

Accepted — Implements LSZ `Respect Tool Feedback` + `GDD Pillar 2 (EDD)` + `GDD Pillar 3 (Semantic vs. Deterministic Split)`.
Refines [ADR-0004](0004-goal-driven-development-gdd-as-foundational-philosophy.md) and [ADR-0009](0009-behavioral-evals-and-manifest-indexed-handoffs.md).

## Context

Autonomous multi-step execution (such as Codex `/goal` loops, Ralph loops, or graph engineering DAGs) requires an objective completion signal. Without an externalized, falsifiable verification boundary, agents suffer from:
1. **Hallucinated Completion**: The model asserts "task is finished" while compiler errors, failing tests, or unhandled failure modes persist.
2. **Vibes-Based Passing**: The model passes code based on superficial visual similarity rather than empirical proof.
3. **Rigid Tooling Coupling**: Previous `eval-gate` assumed single-stack hardcoded scripts (`npm`/`basedpyright`), failing in polyglot workspaces (Rust, TypeScript, Python, Go).
4. **Leaky Review Responsibility**: Previous `code-review` conflated language-specific diff grepping with qualitative semantic audit.

## Decision

We establish the **Goal Gate & Convergence Loop** architecture, decoupling verification into a **Deterministic Floor** and a **Semantic Ceiling**.

### 1. The Goal Gate Predicate
An autonomous session or graph node is complete if and only if the composite **Goal Gate** passes:

$$\text{Goal Attained} \iff (\text{Floor} = \text{PASS}) \land (\text{Semantic Score} \ge 8/10) \land (\text{Blocking Issues} = 0) \land (\text{SOT In Sync})$$

- **Deterministic Floor (`eval-gate`)**: Non-LLM binary execution in the real environment (compilation, static typing, test assertions, security checks).
- **Semantic Ceiling (`code-review`)**: Qualitative Skeptic audit of intent fidelity, refutability (no paper tigers), anti-laziness (no hardcoded returns), and Clean Architecture invariants (inward dependency rule).
- **SOT Sync ([ADR-0009](0009-behavioral-evals-and-manifest-indexed-handoffs.md))**: Any implementation changes to schemas, interfaces, or paths must be back-propagated as amendments to `design.md`.

### 2. Multi-Stack Gate Synthesis (`eval-gate`)
`eval-gate` is refactored into a **Stack-Aware Gate Generator**:
- **Stack Discovery**: Dynamically identifies project root markers (`Cargo.toml` for Rust, `package.json`/`tsconfig.json` for TypeScript, `pyproject.toml`/`uv.lock` for Python, `go.mod` for Go).
- **Dynamic Probe Synthesis**: Compiles high-level intent criteria into a consolidated executable runner (`run_evals.sh` or `run_evals.py`).
- **Unified Machine-Verifiable Output**: The runner outputs a single JSON schema with `status`, `score`, `criteria`, and `issues`.

### 3. Decoupled Semantic Review (`code-review`)
`code-review` is stripped of mechanical shell commands and regexes:
- Acts purely as high-level invariant policy and the **Skeptic** persona.
- Consumes `eval-gate`'s structured JSON output + diff + spec.
- Outputs structured verdict with route (`continue` | `remediate` | `blocked`).

### 4. Convergence Loop Mechanics
The loop runner (`/goal` or graph orchestrator) executes in cycles:
1. **Worker Iteration**: Subagent implements code or remediates issues.
2. **Floor Evaluation**: `eval-gate` runs native probes. If `FAIL`, issues list is written to `issues.md` and loop returns to Worker (saving tokens on LLM review).
3. **Ceiling Audit**: If Floor is `PASS`, `code-review` subagent audits diff. If score $< 8$ or blocking issues exist, findings append to `issues.md` and loop returns to Worker.
4. **Termination**: Loop exits on Goal Gate satisfaction or when `max_loops` (default: 5) is reached, triggering human escalation.

## Consequences

- **Polyglot Portability**: Works consistently across Rust, TypeScript, Python, and Go projects without manual script authoring.
- **Token Efficiency**: Cheap deterministic failures fail fast before invoking expensive semantic subagents.
- **Refutability**: Prevents paper tigers and mock tautologies from faking task completion.
