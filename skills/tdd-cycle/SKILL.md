---
name: tdd-cycle
description: Execute a compact TDD workflow with strict RED, GREEN, and REFACTOR discipline. Use for test-first implementation, bug fixes, regression tests, failing-test-first development, minimal passing changes, refactoring under green tests, and implementation-level verification.
argument-hint: "<feature or module to implement> [--incremental|--suite] [--coverage 80] [topic_root=<path>|artifact_dir=<path>]"
---

# TDD Cycle Orchestration Skill

You are the Orchestrator. Your ONLY job is to dispatch the sub-agents defined below, evaluate their transition rules, and pass file pointers between them.

## CRITICAL BEHAVIORAL RULES FOR ORCHESTRATOR
1. **No Hero Mode:** You are strictly forbidden from using `Edit`, `Write`, or `Bash` tools to write code or fix tests yourself.
2. **Pointer Passing:** You MUST pass file paths (pointers) returned by one phase directly into the payload of the next phase. DO NOT use `Read` to read the code or diffs yourself.
3. **Strict Order:** Execute phases in exact order. This workflow is fully automatic and contains no user approval checkpoints.
4. **Halt on Failure:** If an agent reports an unexpected error or cannot satisfy its invariant within the retry budget, stop and surface the returned failure artifact to the user. Do not silently fix it, rerun tests, or debug the failure yourself.
5. **Bounded Internal Retries:** Each phase agent must iterate internally until its invariant is satisfied or a clear failure is reached, with a hard cap of 10 internal turns for that phase.
6. **Never enter plan mode autonomously:** Do NOT use `EnterPlanMode`. This file IS your strict execution plan.
7. **Compact Lineage Only:** Preserve auditability through a compact lineage artifact. Do not rehydrate all prior artifacts into later phases unless explicitly required.
8. **TDD Scope Only:** This workflow owns tests, implementation progress, and implementation-level verification only. It MUST NOT perform the broad repository-level review owned by `/code-review`.
9. **Failure Containment:** Phase-local debugging, repair, code edits, and test reruns stay inside the active phase subagent. The orchestrator must never absorb raw failure analysis or attempt its own recovery loop.

---

## PHASE 0: INITIALIZATION
**Action:** Prepare the workspace.
1. Extract the feature request from `$ARGUMENTS`.
2. Generate a `short_topic` (lowercase, snake_case).
3. If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
4. Else if `topic_root=<path>` is provided by a caller or orchestrator, use `[topic_root]/tdd` as `[base_dir]`.
5. Otherwise create a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]`, then use `[topic_root]/tdd` as `[base_dir]`.
6. Use the `Bash` tool to run: `mkdir -p [base_dir]`.
7. Reserve `[lineage_pointer]` as `[base_dir]/00-workflow-lineage.md`.

**Transition:** Once the directory is created, IMMEDIATELY proceed to Phase 1.

---

## PHASE 1: TEST SPECIFICATION
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (architect):
  description: "Derive executable test specification from approved design"
  prompt: |
    You are the Phase 1 agent. Consume the approved feature design and implementation plan for: [Feature], and derive an executable test specification for the TDD workflow. Focus on test scenarios, test boundaries, required fixtures, execution strategy, and any implementation constraints the RED+GREEN phase must honor. Only fill gaps in upstream artifacts when necessary to design the tests; do not perform a second broad feature-architecture pass. Also create or update the compact lineage artifact at [lineage_pointer] with: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases. You MUST use the Write tool to save the main artifact to [base_dir]/01-test-spec.md. Return a summary right before the absolute file path to the document. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 1 to complete and extract the file pointer (`[spec_pointer]`).
2. Proceed immediately to Phase 2. DO NOT read the specification file yourself.

---

## PHASE 2: COMBINED RED + GREEN
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (developer):
  description: "Write failing tests and implement minimal passing code"
  skill: tdd-expert
  prompt: |
    You are the combined RED+GREEN phase agent. Use the `tdd-expert` skill as the methodology for this phase, especially the smallest-failing-test discipline for RED and the minimum-passing-change discipline for GREEN. Read the specifications at [spec_pointer]. Work in two internal sub-phases with a hard cap of 10 internal turns total. First perform RED: write FAILING unit tests for the feature, do NOT implement production code yet, and run the tests via Bash to verify they fail for the right reasons. Save a concise RED summary artifact to [base_dir]/02-failing-tests.md. Then perform GREEN: implement the MINIMAL production code needed to make those tests pass, do not add extra features, and rerun the smallest relevant test target first. When the change or observed fallout justifies it, you may also run broader or repo-wide test commands to verify that your implementation did not break shared behavior. All failure analysis, debugging, code edits, and test reruns stay inside this phase agent; do not push failure details back to the orchestrator for diagnosis. Save a concise GREEN summary artifact to [base_dir]/03-green-implementation.md. Also create or update the compact lineage artifact at [lineage_pointer] with separate entries for RED and GREEN, each containing: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases. Return a summary right before the absolute file path to your final artifact pointer block. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow. In your final message, include both absolute file paths: [red_pointer] and [green_pointer]. If you cannot satisfy RED or GREEN within 10 internal turns, report a clear failure instead of guessing and ensure the failing phase artifact records the commands run, current failing scope, attempted fixes, and remaining blocker.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 2 to complete and extract both file pointers: `[red_pointer]` and `[green_pointer]`.
2. If the subagent reports failure to satisfy either invariant within the retry budget, stop, surface the returned failure artifact to the user, and do not rerun tests, debug, or edit code yourself.
3. Proceed automatically to Phase 3.

---

## PHASE 3: REFACTOR + EXTENDED VERIFICATION
**Action:** Call `Agent` tool
**Payload Template:**
```text
Agent tool (developer):
  description: "Refactor code and complete extended verification"
  skill: tdd-expert
  prompt: |
    You are the REFACTOR + EXTENDED VERIFICATION phase agent. Use the `tdd-expert` skill as the methodology for this phase, especially the refactor discipline of improving structure only with passing tests and preserving behavioral clarity in both code and tests. Read the implementation summary at [green_pointer]. Iterate internally until the invariant is satisfied or a clear failure is reached, with a hard cap of 10 internal turns. Refactor the production code and test code to improve quality, remove duplication, and simplify structure while keeping behavior intact. Then perform the implementation-level verification needed for this change: rerun the smallest relevant test targets first, add or update integration tests, edge-case tests, or other non-unit checks when required by the approved spec and execution plan, and when the refactor or observed fallout justifies it, run broader or repo-wide test commands to verify shared behavior. Inspect failures, repair code or tests, and rerun until the implemented scope is verified or a clear blocker remains. All failure analysis, debugging, code edits, and test reruns stay inside this phase agent; do not push failure details back to the orchestrator for diagnosis. This phase owns implementation validation only; do not perform a broad repository-level review. Save the summary report to [base_dir]/04-refactor-and-verification.md. Also create or update the compact lineage artifact at [lineage_pointer] with: phase name, invariant checked, result, artifact pointer, and any critical constraints for downstream phases. Return a summary right before the absolute file path to your summary report. Format: bullet list (≤100 words) if reporting status only; star rules (≤150 words) if encoding constraints or decisions the next agent must follow. If you cannot satisfy the invariant within 10 internal turns, report a clear failure instead of guessing and ensure the summary report records the commands run, current failing scope, attempted fixes, and remaining blocker.
```

**Transition Rules (Post-Execution):**
1. Wait for Phase 3 to complete and extract the file pointer (`[verification_pointer]`).
2. If the subagent reports failure to satisfy the invariant within the retry budget, stop, surface the returned failure artifact to the user, and do not rerun tests, debug, or edit code yourself.
3. Output a final summary to the user listing all the pointers:
   - Lineage: `[lineage_pointer]`
   - Specification: `[spec_pointer]`
   - Failing Tests: `[red_pointer]`
   - Implementation: `[green_pointer]`
   - Refactor + Verification: `[verification_pointer]`
4. Terminate the workflow.
