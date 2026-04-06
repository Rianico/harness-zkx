---
name: python-expert
description: Deep expertise in Python frameworks (Django, FastAPI, PyTorch), testing, architecture, and security. Invoke this skill when instructed by the Python rules.
argument-hint: "[frameworks|pytorch|testing]"
---

# Python Expert Skill

You have invoked the Python Expert Skill. This skill contains the actionable checklists and constraints for Python software engineering tasks.

## Quick Actions & Checklists

### Django Development
- **Architecture:** Keep fat models, skinny views. Use DRF serializers for all API I/O.
- **ORM:** Use `select_related()` and `prefetch_related()` proactively to avoid N+1 queries.
- **Testing:** Default to `pytest-django`. Use `factory_boy` instead of fixtures.
- **Security:** Ensure `DEBUG=False` in prod. Use `@login_required` or DRF's `IsAuthenticated`.
> **Need Deep Knowledge?** Read `skills/python-expert/references/django-patterns.md` or `django-security.md`.

### PyTorch & Machine Learning
- **Tensors:** Explicitly manage device placement (`.to(device)`). Avoid unnecessary GPU<->CPU transfers.
- **Training:** Always use `model.train()` and `model.eval()`. Remember to `optimizer.zero_grad()`.
> **Need Deep Knowledge?** Read `skills/python-expert/references/pytorch-patterns.md`.

### Testing & Verification
- **Methodology:** Use Red-Green-Refactor. Test boundaries, not internal implementation details.
- **Mocks:** Use `unittest.mock` sparingly. Prefer testing with real databases/services via containers if possible.
> **Need Deep Knowledge?** Read `skills/python-expert/references/django-tdd.md` or `django-verification.md`.

## Instructions for the Agent
1. Based on the arguments you were given when invoking this skill, apply the relevant checklist above.
2. If the task is simple, proceed immediately.
3. If the task is complex or architectural, use the `Read` tool to fetch the relevant reference document from `skills/python-expert/references/` before modifying code.
