---
name: tdd-expert
description: TDD domain expertise for RED-GREEN-REFACTOR execution, failing tests first, test design, regression tests, behavior-focused assertions, refactoring discipline, incremental implementation, and test-first workflow review. Use when a workflow needs strict TDD rigor beyond a generic developer baseline.
argument-hint: "[red|green|refactor|full-cycle]"
---

# TDD Expert Skill

You have invoked the TDD Expert Skill. This skill provides reusable TDD methodology. It shapes how an agent reasons about RED, GREEN, and REFACTOR, but it does not own orchestration.

## Core TDD Stance

- Write the smallest failing test that proves the next missing behavior.
- Make the smallest production change that turns the test green.
- Refactor only after behavior is protected by passing tests.
- Prefer one behavior increment at a time.
- Do not add speculative features while going green.
- Treat test design as design work, not just verification.

## RED Heuristics

- Start with the narrowest observable behavior that advances the feature.
- Prefer one failing reason at a time.
- Fail for the right reason: missing behavior, not broken setup.
- Avoid writing a giant test inventory before proving the first increment.
- Name tests in terms of behavior, not implementation details.
- If a test requires excessive fixture setup, treat that as design feedback.

### RED Checklist
- Is the test focused on one behavior?
- Does it fail for the expected reason?
- Is the failure message useful?
- Does it avoid coupling to incidental structure?
- Is the next production change obvious from the failure?

## GREEN Heuristics

- Add the smallest change that satisfies the failing test.
- Prefer direct code over premature abstraction.
- Do not solve future cases unless the current test requires it.
- Keep the implementation easy to reshape during refactor.
- If you feel pressure to build a framework, you are probably leaving GREEN too early.

### GREEN Checklist
- Did you only implement what the failing test required?
- Are all tests green?
- Did you avoid adding extra branches or options not required by tests?
- Is the code still easy to change in the next refactor step?

## REFACTOR Heuristics

- Refactor only with passing tests.
- Remove duplication after behavior is protected.
- Improve names, boundaries, and structure.
- Extract abstractions only when duplication or coupling is now visible.
- Prefer simpler boundaries and fewer responsibilities.
- If a refactor makes tests harder to understand, reconsider it.

### REFACTOR Checklist
- Did readability improve?
- Did duplication decrease?
- Are responsibilities clearer?
- Do tests still describe behavior clearly?
- Are all tests still green after each change?

## Test Design Guidance

### Good TDD Test Shapes
- Behavior-first unit tests for fast design feedback
- Narrow integration tests when behavior crosses a real boundary
- Edge-case tests only when the behavior contract requires them
- Regression tests when fixing a bug or preventing recurrence

### Avoid
- Snapshotting large structures when focused assertions would do
- Mocking everything by default
- Over-specifying call order or internals unless that is the behavior
- Writing the whole final suite before learning from the first red-green loop

## Design Signals TDD Should Surface

Signals of poor design:
- Tests require excessive setup for simple behavior
- Many mocks are needed just to reach the unit under test
- One small behavior requires touching many unrelated modules
- Test names drift into implementation details because behavior boundaries are unclear
- Green requires adding lots of code unrelated to the failing test

Recommended responses:
- simplify boundaries
- reduce dependency fan-out
- move logic toward a more testable core
- split responsibilities before adding more behavior

## Workflow Integration

Use this skill together with:
- a generic implementation agent for code changes
- a workflow prompt that defines current scope and artifact expectations

This skill should NOT:
- own user approvals
- define artifact storage layout
- replace workflow-specific constraints already owned by commands or orchestration skills
