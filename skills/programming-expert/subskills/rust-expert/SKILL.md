---
name: rust-expert
description: >-
  Rust domain expertise for Cargo builds, borrow checker errors, lifetimes, ownership, traits, generics, Result/error handling, async/concurrency, testing, mocks, and idiomatic review. For Rust implementation, debugging, testing, build resolution, performance refactoring, and ownership.
argument-hint: |-
  [build|review|testing]
metadata:
  managed-by: programming-expert
---

# Rust Expert Skill

You have invoked the Rust Expert Skill. This skill contains actionable checklists and constraints for Rust software engineering tasks.

## Quick Actions & Checklists

### Build & Borrow Checker Resolution
- **Rule 1:** DO NOT use `.clone()` as a first resort to fix borrow checker errors.
- **Rule 2:** Analyze lifetime bounds. If `&'a` is missing, trace the struct instantiation.
- **Rule 3:** If the compiler suggests a trait bound (e.g., `T: Default`), evaluate if the bound makes architectural sense before blindly applying it.
- **Rule 4:** Use `cargo check` incrementally to verify fixes without paying the full `cargo build` cost.

### Coding Patterns
- **Error Handling:** Use the `?` operator and `Result` universally. Prefer libraries like `anyhow` for applications or `thiserror` for libraries.
- **Enums over Booleans:** Use `enum` for state machines instead of multiple boolean flags.
- **Concurrency:** Prefer message passing (`mpsc`) or `RwLock` over `Mutex` where applicable.
- **Deep Modules & Narrow Public API:** Expose minimal `pub` items at crate/module boundaries; keep internal machinery `pub(crate)` or private. The module absorbs internal complexity (locks, buffer pools, caching, transaction boundaries) behind a clean API.
- **Reject Classitis & Over-Abstraction:** Avoid gratuitous single-method structs and deep trait hierarchies. Prefer cohesive functions and enum pattern matching over speculative OOP-style trait abstractions. Keep cohesive logic intact; do not fragment algorithms into micro-helpers if it harms readability.
- **Design Deepening vs. Scope Creep:** Decomposing large modules into internal child modules (`mod internal;`) to cure God files is permitted design deepening. Never widen `pub` exports or cargo features without mandate.
> **Need Deep Knowledge?** Read `$SKILL_DIR/references/rust-patterns.md`.

### Testing & Verification
- **Unit Tests:** Keep them in the same file inside a `#[cfg(test)]` module.
- **Integration Tests:** Place them in the `tests/` directory at the project root.
- **Mocks:** Use traits for dependency injection to allow mocking in tests.
- **Refutation by Counterexample & Oracle Testing:** Supply concrete minimal failing inputs (`input -> expected vs observed`) when diagnosing defects. Verify state machines and combinatorial engines with small-input exhaustive tests or property-based tests (`proptest`).
> **Need Deep Knowledge?** Read `$SKILL_DIR/references/rust-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "build", "testing", "review"), apply the relevant checklist above.
2. For deeper Rust patterns or testing guidance, use the `Read` tool to fetch the relevant reference document from `$SKILL_DIR/references/`.
