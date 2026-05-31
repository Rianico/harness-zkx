---
name: orchestrating
description: >-
  Orchestrate multi-step LSZ workflows for feature development, refactors, bug fixes, and documentation updates. Defines the skill sequence across brainstorming, architect, plan, eval-gate, TDD, build-fix, update-docs, and code-review, with approval checkpoints, shared topic roots, remediation loops, final review behavior, and pointer-based state passing. Supports lightweight (5-phase) and heavy (7-phase) pipelines with complexity-based routing.
argument-hint: >-
  [feature|refactor|bugfix|docs] [--lightweight|--heavy]
metadata:
  depends-on: [brainstorming, architect, eval-gate, tdd-cycle, code-review, build-fix, update-docs, handoff]
---

# Orchestration (GDD)

You have invoked the Orchestration Workflow Skill. This skill defines the strict sequence of LSZ skills to achieve **Human Goals** through **GDD (Goal-Driven Development)**. All boundaries, constraints, and remediation loops derive from the BDD/EDD/Semantic-Deterministic triad.

## Orchestration Rules
1. **Subagent-First Execution (Mandatory Delegation):** The orchestrator MUST NOT perform turn-intensive interactive phases (Brainstorming, Architect) or implementation work (TDD, Build-Fix) directly. You MUST dispatch a specialized subagent (e.g., `generalist`, `architect`, `developer`) and instruct it to load the relevant skill via the `Skill` tool. This preserves the orchestrator's context window and adheres to the "No Hero Mode" mandate.
2. **Sequential Execution:** You must execute the skills in the exact order specified by the pipeline.
3. **The "Executioner" Mindset (EDD):** The orchestrator never trusts a subagent's claim of completion. After implementation, you MUST **dispatch** the **Deterministic Gate** (`eval-gate`) and the **Semantic Audit** (`code-review`) subagents to verify success via fresh environmental signals. The orchestrator MUST NOT run verification commands (pytest, mypy, ruff, type checks) directly — that is the eval-gate's job.
4. **Manifest-Driven Execution (ADR-0007, ADR-0008, ADR-0009):**
   - **Initialization:** Create `[topic_root]/mission_manifest.json` after Step 1 (Brainstorming). Initialize with `intent_hash` (SHA-256 of `design.md`).
   - **Goal Locking (Pre-population):** BEFORE dispatching implementation, the orchestrator MUST pre-allocate the expected **Work Units** (BDD scenarios) in the mission manifest using `manifest-manager add-unit`.
   - **Observation Turns:** After each phase or implementation unit, the orchestrator MUST perform an "Observation Turn" using `eza` (verify artifact files exist) and `sha256sum` (verify file hashes match manifest). This is NOT verification of correctness — that is the eval-gate's job. Observation Turns only confirm artifacts are present and unmodified. **Environmental Truth (EDD) overrides any manifest claim.**
   - **Aggregated Hierarchy:** For IPS skills, record the path and hash of the `[skill]_manifest.json` in the mission manifest.
   - **Scripted Updates:** All updates MUST use the `uv run $SKILL_DIR/scripts/manifest-manager.py` script.
   - **Resume Logic:** Verify file hashes against the manifest using `sha256sum --check`.
5. **Manifest-Indexed Handoffs (Zero-Detail Handoffs):** The `handoff.md` acts as a **Mission Pointer**. It MUST NOT repeat technical decisions, file lists, or test results. It should only contain:
   - The high-level **Mission Goal**.
   - Pointer to **`mission_manifest.json`** for technical state and artifact index.
   - Pointer to **`design.md`** for intent and amended decisions.
6. **Interactive Approval Propagation:** When a subagent requires user approval or feedback, it should return control to the orchestrator with its current state. The orchestrator handles the user interaction and then re-dispatches the subagent (or a new one) with the user's input.
7. **Context Displacement & Compaction:** After a subagent returns from a turn-intensive phase (Brainstorming, Architect), the orchestrator SHOULD recommend that the user run the `/compact` command. **MANDATORY:** You MUST provide the user with the exact command to resume the pipeline, for example: "Mission state preserved. Run `/compact` to clear history, then call `orchestrating --pointer [handoff_path]` to resume Step 2."
8. **Sentinel Rule (Preventing "Hero Mode"):** If you find yourself in a session with minimal history but see evidence of an ongoing mission (e.g., a `.lsz/` directory, a `design.md` file, or a `mission_manifest.json`), you MUST NOT initiate implementation or changes yourself. Even if the user says "go ahead" or "continue", you MUST respond by asking for the `handoff_pointer` to re-initialize the orchestration state.
9. **Pointer-Based Recovery:** When invoked with a `handoff_pointer`, the orchestrator MUST:
   - Read the `handoff.md` at the pointer.
   - Read the `mission_manifest.json` referenced in the handoff.
   - Verify the current environment state against the manifest.
   - Summarize the recovered state to the user and confirm the next phase.
10. **Shared Topic Root & Versioned Runs (ADR-0010):**
   - Create `[topic_root] = .lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]` once at the start.
   - All phase artifacts MUST be stored in: `[topic_root]/[phase_id]/run-[N]/`.
   - The orchestrator calculates the next `run-[N]` by checking the `mission_manifest.json` using the `get-next-run` command.
   - Downstream skills MUST be invoked with `artifact_dir=[topic_root]/[phase_id]/run-[N]` to ensure immutable run history.
11. **Strict Phase Ownership:**
   - **Intent Locking:** Brainstorming and Architect phases lock the "What" and "Why".
   - **Empirical Execution:** TDD and Eval-gate phases prove the "How" works.
   - **Semantic Verification:** Code Review proves the "Intent Alignment" is preserved.
12. **No Redundant Re-encoding:** Do not ask a downstream phase to recreate an upstream artifact as a rewritten checklist, summary, or review unless that transformation is the explicit purpose of the phase.
13. **Topic-Root Source of Truth Exception:** `design.md` may live directly at `[topic_root]/design.md` because it is the mission-level source of truth, not a workflow-specific artifact directory. Workflow phase artifacts still belong under `[topic_root]/{workflow_kind}/run-[N]/` unless `artifact_dir=<path>` overrides them.
14. **Domain Context Injection:** When a phase skill's execution instructions require launching an agent or passing state, prepend concise domain context to the task prompt, then pass only approved upstream pointers relevant to that phase.
15. **Eval Gate (Deterministic Gate) Remediation:** After `eval-gate check`, parse the output routing decision:
    - `Route: continue` → Proceed to `code-review` (Semantic Audit)
    - `Route: remediate` → Increment run number and invoke `tdd-cycle --lightweight issues=[issues_path] topic_root=[topic_root] artifact_dir=[topic_root]/tdd/run-[N]`.
    - `Route: blocked` → Stop and surface blocker to user.
16. **Code Review (Semantic Audit) Remediation:** When `code-review` is the final phase, invoke it with `orchestrated_final_review=true`. Safe `medium`, `low`, or `minor` findings should be delegated for remediation without asking the user first. Ask for approval only when findings are `blocking`, `high`, security-critical, destructive, risky to fix, or require a product or architecture decision.

## Standard Return Format (The LSZ Contract)
Every phase execution (whether via Skill or Agent) MUST return a structured response for the orchestrator to parse:

```markdown
## Summary
<Carmack-style technical summary of what was done and why>

## Artifacts
- <absolute/path/to/artifact_1>
- <absolute/path/to/artifact_2>

## Route
continue | remediate | blocked
Issues:
- <brief issue summary if route is not continue>
```

## Phase Transitions and Handoffs
For complex missions where the agent's context may be reset (session end) or where a clean break between "Thinking" and "Doing" is required, the orchestrator MUST invoke the `handoff` skill.

- **Checkpoint Handoff**: After Step 1 (Brainstorming) or Step 2 (Architect), generate a `handoff.md` in the current phase's artifact directory (e.g., `[topic_root]/brainstorming/run-1/handoff.md`).
- **Final Handoff**: At the end of the pipeline, generate a final `handoff.md` at the root `[topic_root]/handoff.md` that serves as the summary and index of all durable artifacts.
- **Pointer Recovery**: If the orchestrator is invoked with a `handoff_pointer`, it MUST read the handoff to recover the `topic_root` and previous state before resuming the pipeline.
...
