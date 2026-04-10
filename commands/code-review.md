---
description: Code Review Command. Assesses code quality, security, and maintainability.
argument-hint: "<optional_focus_area>"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Bash
---

# Command: /code-review

**Status:** JIT Workflow Command

Executes a universal code review workflow by delegating to the `code-reviewer` agent, followed by interactive resolution.

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or conduct the review yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the artifacts yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the code review focus from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. Use the `Bash` tool to run: `mkdir -p .claude/ecc/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]/review`
4. Store the resulting path as your `[base_dir]` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: CODE REVIEW
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "code-reviewer",
  "description": "Conduct code review",
  "prompt": "You are the Code Reviewer agent. Conduct a review focusing on: [$ARGUMENTS].\n\n**[DOMAIN CONTEXT]**\nLanguage/Domain: [Identify based on project]\nRoot File: [Identify based on project]\n\n**[PREVIOUS STATE POINTER]**\n[Include previous architecture/plan/implementation pointer if available]\n\n**[TASK]**\nReview the implementation for quality, security, and maintainability. You MUST use the Write tool to save your comprehensive review report to [base_dir]/01-code-review-report.md. Return ONLY the absolute file path to the document."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[review_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "Code review complete. Please review the report at [review_pointer]. How would you like to handle the findings?",
    "header": "Review Resolution",
    "multiSelect": false,
    "options": [
      { "label": "Approve & Continue", "description": "No blocking issues, proceed with the workflow." },
      { "label": "Delegate Fixes", "description": "Automatically fix the identified issues." },
      { "label": "Manual Fix", "description": "I will fix these manually." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve & Continue**: Output a final summary with the `[review_pointer]` and terminate the workflow.
- If **Delegate Fixes**: Launch the `tdd-cycle` skill (or appropriate agent) with the `[review_pointer]` to implement the fixes.
- If **Manual Fix**: Wait for the user to make changes, then they can re-run the review.
