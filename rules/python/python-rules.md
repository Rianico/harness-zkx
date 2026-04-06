---
paths:
  - "pyproject.toml"
  - "requirements.txt"
  - "setup.py"
  - "**/*.py"
---

# Python Rules

You are operating in a Python codebase. Before proceeding with your task, review and apply these rules.

## Core Python Standards (80% Base)
- **Formatting:** Enforce PEP 8. Use `snake_case` for variables/functions, `CamelCase` for classes.
- **Typing:** Always use type hints (`def process(data: dict) -> str:`).
- **Immutability:** Do not use mutable default arguments (`def func(x=[]):` -> BAD).
- **Imports:** Group imports (Standard Library -> Third Party -> Local).

## Expertise Routing (Use `Skill` tool)
If your task requires complex decision making, you MUST pause and invoke the `Skill` tool for `python-expert` to retrieve the deep methodology:

- **Web Frameworks:** If working with Django or FastAPI, invoke `Skill(skill="python-expert", args="frameworks")`.
- **Machine Learning:** If working with PyTorch, invoke `Skill(skill="python-expert", args="pytorch")`.
- **Testing:** If writing comprehensive tests, default to `pytest` and invoke `Skill(skill="python-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not try to guess complex architectural patterns or deep framework mechanics. If the user asks for a complex Django security implementation, retrieve the skill first.
