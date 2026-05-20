---
name: tdd-cycle
description: Execute a compact TDD workflow with strict RED, GREEN, and REFACTOR discipline. Use for test-first implementation, bug fixes, regression tests, failing-test-first development, minimal passing changes, refactoring under green tests, and implementation-level verification.
argument-hint: "<feature or module> [--lightweight] [issues=<path>|topic_root=<path>|artifact_dir=<path>]"
metadata:
  depends-on: [tdd-expert]
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
3. Generate a `short_topic` (lowercase, snake_case).
4. If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
5. Else if `topic_root=<path>` is provided by a caller or orchestrator, use `[topic_root]/tdd` as `[base_dir]`.
6. Otherwise create a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`, then use `[topic_root]/tdd` as `[base_dir]`.
7. Use the `Bash` tool to run: `mkdir -p [base_dir]`.
8. Reserve `[lineage_pointer]` as `[base_dir]/00-workflow-lineage.md`.
9. If lightweight mode: extract `issues=<path>` pointer as `[issues_pointer]`.

**Transition:**
- Lightweight mode → proceed immediately to Phase 2 (skip Phase 1).
- Full mode → proceed immediately to Phase 1.

---

## PHASE 1: TEST SPECIFICATION (Full Mode Only)
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (architect):
  description: "Derive executable test specification from approved design"
  prompt: |
    You are the Phase 1 agent. Consume the approved feature design and implementation plan for: [Feature], and derive an executable test specification for the TDD workflow. Focus on test scenarios, test boundaries, required fixtures, execution strategy, and any implementation constraints the RED+GREEN phase must honor. Only fill gaps in upstream artifacts when necessary to design the tests; do not perform a second broad feature-architecture pass. Also create or update the compact lineage artifact at [lineage_pointer] with: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases. You MUST use the Write tool to save the main artifact to [base_dir]/01-test-spec.md.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <what test scenarios were defined, key boundaries, tradeoffs made>

    ## Artifacts
    - [base_dir]/01-test-spec.md
    - [lineage_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**
1. Parse subagent response, extract artifact paths from `## Artifacts` section.
2. If `Route: blocked`, stop and surface issues to user.
3. If `Route: continue`, proceed immediately to Phase 2. DO NOT read the specification file yourself.

---

## PHASE 2: COMBINED RED + GREEN
**Action:** Call `Agent` tool
**Payload Template (Full Mode):**
```text
Agent tool (developer):
  description: "Write failing tests and implement minimal passing code"
  skill: tdd-expert
  prompt: |
    You are the combined RED+GREEN phase agent. Use the `tdd-expert` skill as the methodology for this phase, especially the smallest-failing-test discipline for RED and the minimum-passing-change discipline for GREEN. Read the specifications at [spec_pointer]. Work in two internal sub-phases. First perform RED: write FAILING unit tests for the feature, do NOT implement production code yet, and run the tests via Bash to verify they fail for the right reasons. Save a concise RED summary artifact to [base_dir]/02-failing-tests.md. Then perform GREEN: implement the MINIMAL production code needed to make those tests pass, do not add extra features, and rerun the smallest relevant test target first. When the change or observed fallout justifies it, you may also run broader or repo-wide test commands to verify that your implementation did not break shared behavior. All failure analysis, debugging, code edits, and test reruns stay inside this phase agent; do not push failure details back to the orchestrator for diagnosis. Save a concise GREEN summary artifact to [base_dir]/03-green-implementation.md. Also create or update the compact lineage artifact at [lineage_pointer] with separate entries for RED and GREEN, each containing: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <what tests were written, what was implemented, key tradeoffs>

    ## Artifacts
    - [base_dir]/02-failing-tests.md
    - [base_dir]/03-green-implementation.md
    - [lineage_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Payload Template (Lightweight Mode):**
```text
Agent tool (developer):
  description: "Write failing tests and fix enumerated issues"
  skill: tdd-expert
  prompt: |
    You are the combined RED+GREEN phase agent in lightweight mode. Use the `tdd-expert` skill as the methodology for this phase, especially the smallest-failing-test discipline for RED and the minimum-passing-change discipline for GREEN. Read the issues file at [issues_pointer] to understand what must be fixed. Work in two internal sub-phases. First perform RED: write FAILING unit tests that reproduce the enumerated issues, do NOT implement production code yet, and run the tests via Bash to verify they fail for the right reasons. Save a concise RED summary artifact to [base_dir]/02-failing-tests.md. Then perform GREEN: implement the MINIMAL production code needed to make those tests pass, do not add extra features, and rerun the smallest relevant test target first. All failure analysis, debugging, code edits, and test reruns stay inside this phase agent; do not push failure details back to the orchestrator for diagnosis. Save a concise GREEN summary artifact to [base_dir]/03-green-implementation.md. Also create or update the compact lineage artifact at [lineage_pointer] with separate entries for RED and GREEN, each containing: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <what tests were written, what issues were fixed, key tradeoffs>

    ## Artifacts
    - [base_dir]/02-failing-tests.md
    - [base_dir]/03-green-implementation.md
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

## PHASE 3: REFACTOR + EXTENDED VERIFICATION (Full Mode Only)
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (developer):
  description: "Refactor code and complete extended verification"
  skill: tdd-expert
  prompt: |
    You are the REFACTOR + EXTENDED VERIFICATION phase agent. Use the `tdd-expert` skill as the methodology for this phase, especially the refactor discipline of improving structure only with passing tests and preserving behavioral clarity in both code and tests. Read the implementation summary at [green_pointer]. Iterate internally until the invariant is satisfied or a clear failure is reached. Refactor the production code and test code to improve quality, remove duplication, and simplify structure while keeping behavior intact. Then perform the implementation-level verification needed for this change: rerun the smallest relevant test targets first, add or update integration tests, edge-case tests, or other non-unit checks when required by the approved spec and execution plan, and when the refactor or observed fallout justifies it, run broader or repo-wide test commands to verify shared behavior. Inspect failures, repair code or tests, and rerun until the implemented scope is verified or a clear blocker remains. All failure analysis, debugging, code edits, and test reruns stay inside this phase agent; do not push failure details back to the orchestrator for diagnosis. This phase owns implementation validation only; do not perform a broad repository-level review. Save the summary report to [base_dir]/04-refactor-and-verification.md. Also create or update the compact lineage artifact at [lineage_pointer] with: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases.

    **Return format per rules/templates/resp-format.md:**
    ## Summary
    <what was refactored, verification results, key tradeoffs>

    ## Artifacts
    - [base_dir]/04-refactor-and-verification.md
    - [lineage_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**
1. Parse subagent response, extract artifact paths from `## Artifacts` section.
2. If `Route: blocked`, stop and surface issues to user.
3. If `Route: continue`, output a final summary to the user listing all the pointers:
   - Lineage: `[lineage_pointer]`
   - Specification: `[spec_pointer]`
   - Failing Tests: `[red_pointer]`
   - Implementation: `[green_pointer]`
   - Refactor + Verification: `[verification_pointer]`
4. Terminate the workflow.

---

## Output Summary Format

**Full Mode:**
```text
TDD Cycle Complete
Mode: full
Lineage: [lineage_pointer]
Specification: [spec_pointer]
Failing Tests: [red_pointer]
Implementation: [green_pointer]
Refactor + Verification: [verification_pointer]
```

**Lightweight Mode:**
```text
TDD Cycle Complete
Mode: lightweight
Lineage: [lineage_pointer]
Failing Tests: [red_pointer]
Implementation: [green_pointer]
```
