---
name: rust-expert
description: Rust domain expertise for Cargo builds, borrow checker errors, lifetimes, ownership, traits, generics, Result/error handling, async/concurrency, message passing, testing, mocks through traits, and idiomatic review. Use for Rust implementation, debugging, testing, build resolution, performance-sensitive refactoring, and ownership design tasks.
argument-hint: "[build|review|testing]"
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
> **Need Deep Knowledge?** Read `skills/rust-expert/references/rust-patterns.md`.

### Testing & Verification
- **Unit Tests:** Keep them in the same file inside a `#[cfg(test)]` module.
- **Integration Tests:** Place them in the `tests/` directory at the project root.
- **Mocks:** Use traits for dependency injection to allow mocking in tests.
> **Need Deep Knowledge?** Read `skills/rust-expert/references/rust-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "build", "testing", "review"), apply the relevant checklist above.
2. For deeper Rust patterns or testing guidance, use the `Read` tool to fetch the relevant reference document from `skills/rust-expert/references/`.
