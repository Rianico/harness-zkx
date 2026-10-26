---
paths:
  - "**/*.php"
  - "composer.json"
---

# PHP Rules

You are operating in a PHP/Laravel codebase.

## Core PHP Standards (80% Base)

- **Typing:** use strict typing (`declare(strict_types=1);` at the top of files).
- **Type hints:** always declare parameter type hints and return types (`public function doSomething(string $param): bool`).
- **Formatting:** follow PSR-12 coding standards.
- **Dependencies:** use Composer for dependency management. Do not require libraries globally.

## Expertise Routing (Use `Read` tool)

`php-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/php-expert/SKILL.md` — Laravel architecture, Eloquent, security (policies, mass assignment), Pest/PHPUnit testing
- `skills/programming-expert/subskills/php-expert/references/` — Laravel patterns, security hardening, TDD workflow, verification phases

**CRITICAL:** Do not write legacy procedural PHP or raw SQL queries. Read the expert methodology for modern framework features first.
