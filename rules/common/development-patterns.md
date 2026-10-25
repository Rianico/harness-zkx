# Development Patterns

## 1. Architecture & State
- **Immutable state:** Derive new values from inputs. Treat input data and original structures as read-only.
- **Pure core, impure shell:** Isolate I/O and side-effects at system boundaries. Keep core logic pure.
- **Typed boundaries:** Validate schemas at admission and emission boundaries. Route internal field access through typed models. `dict.get` and `Any` stop at the admission boundary.
- **Deep interfaces:** Expose simple, narrow public APIs that absorb internal complexity. If a wrapper only forwards arguments and spans five lines or fewer, merge it.

## 2. Guards & Errors
- **Fail loud:** Handle exceptions at each boundary. Map them to typed domain errors, or re-raise.
- **Narrow suppressions:** Treat lint and compiler suppressions as a baseline that only shrinks. Restrict each suppression to the narrowest line or scope. Record the reason inline.

## 3. Verification & Context
- **Proof before done:** Run the deterministic gates: tests, type checks, linters. Report completion only after a clean pass.
- **Counterexample proof:** Before you fix a bug claim or broken invariant, reproduce it with an executable minimal failing test.
- **Pointer-first context:** Exchange state through file paths and artifact links instead of inlined diffs or logs. Give each parallel writer its own isolated git worktree.
