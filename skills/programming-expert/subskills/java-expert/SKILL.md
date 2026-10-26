---
name: java-expert
description: >-
  Java and Spring Boot expertise for layered services, Spring MVC/Security, Bean Validation, JPA, Maven/Gradle, JUnit 5/Mockito, integration testing, architecture review, and production hardening. Use for Java implementation, debugging, testing, build resolution, security, and Spring architecture.
argument-hint: |-
  [frameworks|security|testing|build]
metadata:
  managed-by: programming-expert
---

# Java Expert Skill

Checklists and constraints for Java and Spring Boot engineering tasks.

## Quick Actions & Checklists

### Java Coding Standards

- **Modern Java:** prefer clear domain types, immutable values where practical, and explicit null handling.
- **Collections & streams:** use streams when they improve readability. Keep imperative loops when they are clearer.

> Deep dive: [java-coding-standards.md](references/java-coding-standards.md) — naming, immutability, Optional usage, streams best practices.

### Spring Boot Architecture

- **Layers:** use `@RestController`, `@Service`, and `@Repository`. Keep controllers thin.
- **Dependency injection:** use constructor injection. Avoid `@Autowired` on fields.
- **Configuration:** prefer `@ConfigurationProperties` over `@Value`.

> Deep dive: [springboot-patterns.md](references/springboot-patterns.md) — REST API structure, repository and service layers, DTOs, exception handling.

### Security (Spring Security)

- **Auth:** always use Spring Security. Handle CSRF correctly.
- **Validation:** use `@Valid` and the Bean Validation API at the controller level.

> Deep dive: [springboot-security.md](references/springboot-security.md) — authentication, authorization, input validation, SQL injection prevention, password encoding.

### Testing (JUnit 5, Mockito)

- **Unit:** use JUnit 5 and Mockito.
- **Integration:** use `@WebMvcTest` for controller slicing and `@DataJpaTest` for repositories. Reserve `@SpringBootTest` for full E2E tests.

> Deep dive: [springboot-tdd.md](references/springboot-tdd.md) — TDD workflow, JUnit 5 + Mockito units, MockMvc web slices, DataJpaTest persistence. Full gate: [springboot-verification.md](references/springboot-verification.md) — five verification phases from build to security scan.
