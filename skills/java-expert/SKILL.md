---
name: java-expert
description: Deep expertise in Java, Spring Boot, architecture, and testing. Invoke this skill when instructed by the JVM rules for Java codebases.
argument-hint: "[frameworks|security|testing|build]"
---

# Java Expert Skill

You have invoked the Java Expert Skill. This skill contains actionable checklists and constraints for Java and Spring Boot software engineering tasks.

## Quick Actions & Checklists

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
2. If the task requires deep architectural knowledge, use the `Read` tool to fetch the relevant reference document from `skills/java-expert/references/`.
