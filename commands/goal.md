---
name: goal
description: >-
  Autonomous Goal Convergence Loop command. Drives implementation to verified
  completion using Deterministic Floor (eval-gate) and Semantic Ceiling
  (code-review) gates.
arguments: objective
argument-hint: |-
  <objective> [max_loops=<N>] [topic_root=<path>]
allowed-tools:
  - Agent
  - Bash
  - Read
---

# Command: /goal

**Status:** Autonomous Convergence Loop Orchestrator

Drives a task to verified completion through an automated worker-evaluator convergence loop. Eliminates "hallucinated completion" and "vibe passing" by conditioning completion on the composite **Goal Gate**:

$$\text{Goal Attained} \iff (\text{Floor} = \text{PASS}) \land (\text{Semantic Score} \ge 8/10) \land (\text{Blocking Issues} = 0) \land (\text{SOT In Sync})$$

---

## CRITICAL ORCHESTRATOR CONSTRAINTS
1. **Subagent-First Execution**: The orchestrator never writes code or edits files directly. All work is dispatched to subagents.
2. **Pointer Passing**: Exchange file paths, never inline artifact contents.
3. **Strict Loop Bounding**: Default `max_loops=5`. If the Goal Gate does not pass within `max_loops`, halt and escalate to human with residual issues.
4. **Fast Deterministic Circuit-Breaker**: If the Deterministic Floor fails, loop back immediately to the worker. Do NOT waste tokens dispatching the semantic reviewer on broken builds or failing tests.

---

## WORKFLOW PHASES

### PHASE 0: INITIALIZATION & GATE SYNTHESIS
1. Resolve persistent workflow directory under `~/.pi/workflows/projects/{project-hash}/{topic}`:
   ```bash
   TOPIC="${TOPIC:-goal-$(date +%Y%m%d-%H%M%S)}"
   WORKFLOW_DIR=$(uv run skills/eval-gate/scripts/gate_generator.py resolve-dir --repo-root . --topic "$TOPIC")
   mkdir -p "$WORKFLOW_DIR/review"
   ```
2. Detect repository toolchain and synthesize the project-native unified gate runner:
   ```bash
   uv run skills/eval-gate/scripts/gate_generator.py generate-gate --repo-root . --topic "$TOPIC"
   ```
   *(Generates `$WORKFLOW_DIR/gate.json`, `$WORKFLOW_DIR/run_evals.py`, and `$WORKFLOW_DIR/ledger.json`)*
3. Run pre-implementation baseline check:
   ```bash
   uv run "$WORKFLOW_DIR/run_evals.py" > "$WORKFLOW_DIR/baseline.json" || true
   ```
4. Set `loop_count = 1`.

---

### PHASE 1: WORKER IMPLEMENTATION / REMEDIATION
Dispatch developer subagent:
```text
Agent tool (developer):
  description: "Execute goal work unit"
  prompt: |
    You are the implementation agent.
    Objective: [$objective]
    Loop Cycle: [loop_count]/[max_loops]
    Active Issues: [WORKFLOW_DIR]/issues.md (if exists)

    Task:
    - If loop_count == 1: Implement the required feature or bugfix cleanly.
    - If loop_count > 1: Fix every issue enumerated in [WORKFLOW_DIR]/issues.md.
    - Preserved Invariants: Never break items flagged under 'Preserved Invariants' in issues.md.
    - Follow Clean Architecture: domain logic must not import delivery/infra.
    - Ensure tests are refutable (assert actual behavior, not mock calls).
    - Keep design.md in sync if paths, interfaces, or schemas change.

    Return standard response:
    ## Summary
    ## Artifacts
    ## Route: continue
```

---

### PHASE 2: DETERMINISTIC FLOOR GATE (eval-gate)
Execute the consolidated project-native runner:
```bash
uv run "$WORKFLOW_DIR/run_evals.py" > "$WORKFLOW_DIR/report.json"
```
Parse exit code:
- **If exit code != 0 (`status: fail`)**:
  1. Update cumulative regression ledger and emit worker feedback with anti-thrashing alerts:
     ```bash
     uv run skills/eval-gate/scripts/gate_generator.py update-ledger \
       --ledger-path "$WORKFLOW_DIR/ledger.json" \
       --loop "$LOOP_COUNT" \
       --floor-status "fail" \
       --semantic-score 0 \
       --issues-file "$WORKFLOW_DIR/report.json" \
       --emit-feedback "$WORKFLOW_DIR/issues.md"
     ```
  2. Increment `loop_count = loop_count + 1`.
  3. If `loop_count > max_loops`, halt:
     > `Goal failed to converge: Deterministic Floor failing after [max_loops] cycles. Escalating to human.`
  4. Otherwise, loop back directly to **PHASE 1**. (Do NOT run Phase 3).
- **If exit code == 0 (`status: pass`)**:
  Proceed immediately to **PHASE 3**.

---

### PHASE 3: SEMANTIC CEILING AUDIT (code-review)
Dispatch the isolated Skeptic reviewer subagent:
```text
Agent tool (code-reviewer):
  description: "Crux semantic code review"
  prompt: |
    You are the Skeptic Reviewer.
    Objective: [$objective]
    Diff: git diff HEAD~1...HEAD (or working tree changes)
    Gate Specs: [WORKFLOW_DIR]/gate.json
    Deterministic Floor: PASSED (see [WORKFLOW_DIR]/report.json)

    Task:
    Evaluate the change strictly against the 3 Crux Invariants and atomic assertions:
    1. Epistemic Truth: Are tests real behavioral probes or paper tiger mocks?
    2. Ontological Truth: Any hardcoded test returns or empty exception swallows?
    3. Clean Architecture: Inward dependencies preserved? Boundary leaks? Design doc sync?

    Score 1-10 (Threshold >= 8). Drop all formatting/syntax nits.
    Write atomic assertion findings JSON to [WORKFLOW_DIR]/review/findings.json:
    [
      { "id": "SEM-01", "passed": true/false, "evidence": "file:line", "reasoning": "..." }
    ]
    Return standard response per skills/dynamic-workflow-wrapper/references/resp-format.md.
```

Grade atomic assertions deterministically:
```bash
uv run skills/eval-gate/scripts/gate_generator.py grade-assertions \
  --assertions "$WORKFLOW_DIR/gate.json" \
  --grader-results "$WORKFLOW_DIR/review/findings.json" \
  --output "$WORKFLOW_DIR/review/graded.json"
```

---

### PHASE 4: COMPOSITE GOAL GATE ARBITRATION
Execute the deterministic Goal Gate arbiter:
```bash
uv run skills/code-review/scripts/review_gate.py evaluate-goal-gate \
  --eval-report "$WORKFLOW_DIR/report.json" \
  --score [SEMANTIC_SCORE] \
  --findings-json "$WORKFLOW_DIR/review/findings.json" \
  [--sot-drift if flagged] > "$WORKFLOW_DIR/review/goal_verdict.json"
```

Update cumulative regression ledger and checkpoint:
```bash
uv run skills/eval-gate/scripts/gate_generator.py update-ledger \
  --ledger-path "$WORKFLOW_DIR/ledger.json" \
  --loop "$LOOP_COUNT" \
  --floor-status "pass" \
  --semantic-score [SEMANTIC_SCORE] \
  --git-commit "$(git rev-parse HEAD 2>/dev/null || echo '')" \
  --issues-file "$WORKFLOW_DIR/review/goal_verdict.json" \
  --emit-feedback "$WORKFLOW_DIR/issues.md"
```

Evaluate `goal_verdict.json`:
- **If `goal_attained == true`**:
  ```markdown
  ## Goal Attained
  - Objective: [$objective]
  - Total Cycles: [loop_count]
  - Deterministic Floor: PASS (100%)
  - Semantic Ceiling: [SEMANTIC_SCORE]/10
  - Invariants: Zero blocking violations, SOT in sync.
  - Checkpoint Commit: [best_commit]
  ```
  Terminate workflow with completion signal.
- **If `goal_attained == false`**:
  1. Feedback is already prepared in `"$WORKFLOW_DIR/issues.md"` with anti-thrashing invariant preservation alerts and Karpathy checkpoint reference.
  2. Increment `loop_count = loop_count + 1`.
  3. If `loop_count > max_loops`, halt:
     > `Goal convergence timed out after [max_loops] cycles. Remaining issues listed in [WORKFLOW_DIR]/issues.md.`
  4. Otherwise, loop back to **PHASE 1**.
