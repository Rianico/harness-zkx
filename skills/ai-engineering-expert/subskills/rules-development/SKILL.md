---
name: rules-development
description: >-
  Rules design principles, rules vs skills boundary, and placement criteria for the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Rules Development

Designing rules that are concise, always-on, and context-efficient.

## Core Principle

Rules are always-on, skills are on-demand. Every token in a rule costs context every conversation.

## Rules vs Skills Boundary

| Rules | Skills |
|-------|--------|
| Always loaded | Loaded on demand |
| WHAT to use | HOW to implement |
| Personal taste, defaults | Non-obvious patterns |
| STATE, don't explain | Show examples |
| One-liner preferences | Framework gotchas |

## Rules Checklist

- [ ] Concise -- one line per rule, no justification
- [ ] Baseline only -- LLM already knows, you're setting YOUR default
- [ ] Stable -- rarely changes, settled decisions
- [ ] STATE -- declare preferences, don't explain why

## When to use rules:

- Tool/lib selection (`uv` over `pip`)
- Style defaults (`pytest -q`)
- Baseline patterns (type hints on all signatures)
- Personal taste that should always apply

## When to use skills:

- Non-obvious patterns (async event loop blocking)
- Framework gotchas (Django N+1 queries)
- Examples needed (PyTorch memory management)
- Architectural decisions (fat models, skinny views)

## Reference

[skill-authoring.md]($SKILL_DIR/../skill-authoring/references/skill-authoring.md) -- Full "Rules vs Skills Boundary" section with design principles, anti-patterns, and layered examples
