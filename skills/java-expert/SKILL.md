---
name: java-expert
description: Java and Spring Boot domain expertise for layered services, Spring MVC, Spring Security, Bean Validation, JPA repositories, Maven/Gradle builds, JUnit 5, Mockito, integration testing, architecture review, and production hardening. Use for Java implementation, debugging, testing, build resolution, security, and Spring architecture tasks.
argument-hint: "[frameworks|security|testing|build]"
---

# Java Expert Skill

You have invoked the Java Expert Skill. This skill contains actionable checklists and constraints for Java and Spring Boot software engineering tasks.

## Quick Actions & Checklists

### Java Coding Standards
- **Modern Java:** Prefer clear domain types, immutable values where practical, and explicit null handling.
- **Collections & Streams:** Use streams when they improve readability; keep imperative loops when they are clearer.
> **Need Deep Knowledge?** Read `skills/java-expert/references/java-coding-standards.md`.

### Spring Boot Architecture
- **Layers:** Use `@RestController`, `@Service`, and `@Repository`. Keep controllers thin.
- **Dependency Injection:** Use constructor injection. Avoid `@Autowired` on fields.
- **Configuration:** Prefer `@ConfigurationProperties` over `@Value`.
> **Need Deep Knowledge?** Read `skills/java-expert/references/springboot-patterns.md`.

### Security (Spring Security)
- **Auth:** Always use Spring Security. Handle CSRF correctly.
- **Validation:** Use `@Valid` and Bean Validation API at the controller level.
> **Need Deep Knowledge?** Read `skills/java-expert/references/springboot-security.md`.

### Testing (JUnit 5, Mockito)
- **Unit:** Use JUnit 5 and Mockito.
- **Integration:** Use `@WebMvcTest` for controller slicing, `@DataJpaTest` for repositories. Avoid `@SpringBootTest` unless writing full E2E tests.
> **Need Deep Knowledge?** Read `skills/java-expert/references/springboot-tdd.md` or `springboot-verification.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "frameworks", "security", "testing"), apply the relevant checklist above.
2. For deeper Java standards, Spring architecture, security, testing, or verification guidance, use the `Read` tool to fetch the relevant reference document from `skills/java-expert/references/`.
