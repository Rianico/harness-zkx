---
name: tdd-expert
description: >-
  TDD domain expertise for RED-GREEN-REFACTOR execution, failing tests first, test design, regression tests, behavior-focused assertions, refactoring discipline, incremental implementation, and test-first workflow review. Use when a workflow needs strict TDD rigor beyond a generic developer baseline.
argument-hint: >-
  [red|green|refactor|full-cycle]
---

# TDD Expert Skill

You have invoked the TDD Expert Skill. This skill provides reusable TDD methodology. It shapes how an agent reasons about RED, GREEN, and REFACTOR, but it does not own orchestration.

## Core TDD Stance: Vertical Slicing

**Never write all tests first, then all implementation (Horizontal Slicing).** This leads to fragile tests that are coupled to imagined implementation details.

- **Tracer Bullet**: Start with ONE test that confirms ONE end-to-end behavior through the public interface. This proves the path works.
- **Vertical Slices**: Iterate behavior by behavior. Write ONE failing test → implement MINIMAL code to pass → REFACTOR → Repeat.
- **Behavior Over Implementation**: Tests must verify what the system DOES, not how it works internally. If a refactor breaks a test but behavior is unchanged, the test is coupled to implementation.

## Design Principles

- **Deep Modules**: Prefer simple interfaces that hide complex implementations. Avoid "shallow modules" that force users to understand internal logic.
- **Interface First**: Design the public API for testability and clarity before diving into internals.
- **Red-Green-Refactor Loop**: 
  - **RED**: Write the smallest failing test for the next missing behavior.
  - **GREEN**: Make the smallest change to pass. Don't add speculative features.
  - **REFACTOR**: Improve structure only after behavior is protected by passing tests.

## RED Heuristics

- Start with the narrowest observable behavior that advances the feature.
- Prefer one failing reason at a time.
- Fail for the right reason: missing behavior, not broken setup.
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

### GREEN Checklist
- Did you only implement what the failing test required?
- Are all tests green?
- Did you avoid adding extra branches or options not required by tests?

## REFACTOR Heuristics

- Refactor only with passing tests.
- Remove duplication after behavior is protected.
- Improve names, boundaries, and structure.
- Extract abstractions only when duplication or coupling is now visible.
- **Refactor tests too**: Ensure they remain clear and readable as the code evolves.

### REFACTOR Checklist
- Did readability improve?
- Did duplication decrease?
- Are responsibilities clearer?
- Do tests still describe behavior clearly?
- Are all tests still green after each change?
