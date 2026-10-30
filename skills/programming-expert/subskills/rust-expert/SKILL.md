---
name: rust-expert
description: >-
  Rust engineering guide: Cargo, borrow checker, lifetimes, traits, and async error handling. Use when implementing Rust code, fixing compiler/lifetime errors, writing tests, or refactoring ownership models.
argument-hint: |-
  [build|review|testing]
metadata:
  managed-by: programming-expert
---

# Rust Expert Skill

Checklists and constraints for Rust engineering tasks.

## Quick Actions & Checklists

### Build & Borrow Checker Resolution

- **Rule 1:** restructure borrows and lifetimes first. Keep `.clone()` as a last resort for borrow checker errors.
- **Rule 2:** analyze lifetime bounds. If `&'a` is missing, trace the struct instantiation.
- **Rule 3:** if the compiler suggests a trait bound (e.g. `T: Default`), evaluate whether the bound fits the architecture before applying it.
- **Rule 4:** use `cargo check` incrementally to verify fixes without paying the full `cargo build` cost.

### Coding Patterns

- **Error handling:** use the `?` operator and `Result` universally. Prefer `anyhow` for applications or `thiserror` for libraries.
- **Enums over booleans:** use `enum` for state machines instead of multiple boolean flags.
- **Concurrency:** prefer message passing (`mpsc`) or `RwLock` over `Mutex` where applicable.
- **Deep modules & narrow public API:** expose minimal `pub` items at crate/module boundaries. Keep internal machinery `pub(crate)` or private. The module absorbs locks, buffer pools, caching, and transaction boundaries behind a clean API.
- **Reject Classitis & over-abstraction:** avoid gratuitous single-method structs and deep trait hierarchies. Prefer cohesive functions and enum pattern matching over speculative OOP-style trait abstractions. Keep cohesive logic intact. Fragmenting algorithms into micro-helpers harms readability.
- **Design deepening vs. scope creep:** decomposing large modules into internal child modules (`mod internal;`) to cure God files is permitted design deepening. Never widen `pub` exports or cargo features without mandate.

> Deep dive: [rust-patterns.md](references/rust-patterns.md) — core principles, error handling, enums and pattern matching, traits and generics.

### Testing & Verification

- **Unit tests:** keep them in the same file inside a `#[cfg(test)]` module.
- **Integration tests:** place them in the `tests/` directory at the project root.
- **Mocks:** use traits for dependency injection to allow mocking in tests.
- **Refutation by counterexample & oracle testing:** supply concrete minimal failing inputs (`input -> expected vs observed`) when diagnosing defects. Verify state machines and combinatorial engines with small-input exhaustive tests or property-based tests (`proptest`).

> Deep dive: [rust-testing.md](references/rust-testing.md) — TDD workflow, unit and integration tests, error and panic testing.
