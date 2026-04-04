---
description: Invoke python-reviewer to do a code review for PEP 8 compliance, type hints, security, and Pythonic idioms. Invokes the python-reviewer agent.
---

# Python Code Review

This command invokes the **python-reviewer agent** to execute a comprehensive, **read-only** Python-specific code review by following below description.

## What This Command Does

1. **Stack Detection**: The agent analyzes `requirements.txt` or `pyproject.toml` to identify the project's frameworks (e.g., FastAPI, Django).
2. **Dynamic Skill Loading**: It uses the `Skill` tool to dynamically load relevant domain knowledge from the `python-development` plugin (e.g., `python-anti-patterns`, `python-design-patterns`, `async-python-patterns`).
3. **Static Analysis**: Executes `pyright` (preferred), `ruff`, `mypy`, `bandit`, and `pytest` if available.
4. **Code Analysis**: Evaluates modified `.py` files against the loaded best practices.
5. **Report Generation**: Returns a structured report to the main agent.
6. **Orchestration Handoff**: The main agent presents the findings to the user and confirm with user if delegate fixes to active development agents like `python-pro` or `tdd-guide`.

## When to Use

Use `/python-review` when:
- After writing or modifying Python code
- Before committing Python changes
- Reviewing pull requests with Python code
- Onboarding to a new Python codebase

## Review Categories

### CRITICAL (Must Fix)
- SQL/Command injection vulnerabilities
- Pickle unsafe deserialization & YAML unsafe load
- Hardcoded credentials
- Bare except clauses hiding errors

### HIGH (Should Fix)
- Missing type hints on public functions
- Mutable default arguments
- Swallowing exceptions silently
- Not using context managers for resources
- C-style looping instead of comprehensions
- Concurrency issues (shared state without locks)

### MEDIUM (Consider)
- PEP 8 formatting violations
- Missing docstrings on public interfaces
- Magic numbers without named constants
- Inefficient string operations

## Example Workflow

```text
User: /python-review

Main Agent: Spawning `python-reviewer`...

[Inside python-reviewer]:
1. Detects `fastapi` in requirements.txt.
2. Invokes `Skill` -> `python-development:python-design-patterns`.
3. Invokes `Skill` -> `python-development:python-anti-patterns`.
4. Analyzes code and generates report.

Main Agent:
Here is the review report from the python-reviewer:

# Python Code Review Report
...
[HIGH] Mutable default argument in `app/services.py:18`
...

Would you like me to fix these issues using the `python-pro` agent?

User: Yes, please fix the HIGH issues.

Main Agent: Spawning `python-pro` to apply the fixes...
```

## Integration with Other Agents

The `python-reviewer` is designed to work in tandem with the multi-agent `devfleet` architecture:
- **Read-Only**: The reviewer identifies issues and generates fixes in markdown, but never modifies code directly.
- **`python-pro` / `fastapi-pro`**: Use these active development agents to implement the fixes identified by the reviewer.
- **`tdd-guide`**: Use this agent to write missing tests flagged during the review.

## Related Ecosystem

The command heavily relies on the `python-development` plugin suite:
- Core Skills: `python-anti-patterns`, `python-code-style`, `python-type-safety`
- Domain Agents: `fastapi-pro`, `django-pro`
- Concept Skills: `async-python-patterns`, `python-testing-patterns`
