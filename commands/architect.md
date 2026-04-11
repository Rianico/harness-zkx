---
description: Interactive architectural design and review. Assesses system design against modern patterns (Clean Arch, DDD, Microservices).
argument-hint: "<task_description>"
allowed-tools:
  - Agent
  - AskUserQuestion
  - Bash
---

# Command: /architect

**Status:** JIT Workflow Command

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or design the architecture yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the artifacts yourself.
3. **Strict Order:** Execute phases in exact order. Stop at all Checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
5. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the architectural request from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. If `[topic_root]` was provided by an upstream orchestrator, reuse it. Otherwise create it once for this topic as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`.
4. Use the `Bash` tool to run: `mkdir -p [topic_root]/architect`
5. Store `[base_dir] = [topic_root]/architect` for this session.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: ARCHITECTURE DESIGN AND ANALYSIS
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "architect",
  "description": "Perform architectural design and analysis",
  "prompt": "You are the Architect agent. Analyze the requirements and design the architecture for: [$ARGUMENTS].\n\n**[DOMAIN CONTEXT]**\nLanguage/Domain: [Identify based on project]\nRoot File: [Identify based on project]\n\n**[Comprehensive Analysis]**\n[Already known information and analysis]\n\n**[TASK]**\nInclude the user's architectural request and constraints. Write your complete analysis, architectural proposal, diagrams, and trade-offs to a single markdown document. You MUST use the Write tool to save it to [base_dir]/01-architecture-proposal.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[proposal_pointer]`).
2. **CHECKPOINT 1:** You MUST stop and use `AskUserQuestion`. Use the strict schema:
```json
{
  "questions": [{
    "question": "Architectural design is ready. Please review the proposal at [proposal_pointer].",
    "header": "Architecture Review",
    "multiSelect": false,
    "options": [
      { "label": "Approve Design", "description": "Proceed with this architecture." },
      { "label": "Modify Design", "description": "Provide feedback to adjust components, patterns, or trade-offs." },
      { "label": "Reject & Exit", "description": "Discard the design and exit." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve Design**: Output a final summary with the `[proposal_pointer]` and terminate the workflow.
- If **Modify Design**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `architect` agent (do NOT resume the old one) using the payload from Phase 1, but explicitly pass `[proposal_pointer]` and the user's feedback in the prompt so the new agent can iterate on it and overwrite or save to `[base_dir]/02-architecture-proposal-revised.md` (return the new pointer). Then return to CHECKPOINT 1.
- If **Reject & Exit**: Acknowledge the rejection and exit the workflow.

**Usage:**
```bash
/architect "Design a microservice architecture for the new payment gateway"
/architect "Review our current src/ directory for Clean Architecture violations"
```