---
paths:
  - "**/*.swift"
  - "Package.swift"
---

# Swift Rules

You are operating in a Swift codebase.

## Core Swift Standards (80% Base)

- **Safety first:** avoid forced unwrapping (`!`) unless logically guaranteed. Use `guard let` or `if let` to unwrap safely.
- **Immutability:** use `let` by default. Use `var` only when the value must change.
- **Structs over classes:** default to `struct` for data models to get value semantics. Use `class` only when reference semantics or inheritance is required. Use `actor` for shared mutable state.
- **Formatting:** adhere to standard Swift formatting (e.g. `swift-format`).

## Expertise Routing (Use `Read` tool)

`swift-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/swift-expert/SKILL.md` — Swift 6 strict concurrency, SwiftUI architecture, protocol-oriented DI and testing
- `skills/programming-expert/subskills/swift-expert/references/` — concurrency patterns, actor persistence, SwiftUI patterns, protocol DI testing

**CRITICAL:** Do not guess solutions to `Sendable` warnings or actor isolation issues. Read the expert methodology first.
