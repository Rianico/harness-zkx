---
name: php-expert
description: >-
  PHP and Laravel domain expertise: Laravel architecture, controllers, actions, services, Eloquent ORM, Form Requests, Auth/Policies, Pest/PHPUnit/factories, and security. For implementation, debugging, testing, authorization, database, and refactoring.
argument-hint: |-
  [patterns|security|testing]
metadata:
  managed-by: programming-expert
---

# PHP/Laravel Expert Skill

Checklists and constraints for PHP and Laravel engineering tasks.

## Quick Actions & Checklists

### Laravel Architecture & Eloquent

- **Controllers:** keep controllers skinny. Move business logic to Action classes or Services.
- **Eloquent ORM:** use eager loading (`with()`) proactively to avoid N+1 query problems.
- **Validation:** use Form Requests for complex validation logic instead of validating in the controller.

> Deep dive: [laravel-patterns.md](references/laravel-patterns.md) — controllers, actions, services, Eloquent usage.

### Security

- **Authentication:** use built-in Laravel Auth scaffolding (Breeze/Jetstream) or Fortify.
- **Authorization:** use Policies for resource-based authorization, not inline checks.
- **Mass assignment:** configure `$fillable` or `$guarded` deliberately on every model.
- **Injection:** use Eloquent or the query builder, which apply parameter binding automatically.

> Deep dive: [laravel-security.md](references/laravel-security.md) — core security settings, session/cookie hardening, auth and tokens, password security.

### Testing & Verification

- **Framework:** prefer Pest over PHPUnit when the project has it. Otherwise use PHPUnit.
- **Database:** use the `RefreshDatabase` trait to reset DB state between tests.
- **Factories:** use Model Factories to generate test data instead of manual inserts.

> Deep dives: [laravel-tdd.md](references/laravel-tdd.md) — Pest/PHPUnit TDD workflow. [laravel-verification.md](references/laravel-verification.md) — phased verification from composer and lint to tests and coverage.
