---
description: Interactive workflow to sync project docs or generate architecture codemaps.
argument-hint: "[codemaps|project-docs|all]"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Bash
---

# Command: /update-docs

**Status:** JIT Workflow Command

Executes an interactive workflow to update project documentation (e.g., CONTRIBUTING.md, .env docs) or generate token-lean architectural codemaps.

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or update the documentation yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the artifacts yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the documentation target from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. Use the `Bash` tool to run: `mkdir -p .claude/ecc/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]/docs`
4. Store the resulting path as your `[base_dir]` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: UPDATE DOCUMENTATION
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "doc-updater",
  "description": "Update documentation",
  "prompt": "**[DOMAIN CONTEXT]**\nLanguage/Domain: [Identify based on project]\nRoot File: [Identify based on project]\n\n**[TASK]**\nUpdate documentation or generate codemaps based on the following target: [$ARGUMENTS]. You MUST use the Write tool to save a summary of the documentation changes to [base_dir]/01-doc-updates-summary.md. Return a brief summary (up to 100 words) right before the absolute file path to the document."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[docs_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "Documentation updates are ready. Please review the summary at [docs_pointer]. How would you like to proceed?",
    "header": "Docs Review",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Proceed with the updates." },
      { "label": "Request Changes", "description": "Provide feedback to adjust the documentation." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve**: Output a final summary with the `[docs_pointer]` and terminate the workflow.
- If **Request Changes**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `doc-updater` agent (do NOT resume the old one) using the payload from Phase 1, but explicitly pass `[docs_pointer]` and the user's feedback in the prompt so the new agent can iterate on it. Return to CHECKPOINT 1.
