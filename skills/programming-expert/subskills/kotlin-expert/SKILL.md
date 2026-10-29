---
name: kotlin-expert
description: >-
  Kotlin domain expertise for Android, KMP, Compose, Ktor, and Coroutines. Use when implementing features, debugging coroutines, testing, or designing Compose UI architectures.
argument-hint: |-
  [frameworks|coroutines|testing|build|compose]
metadata:
  managed-by: programming-expert
---

# Kotlin Expert Skill

Checklists and constraints for Kotlin engineering tasks.

## Quick Actions & Checklists

### Idiomatic Kotlin Design

- **Null safety:** model absence with nullable types or sealed results instead of sentinel values.
- **Extensions:** use extension functions for local readability, not to hide large behavior.

> Deep dive: [kotlin-patterns.md](references/kotlin-patterns.md) — core principles, sealed classes and interfaces, scope functions.

### Kotlin Coroutines & Flow

- **Scope:** never use `GlobalScope`. Use structured concurrency (`viewModelScope`, `lifecycleScope`, `coroutineScope`).
- **Dispatchers:** inject dispatchers explicitly for testability.
- **Flow:** use `StateFlow` for state, `SharedFlow` for events.

> Deep dive: [kotlin-coroutines.md](references/kotlin-coroutines.md) — structured concurrency, Flow patterns, dispatchers, cancellation, testing.

### Frameworks (Ktor & Exposed)

- **Ktor:** use DSL routing. Extract complex logic into plugins or service classes.
- **Exposed:** prefer DSL over DAO for complex queries. Wrap DB calls in `transaction {}`.

> Deep dives: [kotlin-ktor.md](references/kotlin-ktor.md) — application structure, routing DSL, serialization, authentication, status pages. [kotlin-exposed.md](references/kotlin-exposed.md) — table definitions, DSL queries, database setup.

### Testing (Kotest, MockK)

- **Mocks:** use `MockK` instead of Mockito for coroutine and extension function mocking.
- **Async:** use `runTest` from `kotlinx-coroutines-test` for suspending functions.

> Deep dive: [kotlin-testing.md](references/kotlin-testing.md) — MockK and runTest examples.

### Compose & Compose Multiplatform

- **State:** ViewModel + `StateFlow` with `collectAsStateWithLifecycle`. One data class per screen.
- **Events:** sealed interface event sink over multiple callback lambdas for complex screens.
- **Navigation:** type-safe routes with `@Serializable` objects (Compose Navigation 2.8+). Pass lambdas, not `NavController`.
- **Performance:** `@Immutable` data classes, `key()` in lazy lists, `derivedStateOf` for derived reads.
- **KMP:** `expect`/`actual` for platform-specific composables.

> Deep dive: [kotlin-compose.md](references/kotlin-compose.md) — state management, navigation, composable design, KMP platform UI, performance.
