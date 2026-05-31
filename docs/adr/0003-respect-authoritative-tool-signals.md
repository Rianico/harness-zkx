# 3. Respect authoritative tool signals

Date: 2026-05-24

## Status

Accepted

implemented by [4. Goal-Driven Development (GDD) as Foundational Philosophy](0004-goal-driven-development-gdd-as-foundational-philosophy.md)

## Context

AI agents often ignore "minor" warnings or "style" diagnostics from tools like LSP servers, linters, and type checkers. This leads to silent failures, hidden regressions, and degraded code quality over time, especially in long-running or multi-agent missions where technical debt accumulates quickly.

## Decision

We will treat all automated tool feedback — including LSP diagnostics, type checker warnings, and linter errors — as authoritative signals. 

1. **Blockers, not suggestions**: A task is not considered "Done" until all diagnostics are resolved (fixed or intentionally suppressed).
2. **Mandatory Triage**: Every diagnostic must be triaged. Silent ignoring is a systemic failure.
3. **Justified Suppressions**: Suppressions are allowed but require a brief one-line justification explaining why the diagnostic is not applicable in that specific instance.

## Consequences

- **Higher Initial Cost**: Agents may spend more turns resolving "pedantic" issues up front.
- **Improved Long-term Stability**: Higher-fidelity codebases with fewer hidden bugs and clearer intent.
- **Authoritative Grounding**: Provides agents with a non-subjective success criterion for implementation work.
