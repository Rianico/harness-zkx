---
description: Code Review Command. Assesses code quality, security, and maintainability.
argument-hint: "<optional_focus_area> [topic_root=<path>|artifact_dir=<path>]"
allowed-tools:
  - Agent
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

## ORCHESTRATED FINAL REVIEW MODE

If `$ARGUMENTS` includes `orchestrated_final_review=true`, this command is running as the final review phase of the `orchestrate` skill.

In this mode:
1. The review agent MUST classify findings by severity: `blocking`, `high`, `medium`, `low`, or `minor`, and MUST mark each finding as either safe to auto-remediate or requiring user approval because it is security-critical, destructive, risky, or product/architecture decision-requiring.
2. After Phase 1, derive the transition from the review agent's routing block. Treat `route: auto_remediate` as valid only when `blocking=0`, `high=0`, `requires_user_approval=false`, and every finding is safe, local, non-destructive `medium`, `low`, or `minor`; otherwise route to CHECKPOINT 1. Delegate valid auto-remediation findings to the Phase 2 remediation agent using `[review_pointer]`, then re-run Phase 1 once in post-remediation verification mode.
3. Ask the user only when findings are `blocking`, `high`, security-critical, destructive or risky to fix, or require product/architecture judgment.
4. If the second review still reports findings after delegated remediation, summarize the residual issues and ask the user whether to stop or approve one additional remediation pass. After one user-approved additional pass, stop with residual findings instead of continuing the loop.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the code review focus from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
4. Else if `topic_root=<path>` is provided by a caller or orchestrator, use `[topic_root]/review` as `[base_dir]`.
5. Otherwise create a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`, then use `[topic_root]/review` as `[base_dir]`.
6. Use the `Bash` tool to run: `mkdir -p [base_dir]`.

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
    Review the implementation at the repository level for security, maintainability, cross-cutting correctness gaps not already covered by the TDD workflow, and overall readiness. Classify every finding by severity: `blocking`, `high`, `medium`, `low`, or `minor`. For each finding, state whether it is safe to auto-remediate or requires user approval because it is security-critical, destructive, risky, or product/architecture decision-requiring. Include a routing block in your returned summary before the report path: `route: no_findings|auto_remediate|needs_user`, `counts: blocking=<n>, high=<n>, medium=<n>, low=<n>, minor=<n>`, `requires_user_approval: true|false`, and `approval_reasons: [...]`. Do NOT restate RED/GREEN/refactor progress, recreate implementation summaries, or rerun the internal TDD verification loop. If this is the initial review, you MUST use the Write tool to save your comprehensive review report to [base_dir]/01-code-review-report.md. If this is post-remediation verification mode, include the Phase 2 remediation summary and verification results in scope and save the verification review to [base_dir]/03-post-remediation-review-report.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[review_pointer]`).
2. If `$ARGUMENTS` includes `orchestrated_final_review=true` and Phase 1 is running in initial review mode, derive the transition from the returned routing block. If `route: no_findings`, output a final summary with `[review_pointer]` and terminate the workflow. If `route: auto_remediate` and `blocking=0`, `high=0`, `requires_user_approval=false`, and every finding is safe, local, non-destructive `medium`, `low`, or `minor`, skip CHECKPOINT 1 and proceed directly to Phase 2. Otherwise proceed to CHECKPOINT 1. If Phase 1 is running in post-remediation verification mode, do not auto-remediate again: terminate on `route: no_findings`; otherwise summarize the residual findings and ask the user whether to stop or approve one additional remediation pass. After one user-approved additional pass, stop with residual findings.
3. **CHECKPOINT 1:** You MUST stop and present options to the user unless the orchestrated final review rule above explicitly skips this checkpoint. Wait for their response before continuing:

---
**Review Resolution**

Code review complete. Please review the report at `[review_pointer]`.

Options:
1. **Approve & Continue** — No blocking issues, proceed with the workflow.
2. **Delegate Fixes** — Automatically fix the identified issues.
3. **Manual Fix** — I will fix these manually.
---

4. **Handle User Response:**
- If **Approve & Continue**: Output a final summary with the `[review_pointer]` and terminate the workflow.
- If **Delegate Fixes**: Delegate implementation of the findings to the Phase 2 remediation agent using the `[review_pointer]`, without treating `/code-review` itself as an internal TDD verification pass.
- If **Manual Fix**: Wait for the user to make changes, then they can re-run the review.

---

## PHASE 2: ORCHESTRATED REMEDIATION
**Action:** Call `Agent` tool only when orchestrated final review mode skips CHECKPOINT 1 for safe `medium`, `low`, or `minor` findings.
**Payload Template:**
```text
Agent tool (developer):
  description: "Fix review findings"
  prompt: |
    You are the remediation agent for the final `orchestrate` skill code review.

    **[REVIEW POINTER]**
    [review_pointer]

    **[TASK]**
    Fix only the safe `medium`, `low`, or `minor` findings in the review report. Do not address blocking, high-severity, security-critical, destructive, risky, or decision-requiring findings. Do not broaden scope beyond the review report. Preserve existing behavior except where the review report explicitly identifies a defect. Run the smallest relevant verification commands and report what changed.

    Return:
    1. A concise remediation summary
    2. Verification commands and results
    3. Any findings intentionally left unresolved and why
```

**Transition:** After Phase 2 completes, re-run Phase 1 once in post-remediation verification mode with the Phase 2 remediation summary and verification results in scope. If the second review has no findings, output the final summary and terminate. If it has residual findings, ask the user whether to stop or approve one additional remediation pass. After one user-approved additional pass, stop with residual findings instead of continuing the loop.
