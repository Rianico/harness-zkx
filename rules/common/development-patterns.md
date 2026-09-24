# Development Patterns

## 1. Architecture & State
- **Immutable state:** New values from inputs; origins read-only.
- **Pure core, impure shell:** Keep I/O and side-effects at the outer edges. Core logic remains pure.
- **Typed boundaries:** Validate schemas at admission/emission. Trust typed models internally (no raw `dict.get` or `Any`).
- **Deep interfaces:** Expose simple, narrow public APIs hiding internal complexity. No 5-line pass-through wrappers.

## 2. Guards & Errors
- **Fail loud:** Explicitly handle, map to typed error, or re-raise. Zero empty catches.
- **Suppressions:** Shrink-only; narrowest possible line/scope with documented reason.

## 3. Verification & Context
- **Proof before done:** Deterministic tests, types, and linters must pass cleanly.
- **Counterexamples:** Claims of bugs or broken invariants require an executable minimal failing repro.
- **Context:** Pass file paths and artifact links, not raw diffs or logs. Parallel writers use isolated worktrees (e.g. via `wt` or git).
