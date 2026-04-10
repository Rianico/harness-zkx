---
name: tdd-cycle-workflow
description: Execute a comprehensive TDD workflow with strict red-green-refactor discipline.
argument-hint: "<feature or module to implement> [--incremental|--suite] [--coverage 80]"
---

# TDD Cycle Orchestration Skill

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or fix tests yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the code or diffs yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the feature request from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. Use the `Bash` tool to run: `mkdir -p .claude/ecc/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]/tdd`
4. Store the resulting path as your `[base_dir]` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: TEST SPECIFICATION & DESIGN
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "architect",
  "description": "Analyze requirements and design test architecture",
  "prompt": "You are the Phase 1 agent. Analyze requirements and design test architecture for: [Feature]. Write your complete analysis, test scenarios, and architecture to a single markdown document. You MUST use the Write tool to save it to [base_dir]/01-spec-and-arch.md. Return a brief summary (up to 100 words) right before the absolute file path to the document."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[spec_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "Test specification and architecture complete. Please review the generated document at [spec_pointer].",
    "header": "Phase 1",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Proceed to RED phase" },
      { "label": "Request Changes", "description": "Adjust specifications before continuing" }
    ]
  }]
}
```
3. If approved, proceed to Phase 2. DO NOT read the specification file yourself.

---

## PHASE 2: RED (Write Failing Tests)
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "developer",
  "description": "Write failing tests for [Feature]",
  "prompt": "You are the RED phase agent. Read the specifications at [spec_pointer]. Write FAILING unit tests for the feature. DO NOT implement production code. Use the project's testing framework. Run the tests via Bash to verify they fail for the right reasons (missing implementation). Save a summary report of the failing tests to [base_dir]/02-failing-tests.md. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 2 to complete and extract the file pointer (`[red_pointer]`).
2. If the subagent reports that the tests PASS, the test is invalid. Re-dispatch Phase 2 to fix the test. Do NOT fix the test yourself.
3. **CHECKPOINT 2:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "RED phase complete. Tests are failing as expected. Review report at [red_pointer].",
    "header": "Phase 2",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Proceed to GREEN phase" },
      { "label": "Request Changes", "description": "Adjust tests before implementing" }
    ]
  }]
}
```
4. If approved, proceed to Phase 3.

---

## PHASE 3: GREEN (Make Tests Pass)
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "developer",
  "description": "Implement minimal code to make tests pass",
  "prompt": "You are the GREEN phase agent. Read the specifications at [spec_pointer] and the failing test summary at [red_pointer]. Implement MINIMAL production code to make the tests pass. Do not add extra features. Run the tests via Bash to verify they are all green. Save a summary report of the implementation to [base_dir]/03-green-implementation.md. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 3 to complete and extract the file pointer (`[green_pointer]`).
2. If the subagent reports that tests still FAIL, re-dispatch Phase 3 to fix the implementation. Do NOT fix the code yourself.
3. **CHECKPOINT 3:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "GREEN phase complete. All tests are passing. Review report at [green_pointer].",
    "header": "Phase 3",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Proceed to REFACTOR phase" },
      { "label": "Request Changes", "description": "Adjust implementation" }
    ]
  }]
}
```
4. If approved, proceed to Phase 4.

---

## PHASE 4: REFACTOR (Improve Code Quality)
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "developer",
  "description": "Refactor implementation and tests",
  "prompt": "You are the REFACTOR phase agent. Read the implementation summary at [green_pointer]. Refactor the production code and the test code to improve quality, remove duplication, and apply SOLID principles. You MUST run the tests via Bash after each change to ensure they remain green. Save a summary report of your refactoring to [base_dir]/04-refactor-summary.md. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 4 to complete and extract the file pointer (`[refactor_pointer]`).
2. **CHECKPOINT 4:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "REFACTOR phase complete. Code quality improved. Review report at [refactor_pointer].",
    "header": "Phase 4",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Proceed to Integration Testing" },
      { "label": "Request Changes", "description": "Adjust refactoring" }
    ]
  }]
}
```
3. If approved, proceed to Phase 5.

---

## PHASE 5: INTEGRATION & EXTENDED TESTING
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "e2e-runner",
  "description": "Write and implement integration/edge-case tests",
  "prompt": "You are the Integration phase agent. Read the refactored summary at [refactor_pointer]. Write integration tests, performance tests, and edge case tests for the feature. Implement any necessary integration code. Ensure all tests pass. Save a summary report to [base_dir]/05-integration-tests.md. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 5 to complete and extract the file pointer (`[integration_pointer]`).
2. Proceed to Phase 6.

---

## PHASE 6: FINAL REVIEW
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "code-reviewer",
  "description": "Final TDD cycle review",
  "prompt": "You are the Final Review agent. Perform a comprehensive review of the newly implemented feature. Verify TDD process adherence, code quality, and test coverage. Save your final review report to [base_dir]/06-final-review.md. Return a brief summary (up to 100 words) right before the absolute file path to your summary report."
}
```

**Transition Rules (Post-Execution):**
1. Output a final summary to the user listing all the pointers:
   - Specification: `[spec_pointer]`
   - Failing Tests: `[red_pointer]`
   - Implementation: `[green_pointer]`
   - Refactoring: `[refactor_pointer]`
   - Integration: `[integration_pointer]`
   - Final Review: (The path returned by Phase 6)
2. Terminate the workflow.