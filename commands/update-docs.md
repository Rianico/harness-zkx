---
description: Interactive workflow to sync project docs or generate architecture codemaps.
argument-hint: "[codemaps|project-docs|all] [topic_root=<path>|artifact_dir=<path>]"
allowed-tools:
  - Agent
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
3. If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
4. Else if `topic_root=<path>` is provided by a caller or orchestrator, use `[topic_root]/docs` as `[base_dir]`.
5. Otherwise create a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`, then use `[topic_root]/docs` as `[base_dir]`.
6. Use the `Bash` tool to run: `mkdir -p [base_dir]`.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: UPDATE DOCUMENTATION
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (doc-updater):
  description: "Update documentation"
  prompt: |
    **[DOMAIN CONTEXT]**
    Language/Domain: [Identify based on project]
    Root File: [Identify based on project]

    **[TASK]**
    Update documentation or generate codemaps based on the following target: [$ARGUMENTS]. You MUST use the Write tool to save a summary of the documentation changes to [base_dir]/01-doc-updates-summary.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[docs_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and present options to the user. Wait for their response before continuing:

---
**Docs Review**

Documentation updates are ready. Please review the summary at `[docs_pointer]`.

Options:
1. **Approve** — Proceed with the updates.
2. **Request Changes** — Provide feedback to adjust the documentation.
---

3. **Handle User Response:**
- If **Approve**: Output a final summary with the `[docs_pointer]` and terminate the workflow.
- If **Request Changes**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `doc-updater` agent (do NOT resume the old one) using the payload from Phase 1, but explicitly pass `[docs_pointer]` and the user's feedback in the prompt so the new agent can iterate on it. Return to CHECKPOINT 1.
