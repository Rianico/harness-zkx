---
name: swift-expert
description: Swift domain expertise for Swift 6, SwiftUI, async/await, actors, Sendable, strict concurrency warnings, protocol-oriented design, XCTest, iOS, macOS, state management, and dependency injection. Use for Swift implementation, debugging, testing, concurrency fixes, SwiftUI architecture, and refactoring tasks.
argument-hint: "[concurrency|swiftui|testing]"
---

# Swift Expert Skill

You have invoked the Swift Expert Skill. This skill contains actionable checklists and constraints for Swift/iOS/macOS software engineering tasks.

## Quick Actions & Checklists

### Swift Concurrency (Swift 6 Strict Mode)
- **Async/Await:** Avoid legacy completion handlers (closures). Use `async`/`await`.
- **Actors:** Protect mutable state using `actor` or `@MainActor` for UI-bound state. Avoid unchecked `Sendable` warnings.
- **Tasks:** Avoid unstructured concurrency (`Task { }`) unless bridging synchronous and asynchronous code. Prefer `TaskGroup` or `async let` for parallel operations.
> **Need Deep Knowledge?** Read `skills/swift-expert/references/swift-concurrency.md` or `swift-actor-persistence.md`.

### SwiftUI Architecture & Patterns
- **State Management:** Use `@Observable` macro (Swift 5.9+) over legacy `@StateObject`/`@ObservedObject` where possible.
- **Views:** Keep views small. Extract complex logic into view models or domain objects.
- **Modifiers:** Order modifiers logically (e.g., layout and framing before styling and background).
> **Need Deep Knowledge?** Read `skills/swift-expert/references/swiftui-patterns.md`.

### Testing & Protocol-Oriented Design
- **Dependency Injection:** Use Protocols for all dependencies to allow for easy mocking. Avoid singletons (`.shared`).
- **XCTest:** Group tests logically. Use `setUpWithError` and `tearDownWithError` for test fixtures.
- **Async Testing:** Use `await` inside tests seamlessly; `XCTest` natively supports async test methods.
> **Need Deep Knowledge?** Read `skills/swift-expert/references/swift-protocol-di-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "concurrency", "swiftui", "testing"), apply the relevant checklist above.
2. If the task is complex, architectural, or requires resolving strict concurrency warnings, use the `Read` tool to fetch the relevant reference document from `skills/swift-expert/references/`.
