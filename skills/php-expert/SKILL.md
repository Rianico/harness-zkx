---
name: php-expert
description: PHP and Laravel domain expertise for Laravel architecture, controllers, actions, services, Eloquent ORM, eager loading, Form Requests, Auth, Policies, mass assignment, Pest, PHPUnit, factories, and security. Use for PHP/Laravel implementation, debugging, testing, authorization, database, and refactoring tasks.
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
2. For deeper Laravel patterns, security, TDD, or verification guidance, use the `Read` tool to fetch the relevant reference document from `skills/php-expert/references/`.
