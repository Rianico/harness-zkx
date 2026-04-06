---
name: kotlin-expert
description: Deep expertise in Kotlin, Coroutines, Android, and Ktor. Invoke this skill when instructed by the JVM rules for Kotlin codebases.
argument-hint: "[frameworks|coroutines|testing|build]"
---

# Kotlin Expert Skill

You have invoked the Kotlin Expert Skill. This skill contains actionable checklists and constraints for Kotlin software engineering tasks.

## Quick Actions & Checklists

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
2. If the task requires deep architectural knowledge, use the `Read` tool to fetch the relevant reference document from `skills/kotlin-expert/references/`.
