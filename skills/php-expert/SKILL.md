---
name: php-expert
description: Deep expertise in PHP, Laravel patterns, Eloquent ORM, security, and Pest/PHPUnit testing. Invoke this skill when instructed by the PHP rules.
argument-hint: "[patterns|security|testing]"
---

# PHP/Laravel Expert Skill

You have invoked the PHP/Laravel Expert Skill. This skill contains actionable checklists and constraints for PHP software engineering tasks.

## Quick Actions & Checklists

### Laravel Architecture & Eloquent
- **Controllers:** Keep controllers skinny. Move business logic to Action classes or Services.
- **Eloquent ORM:** Use Eager Loading (`with()`) proactively to avoid N+1 query problems.
- **Validation:** Always use Form Requests for complex validation logic instead of validating in the controller.
> **Need Deep Knowledge?** Read `skills/php-expert/references/laravel-patterns.md`.

### Security
- **Authentication:** Use built-in Laravel Auth scaffolding (Breeze/Jetstream) or Fortify.
- **Authorization:** Use Policies for resource-based authorization, not inline checks.
- **Mass Assignment:** Carefully configure `$fillable` or `$guarded` on models.
- **Injection:** Always use Eloquent or the query builder, which use parameter binding automatically.
> **Need Deep Knowledge?** Read `skills/php-expert/references/laravel-security.md`.

### Testing & Verification
- **Framework:** Prefer Pest over PHPUnit if available in the project, otherwise use PHPUnit.
- **Database:** Use `RefreshDatabase` trait to reset the DB state between tests.
- **Factories:** Use Model Factories heavily to generate test data instead of manual inserts.
> **Need Deep Knowledge?** Read `skills/php-expert/references/laravel-tdd.md` or `laravel-verification.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "patterns", "security", "testing"), apply the relevant checklist above.
2. If the task is architectural or complex, use the `Read` tool to fetch the relevant reference document from `skills/php-expert/references/`.
