---
name: swift-expert
description: >-
  Swift 6 guide: SwiftUI, async/await, actors, Sendable, strict concurrency, and XCTest. Use when implementing Swift features, debugging concurrency issues, building SwiftUI views, or fixing build errors.
argument-hint: |-
  [concurrency|swiftui|testing]
metadata:
  managed-by: programming-expert
---

# Swift Expert Skill

Checklists and constraints for Swift, iOS, and macOS engineering tasks.

## Quick Actions & Checklists

### Swift Concurrency (Swift 6 Strict Mode)

- **Async/await:** use `async`/`await`. Migrate away from legacy completion-handler closures.
- **Actors:** protect mutable state with `actor` or `@MainActor` for UI-bound state. Mark cross-task types `Sendable` and resolve every warning.
- **Tasks:** avoid unstructured concurrency (`Task { }`) unless bridging synchronous and asynchronous code. Prefer `TaskGroup` or `async let` for parallel operations.

> Deep dives: [swift-concurrency.md](references/swift-concurrency.md) — isolated conformances, global and static variables, `@concurrent` background work. [swift-actor-persistence.md](references/swift-actor-persistence.md) — actor persistence core pattern, design decisions, anti-patterns.

### SwiftUI Architecture & Patterns

- **State management:** use the `@Observable` macro (Swift 5.9+) over legacy `@StateObject`/`@ObservedObject` where possible.
- **Views:** keep views small. Extract complex logic into view models or domain objects.
- **Modifiers:** order modifiers logically — layout and framing before styling and background.

> Deep dive: [swiftui-patterns.md](references/swiftui-patterns.md) — state management, view composition, navigation, performance, previews.

### Testing & Protocol-Oriented Design

- **Dependency injection:** use protocols for all dependencies to allow easy mocking. Avoid singletons (`.shared`).
- **XCTest:** group tests logically. Use `setUpWithError` and `tearDownWithError` for test fixtures.
- **Async testing:** use `await` directly inside test methods. `XCTest` supports async test methods natively.

> Deep dive: [swift-protocol-di-testing.md](references/swift-protocol-di-testing.md) — protocol-based DI core pattern, best practices, anti-patterns.
