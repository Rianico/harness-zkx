---
name: tdd-workflow
description: Language-agnostic Test-Driven Development methodology. Enforces the Red-Green-Refactor loop, coverage requirements, and test strategy.
origin: ECC
---

# Test-Driven Development Workflow

This skill defines the pure, language-agnostic behavioral methodology for Test-Driven Development (TDD). It dictates the *what* and *when* of testing. 

For the *how* (syntax, frameworks, mocks), this skill must be combined with a language-specific testing skill (e.g., `python-testing`, `go-testing`, `typescript-testing`).

## The Core Philosophy: Tests BEFORE Code

You must strictly enforce the following state machine. You cannot move to the next state until the current state's requirements are met.

### State 1: RED (Write the Failing Test)
1. Define the API/Interface (scaffold the function/class signature).
2. Write a test that exercises the expected behavior.
3. **CRITICAL:** Run the test. It MUST fail. If it passes, the test is flawed or the code already existed.
4. Verify the test fails for the *expected* reason (e.g., "Not implemented" or "Assertion failed"), not a syntax/compilation error.

### State 2: GREEN (Make it Pass)
1. Write the *absolute minimum* implementation code required to make the test pass. Do not over-engineer.
2. Run the test. It MUST pass.
3. If it fails, fix the implementation until it passes.

### State 3: REFACTOR (Improve the Code)
1. With a passing test suite acting as a safety net, clean up the implementation.
2. Remove duplication, extract variables, improve naming, optimize performance.
3. Run the tests again. They MUST still pass.

### State 4: REPEAT (Next Scenario)
1. Move on to the next edge case, error path, or feature requirement.
2. Return to State 1.

## Test Strategy & Coverage

You must ensure that the test suite is comprehensive.

### 1. Test Types
*   **Unit Tests:** Test pure logic, algorithms, and individual functions in isolation. Mock external dependencies (DBs, APIs, Time).
*   **Integration Tests:** Test the boundaries. Does the repository actually write to the database? Does the API endpoint return the right HTTP status?
*   **E2E Tests:** (If applicable) Test the entire user journey.

### 2. Coverage Requirements (Minimum 80%)
You are responsible for driving coverage up to at least 80% (100% for critical paths like auth, financial math, or security).

Ensure the following scenarios are always tested:
*   **Happy Path:** The standard expected use case.
*   **Boundary Conditions:** Empty arrays/strings, 0, negative numbers, maximum values.
*   **Null/Undefined/Missing:** Omitted parameters or null inputs.
*   **Error Paths:** Network timeouts, invalid state, unauthorized access.

## Anti-Patterns to Avoid
*   **Implementation Testing:** Do not test *how* the code works (e.g., asserting internal variable states). Test *what* it does (inputs vs. outputs).
*   **Over-mocking:** Do not mock the system under test. Only mock external boundaries.
*   **Shared State:** Tests must be completely independent. Setup and teardown must isolate each test run.

## Agent Execution Guidelines

When operating as the `tdd-guide` agent:
1. Always announce which phase (RED, GREEN, REFACTOR) you are currently in.
2. Never write the implementation code in the same step/tool-call as the test.
3. Always execute the test runner via the `Bash` tool to prove the test state before proceeding.
