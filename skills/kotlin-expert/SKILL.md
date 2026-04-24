---
name: kotlin-expert
description: Kotlin domain expertise for Android, Ktor, Exposed, Coroutines, Flow, structured concurrency, Gradle builds, Kotest, MockK, null-safety, extension functions, and idiomatic Kotlin design. Use for Kotlin implementation, debugging, testing, build resolution, coroutine design, Android/Ktor architecture, and refactoring tasks.
argument-hint: "[frameworks|coroutines|testing|build]"
---

# Kotlin Expert Skill

You have invoked the Kotlin Expert Skill. This skill contains actionable checklists and constraints for Kotlin software engineering tasks.

## Quick Actions & Checklists

### Idiomatic Kotlin Design
- **Null Safety:** Model absence with nullable types or sealed results instead of sentinel values.
- **Extensions:** Use extension functions for local readability, not to hide large behavior.
> **Need Deep Knowledge?** Read `skills/kotlin-expert/references/kotlin-patterns.md`.

### Kotlin Coroutines & Flow
- **Scope:** Never use `GlobalScope`. Use structured concurrency (e.g., `viewModelScope`, `lifecycleScope`, `coroutineScope`).
- **Dispatchers:** Explicitly inject dispatchers for testability (don't hardcode `Dispatchers.IO`).
- **Flow:** Use `StateFlow` for state, `SharedFlow` for events.
> **Need Deep Knowledge?** Read `skills/kotlin-expert/references/kotlin-coroutines.md`.

### Frameworks (Ktor & Exposed)
- **Ktor:** Use DSL routing. Extract complex logic into plugins or service classes.
- **Exposed:** Prefer DSL over DAO for complex queries. Always wrap DB calls in `transaction {}`.
> **Need Deep Knowledge?** Read `skills/kotlin-expert/references/kotlin-ktor.md` or `kotlin-exposed.md`.

### Testing (Kotest, MockK)
- **Mocks:** Use `MockK` instead of Mockito for proper coroutine and extension function mocking.
- **Async:** Use `runTest` from `kotlinx-coroutines-test` for suspending functions.
> **Need Deep Knowledge?** Read `skills/kotlin-expert/references/kotlin-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "frameworks", "coroutines", "testing"), apply the relevant checklist above.
2. For deeper Kotlin patterns, coroutine, framework, database, or testing guidance, use the `Read` tool to fetch the relevant reference document from `skills/kotlin-expert/references/`.
