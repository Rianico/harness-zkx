---
paths:
  - "**/*.kt"
  - "**/*.kts"
  - "**/*.java"
  - "build.gradle*"
  - "pom.xml"
---

# JVM (Kotlin/Java) Rules

You are operating in a Kotlin or Java codebase.

## Core JVM Standards (80% Base)

- **Null safety:** in Kotlin, use the nullable type system (`?`) strictly. `!!` requires mathematical proof of safety. In Java, use `Optional` or `@Nullable`/`@NotNull` annotations.
- **Immutability:** in Kotlin, prefer `val` over `var` and immutable collections (`listOf`).
- **Data/records:** use Kotlin `data class` or Java 14+ `record` for DTOs and value objects.
- **Dependency injection:** favor constructor injection over field/setter injection.

## Expertise Routing (Use `Read` tool)

`java-expert` and `kotlin-expert` are managed subskills of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file that matches your language directly:

- `skills/programming-expert/subskills/java-expert/SKILL.md` — Spring Boot layers, security, JUnit 5/Mockito testing, verification phases
- `skills/programming-expert/subskills/kotlin-expert/SKILL.md` — coroutines/Flow, Ktor, Exposed, Compose, MockK/runTest testing
- Both carry deeper material under their `references/` directories.

**CRITICAL:** Do not randomly guess Spring Boot annotations or Coroutine scopes. Read the expert methodology first.
