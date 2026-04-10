---
description: Interactive planner. Assesses risks and creates step-by-step implementation plans using AskUserQuestion for approval.
argument-hint: "<task_description>"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Bash
---

# Command: /plan

**Status:** JIT Workflow Command

Invokes the `planner` agent to create a comprehensive implementation plan before writing any code. Uses interactive prompts for approval.

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or write the plan yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the artifacts yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the planning request from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. Use the `Bash` tool to run: `mkdir -p .claude/ecc/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]/plan`
4. Store the resulting path as your `[base_dir]` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: GENERATE IMPLEMENTATION PLAN
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "planner",
  "description": "Generate implementation plan",
  "prompt": "You are the Planner agent. Generate a step-by-step implementation plan for: [$ARGUMENTS].\n\n**[DOMAIN CONTEXT]**\nLanguage/Domain: [Identify based on project]\nRoot File: [Identify based on project]\n\n**[PREVIOUS STATE / COMPREHENSIVE ANALYSIS]**\n[Include previous architecture/plan pointer if available, and any known analysis]\n\n**[TASK]**\nCreate a comprehensive implementation plan detailing the phases, tasks, files to create/modify, and risks. You MUST use the Write tool to save it to [base_dir]/01-implementation-plan.md. Return a brief summary (up to 100 words) right before the absolute file path to the document."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[plan_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "Implementation plan is ready. Please review the plan at [plan_pointer].",
    "header": "Plan Approval",
    "multiSelect": false,
    "options": [
      { "label": "Approve Plan", "description": "Proceed with the generated plan." },
      { "label": "Modify Plan", "description": "Provide feedback to adjust the phases or architecture." },
      { "label": "Reject & Exit", "description": "Discard the plan and exit." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve Plan**: Output a final summary with the `[plan_pointer]` and terminate the workflow.
- If **Modify Plan**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `planner` agent (do NOT resume the old one) using the payload from Phase 1, but explicitly pass `[plan_pointer]` and the user's feedback in the prompt so the new agent can iterate on it and overwrite or save to `[base_dir]/02-implementation-plan-revised.md` (return the new pointer). Then return to CHECKPOINT 1.
- If **Reject & Exit**: Acknowledge the rejection and exit the workflow.
