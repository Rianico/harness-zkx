---
description: Interactive planner. Assesses risks and creates step-by-step implementation plans with user approval at checkpoints.
argument-hint: "<task_description> [topic_root=<path>|artifact_dir=<path>]"
allowed-tools:
  - Agent
  - Bash
  - Write
---

# Command: /plan

**Status:** JIT Workflow Command

Invokes the `planner` agent to create a comprehensive implementation plan before writing any code. Uses interactive prompts for approval.

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the artifacts yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the planning request from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
4. Else if `topic_root=<path>` is provided by a caller or orchestrator, use `[topic_root]/plan` as `[base_dir]`.
5. Otherwise create a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`, then use `[topic_root]/plan` as `[base_dir]`.
6. Use the `Bash` tool to run: `mkdir -p [base_dir]`.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: GENERATE EXECUTION PLAN
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (planner):
  description: "Generate execution plan"
  prompt: |
    You are the Planner agent. Generate an execution plan for: [$ARGUMENTS].

    **[DOMAIN CONTEXT]**
    Language/Domain: [Identify based on project]
    Root File: [Identify based on project]

    **[APPROVED UPSTREAM STATE]**
    [Include previous architecture pointer if available, plus any known constraints]

    **[TASK]**
    Convert the approved architecture and user requirements into an execution plan only. The artifact MUST define: ordered implementation steps, files or modules expected to change, dependency sequencing, checkpoints, major risks, and explicit out-of-scope items. Keep it execution-oriented. Do NOT re-argue architecture choices, generate a broad architecture analysis, or produce a detailed test matrix or fixture specification unless the user explicitly asked for that. Write the artifact to [base_dir]/01-execution-plan.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[plan_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and present options to the user. Wait for their response before continuing:

---
**Plan Approval**

Implementation plan is ready. Please review the plan at `[plan_pointer]`.

Options:
1. **Approve Plan** — Proceed with the generated plan.
2. **Modify Plan** — Provide feedback to adjust the execution steps, sequencing, or scope boundaries.
3. **Reject & Exit** — Discard the plan and exit.
---

3. **Handle User Response:**
- If **Approve Plan**: Output a final summary with the `[plan_pointer]` and terminate the workflow.
- If **Modify Plan**: Ask the user what they want to change. Once they reply, invoke a **NEW** `planner` agent (do NOT resume the old one) using the payload from Phase 1, but explicitly pass `[plan_pointer]` and the user's feedback in the prompt so the new agent can iterate on it and overwrite or save to `[base_dir]/02-execution-plan-revised.md` (return the new pointer). Then return to CHECKPOINT 1.
- If **Reject & Exit**: Acknowledge the rejection and exit the workflow.
