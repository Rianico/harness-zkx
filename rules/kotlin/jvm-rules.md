---
paths:
  - "**/*.kt"
  - "**/*.kts"
  - "**/*.java"
  - "build.gradle*"
  - "pom.xml"
---

# JVM (Kotlin/Java) Rules

You are operating in a Kotlin or Java codebase. Before proceeding with your task, review and apply these rules.

## Core JVM Standards (80% Base)
- **Null Safety:** In Kotlin, strictly leverage the nullable type system (`?`). Do not use `!!` unless mathematically proven safe. In Java, use `Optional` or `@Nullable`/`@NotNull` annotations.
- **Immutability:** In Kotlin, prefer `val` over `var` and immutable collections (`listOf`).
- **Data/Records:** Use Kotlin `data class` or Java 14+ `record` for DTOs and value objects.
- **Dependency Injection:** Favor constructor injection over field/setter injection.

## Expertise Routing (Use `Skill` tool)
If your task requires framework architecture, Coroutines, or complex build resolution, you MUST pause and invoke the `Skill` tool. 

First, determine if you are primarily working with Kotlin or Java, then invoke the appropriate expert skill:

**If working in Java (Spring Boot):**
- **Frameworks:** Invoke `Skill(skill="java-expert", args="frameworks")`.
- **Security:** Invoke `Skill(skill="java-expert", args="security")`.
- **Testing:** Invoke `Skill(skill="java-expert", args="testing")`.

**If working in Kotlin (Ktor, Android, Coroutines):**
- **Frameworks:** Invoke `Skill(skill="kotlin-expert", args="frameworks")`.
- **Coroutines:** Invoke `Skill(skill="kotlin-expert", args="coroutines")`.
- **Testing:** Invoke `Skill(skill="kotlin-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not randomly guess Spring Boot annotations or Coroutine scopes without loading the expert methodology first.
