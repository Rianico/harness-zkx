---
description: Build and Fix
argument-hint: "<optional_error_context>"
allowed-tools:
  - Agent
  - Bash
---

# Command: /build-fix

**Status:** JIT Workflow Command

Resolves build and compilation errors incrementally across any supported language by delegating to the `build-resolver` agent.

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or resolve the build errors yourself.
2. **Strict Order:** Execute phases in exact order.
3. **Halt on Failure:** If an agent reports an unexpected error, stop and ask the user. Do not silently fix it.
4. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.

---

## PHASE 1: RESOLVE BUILD ERRORS
**Action:** Call `Agent` tool
**Payload Template:**
```json
{
  "subagent_type": "build-resolver",
  "description": "Resolve build errors",
  "prompt": "**[DOMAIN CONTEXT]**\nLanguage/Domain: [Identify based on project]\nRoot File: [Identify based on project]\n\n**[TASK]**\nResolve the following build errors: [$ARGUMENTS]. Implement the fixes using your tools and ensure the build succeeds. Return a summary of the fixes applied."
}
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete.
2. Output a final summary to the user detailing the build fixes that were applied and terminate the workflow.
