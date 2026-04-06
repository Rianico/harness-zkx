---
paths:
  - "**/*.rs"
  - "Cargo.toml"
---

# Rust Rules

You are operating in a Rust codebase. Before proceeding with your task, review and apply these rules.

## Core Rust Standards (80% Base)
- **Formatting:** Enforce `cargo fmt` and `cargo clippy`. 
- **Safety:** Use `unsafe` ONLY if absolutely necessary and explicitly document why.
- **Immutability:** Variables are immutable by default. Only use `mut` when state mutation is required.
- **Result/Option:** Always handle `Result` and `Option` explicitly (via `?`, `match`, `unwrap_or_else`). Do not use `.unwrap()` in production code.

## Expertise Routing (Use `Skill` tool)
If your task requires resolving build errors or making complex design decisions, you MUST pause and invoke the `Skill` tool for `rust-expert` to retrieve the deep methodology:

- **Build Resolution:** If fixing compiler/borrow-checker errors, invoke `Skill(skill="rust-expert", args="build")`.
- **Code Review:** If performing a PR or code review, invoke `Skill(skill="rust-expert", args="review")`.
- **Testing:** If writing comprehensive tests, invoke `Skill(skill="rust-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not randomly guess borrow checker fixes by adding `.clone()`. Retrieve the expert skill methodology first.
