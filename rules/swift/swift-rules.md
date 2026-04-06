---
paths:
  - "**/*.swift"
  - "Package.swift"
---

# Swift Rules

You are operating in a Swift codebase. Before proceeding with your task, review and apply these rules.

## Core Swift Standards (80% Base)
- **Safety First:** Avoid forced unwrapping (`!`) unless logically guaranteed. Use `guard let` or `if let` to unwrap safely.
- **Immutability:** Use `let` by default. Only use `var` if the value must change.
- **Structs over Classes:** Default to `struct` for data models to get value semantics. Use `class` only when reference semantics or inheritance is required. Use `actor` for shared mutable state.
- **Formatting:** Adhere to standard Swift formatting (e.g., `swift-format`).

## Expertise Routing (Use `Skill` tool)
If your task requires advanced concurrency handling, SwiftUI architecture, or strict protocol-oriented testing, you MUST pause and invoke the `Skill` tool for `swift-expert` to retrieve the deep methodology:

- **Concurrency & State:** Invoke `Skill(skill="swift-expert", args="concurrency")`.
- **UI & SwiftUI:** Invoke `Skill(skill="swift-expert", args="swiftui")`.
- **Testing & DI:** Invoke `Skill(skill="swift-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not randomly guess solutions to "Sendable" warnings or actor isolation issues. Retrieve the expert skill methodology first.
