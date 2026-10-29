---
paths:
  - "**/*.rs"
  - "Cargo.toml"
---

# Rust Rules

You are operating in a Rust codebase.

## Core Rust Standards (80% Base)

- **Formatting:** enforce `cargo fmt` and `cargo clippy`.
- **Safety:** use `unsafe` only when strictly necessary, and document why at the site.
- **Immutability:** variables are immutable by default. Use `mut` only when state mutation is required.
- **Result/Option:** always handle `Result` and `Option` explicitly (via `?`, `match`, `unwrap_or_else`). `.unwrap()` in production code is banned.

## Expertise Routing (Use `Read` tool)

`rust-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/rust-expert/SKILL.md` — borrow checker resolution rules, coding patterns, testing checklists
- `skills/programming-expert/subskills/rust-expert/references/` — rust patterns (error handling, traits, enums), testing (unit, integration, panic testing)

**CRITICAL:** Do not guess borrow checker fixes by adding `.clone()`. Read the expert methodology first.
