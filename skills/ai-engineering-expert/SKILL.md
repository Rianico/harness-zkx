---
name: ai-engineering-expert
description: AI engineering expertise for designing skills, agents, workflows, evals, and regression tests in the LSZ architecture. TRIGGER when designing, refining, iterating, or redesigning a skill, workflow, agent, or command; structuring agent orchestration; defining tool boundaries, action spaces, observation formats, or error recovery contracts; eval-first execution, model routing, AI regression testing, bug-check workflows, sandbox/production mismatch tests, SELECT clause omission tests, error state leakage tests, or optimistic update rollback tests; OR user asks 'should this be a skill or command', 'is this the right granularity', 'how should I structure this workflow', 'what's the right action space', 'how do I make this trigger reliably', 'which model tier for this task', 'how do I test AI-generated code', 'how do I redesign this agent', 'help me iterate on this skill'.
---

# AI Engineering Expert

Core principles for building robust AI systems. Use this skill when designing or refining skills, agents, workflows, and orchestration patterns.

## Core Mental Model

AI system quality is constrained by four factors:

1. **Action space quality** — Can the agent express the right operations?
2. **Observation quality** — Does the agent see what it needs to decide?
3. **Recovery quality** — Can the agent handle errors gracefully?
4. **Context budget quality** — Is guidance loaded when needed, not before?

Skills that violate these constraints produce fragile agents that fail silently or exhaust context on irrelevant details.

## Quick Reference: Architecture & Process

**Team Operating Model**
- Planning quality > typing speed
- Eval coverage > anecdotal confidence
- Review focus: behavior and invariants, not style

**Eval-First Loop**
1. Define capability eval and regression eval
2. Run baseline, capture failure signatures
3. Execute implementation
4. Re-run evals, compare deltas

**Model Routing**
- Fast/cheap: classification, boilerplate, narrow edits
- Balanced: implementation, refactors, multi-file work
- Strong: architecture, root-cause analysis, complex invariants

**Session Strategy**
- Continue for closely-coupled units
- Fresh session after major phase transitions
- Compact at milestones, not during debugging

[Full details: eval-first-development.md](references/eval-first-development.md)

## Quick Reference: Harness Design

**Action Space Rules**
- Stable, explicit tool names
- Schema-first, narrow inputs
- Deterministic output shapes
- Avoid catch-all tools unless isolation impossible

**Observation Design**
Every tool response should include:
- `status`: success|warning|error
- `summary`: one-line result
- `next_actions`: actionable follow-ups
- `artifacts`: file paths / IDs

**Error Recovery**
Every error path needs:
- Root cause hint
- Safe retry instruction
- Explicit stop condition

[Full details: tool-design-contracts.md](references/tool-design-contracts.md)

## Quick Reference: Skill Authoring

**Required Frontmatter**
- `name`: Display name (lowercase, hyphens, max 64 chars)
- `description`: What + when, third-person, trigger vocabulary

**Key Optional Fields**
- `argument-hint`: Autocomplete hint like `[mode] <topic>`
- `allowed-tools`: Tool allowlist without permission prompts
- `model`: Override model (`opus`, `sonnet`, `haiku`, `inherit`)
- `effort`: Thinking level (`low`, `medium`, `high`, `xhigh`, `max`)

**Structure**
- SKILL.md under 500 lines
- Deep content in `references/` (one level deep)
- Executable logic in `scripts/`

**References:**
- [skill-frontmatter.md](references/skill-frontmatter.md) — Full frontmatter spec
- [skill-structure.md](references/skill-structure.md) — Directory layout, progressive disclosure
- [skill-description-patterns.md](references/skill-description-patterns.md) — Writing triggerable descriptions

## Quick Reference: Testing Patterns

**The Core Problem**
When the same AI writes and reviews code, it carries the same assumptions into both steps. Systematic blind spots emerge that only automated tests catch.

**Top Regression Patterns**
1. Sandbox/production path mismatch
2. SELECT clause omission
3. Error state leakage
4. Optimistic update without rollback

**Test Strategy**
Write tests for bugs that were found, not for code that works. AI tends to make the same category of mistakes repeatedly — once tested, that regression cannot happen again.

[Full details: sandbox-testing-patterns.md](references/sandbox-testing-patterns.md)

## Gotchas

- **Vague descriptions** — "Helps with documents" won't trigger. Use explicit trigger vocabulary.
- **Wrong POV** — "I can help you..." fails discovery. Always third-person.
- **Missing problem framing** — Description covers "design architecture" but misses "this code is a mess".
- **Overloading SKILL.md** — Keep under 500 lines. Move depth to references/.
- **Deep nesting** — References should be one level from SKILL.md. Nested references get partially read.
- **No validation loops** — Skills that do destructive work without self-checking produce silent failures.

## Skill Authoring Checklist

Before publishing a skill:

### Core Quality
- [ ] Description is third-person, specific, includes trigger terms
- [ ] Description includes both what AND when to use
- [ ] Methodology skills: Description covers all three trigger patterns (direct domain, problem framing, decision language)
- [ ] SKILL.md body under 500 lines / 5,000 tokens
- [ ] Reference files are one level deep from SKILL.md
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract

### Structure
- [ ] Frontmatter includes `name` and `description` (required)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks
