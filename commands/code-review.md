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

Executes a universal code review workflow by delegating to the `code-reviewer` agent, followed by interactive resolution. This command is the repository-level review gate for security, maintainability, cross-cutting correctness gaps, and overall readiness after implementation workflows such as `/tdd`.

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
3. If `[topic_root]` was provided by an upstream orchestrator, reuse it. Otherwise create it once for this topic as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`.
4. Use the `Bash` tool to run: `mkdir -p [topic_root]/review`
5. Store `[base_dir] = [topic_root]/review` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: CODE REVIEW
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (code-reviewer):
  description: "Conduct code review"
  prompt: |
    You are the Code Reviewer agent. Conduct a repository-level review focusing on: [$ARGUMENTS].

    **[DOMAIN CONTEXT]**
    Language/Domain: [Identify based on project]
    Root File: [Identify based on project]

    **[APPROVED UPSTREAM POINTERS]**
    [Include only the relevant approved implementation or verification pointers if available]

    **[TASK]**
    Review the implementation at the repository level for security, maintainability, cross-cutting correctness gaps not already covered by the TDD workflow, and overall readiness. Do NOT restate RED/GREEN/refactor progress, recreate implementation summaries, or rerun the internal TDD verification loop. You MUST use the Write tool to save your comprehensive review report to [base_dir]/01-code-review-report.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
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
- If **Delegate Fixes**: Delegate implementation of the findings to the appropriate implementation workflow using the `[review_pointer]`, without treating `/code-review` itself as an internal TDD verification pass.
- If **Manual Fix**: Wait for the user to make changes, then they can re-run the review.
