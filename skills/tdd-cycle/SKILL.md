---
name: tdd-cycle
description: >-
  Orchestrates the TDD workflow (Red-Green-Refactor) using Vertical Slicing. Supports Full Mode (Design -> Implement -> Verify) and Lightweight Mode (Direct Fix). Accepts an optional [handoff_pointer] for seamless transitions from brainstorming.
argument-hint: |-
  <feature or module> [--lightweight] [handoff_pointer=<path>] [issues=<path>]
metadata:
  depends-on: [tdd-expert, handoff]
---

# TDD Cycle Orchestration Skill

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or fix tests yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the code or diffs yourself.
3. **Strict Order:** Execute phases in exact order. This workflow is fully automatic and contains no user approval checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error or cannot satisfy its invariant within the retry budget, stop and surface the returned failure artifact to the user. Do not silently fix it, rerun tests, or debug the failure yourself.
5. **Bounded Internal Retries:** Each phase agent must iterate internally until its invariant is satisfied or a clear failure is reached.
6. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.
7. **Compact Lineage Only:** Preserve auditability through a compact lineage artifact. Do not rehydrate all prior artifacts into later phases unless explicitly required.
8. **TDD Scope Only:** This workflow owns tests, implementation progress, and implementation-level verification only. It MUST NOT perform the broad repository-level review owned by `/code-review`.
9. **Failure Containment:** Phase-local debugging, repair, code edits, and test reruns stay inside the active phase subagent. The orchestrator must never absorb raw failure analysis or attempt its own recovery loop.

---

## Mode Selection

| Mode | Flag | Phases | Use Case |
|------|------|--------|----------|
| **Full** | (default) | 0 → 1 → 2 → 3 | New features, refactors, bugfixes |
| **Lightweight** | `--lightweight` | 0 → 2 | Eval remediation, targeted fixes with enumerated issues |

**Lightweight mode** skips Phase 1 (test spec derivation) and Phase 3 (refactor). It expects an `issues=<path>` pointer to a file enumerating specific issues to fix. Use this when issues are already identified (e.g., by eval-gate check).

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract arguments from `$ARGUMENTS`.
2. Detect mode: `--lightweight` flag present → lightweight mode, else full mode.
3. **Path Resolution**: 
   - If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
   - Else if `topic_root=<path>` is provided, use `.lsz/{date}/{topic}/tdd/run-1/` as `[base_dir]`.
   - Otherwise use a fresh timestamp-based root.
4. Use the `Bash` tool to run: `mkdir -p [base_dir]`.
5. Use the provided `lineage_pointer` or reserve as `[base_dir]/00-workflow-lineage.md`.
7. If lightweight mode: extract `issues=<path>` pointer as `[issues_pointer]`.

**Transition:**
- Lightweight mode → proceed immediately to Phase 2 (skip Phase 1).
- Full mode → proceed immediately to Phase 1.

---

## PHASE 1: BEHAVIOR SEQUENCE MAPPING (Full Mode Only)
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (architect):
  description: "Derive a behavior sequence map for iterative implementation"
  prompt: |
    You are the Phase 1 agent. Consume the approved design for: [Feature]. Your goal is to map out a sequence of observable behaviors that will be implemented using TDD.

    1. **BDD Alignment**: Review the **Behavioral Specification (BDD)** in the design. Use the Given/When/Then scenarios as the foundation for your implementation sequence.
    2. Identify the **Tracer Bullet**: The single most critical end-to-end behavior that establishes the public interface.
    3. Sequence remaining behaviors: Order them to build complexity incrementally, following the BDD scenarios.
    4. Define constraints: Note any architectural boundaries or performance targets that downstream phases must honor.

    Avoid writing actual test code or detailed test cases here. Focus on defining the *what* and the *order*. Create or update the compact lineage artifact at [lineage_pointer] with: phase name, result (the tracer bullet), and artifact pointer. You MUST use the Write tool to save the sequence map to [base_dir]/01-behavior-sequence.md.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <the identified tracer bullet and the logic behind the behavior sequence>

    ## Artifacts
    - [base_dir]/01-behavior-sequence.md
    - [lineage_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**
1. Parse subagent response, extract artifact paths from `## Artifacts` section.
2. If `Route: blocked`, stop and surface issues to user.
3. If `Route: continue`, proceed immediately to Phase 2.

---

## PHASE 2: ITERATIVE RED-GREEN-REFACTOR
**Action:** Call `Agent` tool
**Payload Template (Full Mode):**
```text
Agent tool (developer):
  description: "Implement behavior sequence using iterative Vertical Slices"
  skill: tdd-expert
  prompt: |
    You are the Phase 2 agent. Use the `tdd-expert` skill to implement the behavior sequence at [sequence_pointer].

    **CRITICAL MANDATE: VERTICAL SLICING ONLY.**
    Do NOT write all tests first. For each behavior in the sequence:
    1. **RED**: Write ONE failing test for that behavior.
    2. **GREEN**: Write the MINIMAL code to make that test pass.
    3. **REFACTOR**: Immediately clean up the code and tests while staying green.
    Repeat for the next behavior.

    All failure analysis, debugging, and micro-refactors stay inside this phase. When the implementation justifies it, run broader test targets to ensure no regressions. Save a concise summary of the implementation progress to [base_dir]/02-implementation-summary.md. Update the lineage artifact at [lineage_pointer] with entries for each major behavior milestone reached.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <how many behaviors were implemented, architectural decisions made during the loop, final status>

    ## Artifacts
    - [base_dir]/02-implementation-summary.md
    - [lineage_pointer]

    ## Route
    continue | blocked
```

**Payload Template (Lightweight Mode):**
```text
Agent tool (developer):
  description: "Fix enumerated issues using iterative Vertical Slices"
  skill: tdd-expert
  prompt: |
    You are the Phase 2 agent in lightweight mode. Use the `tdd-expert` skill to resolve the issues enumerated at [issues_pointer].

    **CRITICAL MANDATE: VERTICAL SLICING ONLY.**
    Do NOT write all tests first. For each issue identified:
    1. **RED**: Write ONE failing test that reproduces the issue.
    2. **GREEN**: Write the MINIMAL code to fix the issue and pass the test.
    3. **REFACTOR**: Immediately clean up the code and tests while staying green.
    Repeat for the next issue.

    All failure analysis, debugging, and micro-refactors stay inside this phase. When the implementation justifies it, run broader test targets to ensure no regressions. Save a concise summary of the fixes to [base_dir]/02-implementation-summary.md. Update the lineage artifact at [lineage_pointer] with entries for each issue resolved.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <how many issues were fixed, architectural decisions made during the loop, final status>

    ## Artifacts
    - [base_dir]/02-implementation-summary.md
    - [lineage_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**
1. Parse subagent response, extract artifact paths from `## Artifacts` section.
2. If `Route: blocked`, stop and surface issues to user.
3. Lightweight mode → output final summary and terminate (skip Phase 3).
4. Full mode → proceed automatically to Phase 3.

---

## PHASE 3: EXTENDED VERIFICATION (Full Mode Only)
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (developer):
  description: "Complete extended verification and final polish"
  skill: tdd-expert
  prompt: |
    You are the PHASE 3 agent. Your goal is to provide final verification for the implementation described in [implementation_pointer].

    1. **Edge Cases**: Identify and implement any remaining edge cases or boundary conditions not covered by the core behavior sequence.
    2. **Integration**: Run broader system-level or integration tests to ensure the new feature fits perfectly into the existing codebase.
    3. **Cleanup**: Perform a final pass on variable names, documentation, and test clarity.

    Save the summary report to [base_dir]/03-verification-report.md. Update the lineage artifact at [lineage_pointer] with the final verification result.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <verification results, any final minor adjustments, overall confidence>

    ## Artifacts
    - [base_dir]/03-verification-report.md
    - [lineage_pointer]

    ## Route
    continue | blocked
```

**Transition Rules (Post-Execution):**
1. Parse subagent response, extract artifact paths from `## Artifacts` section.
2. If `Route: blocked`, stop and surface issues to user.
3. If `Route: continue`:
   - **Mission Handoff**: Invoke the `handoff` skill with `artifacts=[design_pointer],[implementation_pointer],[verification_pointer]` to aggregate the final mission state.
   - **Final Summary**: Output the final summary listing all pointers, with the `handoff_pointer` as the primary bridge for any subsequent documentation or review phases.
4. Terminate the workflow.

---

## Output Summary Format

**Full Mode:**
```text
TDD Cycle Complete
Mode: full
Lineage: [lineage_pointer]
Sequence Map: [sequence_pointer]
Implementation: [implementation_pointer]
Verification: [verification_pointer]
```

**Lightweight Mode:**
```text
TDD Cycle Complete
Mode: lightweight
Lineage: [lineage_pointer]
Failing Tests: [red_pointer]
Implementation: [green_pointer]
```
