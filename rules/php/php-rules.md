---
paths:
  - "**/*.php"
  - "composer.json"
---

# PHP Rules

You are operating in a PHP/Laravel codebase. Before proceeding with your task, review and apply these rules.

## Core PHP Standards (80% Base)
- **Typing:** Use strict typing (`declare(strict_types=1);` at the top of files).
- **Type Hints:** ALWAYS use parameter type hints and return type declarations (`public function doSomething(string $param): bool`).
- **Formatting:** Follow PSR-12 coding standards.
- **Dependencies:** Use Composer for dependency management. Do not require libraries globally.

## Expertise Routing (Use `Skill` tool)
If your task requires Laravel architecture, complex Eloquent queries, security review, or TDD, you MUST pause and invoke the `Skill` tool for `php-expert` to retrieve the deep methodology:

- **Laravel Architecture:** Invoke `Skill(skill="php-expert", args="patterns")`.
- **Security:** Invoke `Skill(skill="php-expert", args="security")`.
- **Testing:** Invoke `Skill(skill="php-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not write legacy procedural PHP or raw SQL queries. Retrieve the expert skill methodology to use modern framework features.
