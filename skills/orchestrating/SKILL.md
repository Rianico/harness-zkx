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
1. **Skill Execution, Not Bare Agents:** You MUST NOT invoke the `Agent` tool directly unless instructed by a specific skill's execution rules. Instead, load the phase skill via the `Skill` tool, then execute its workflow exactly as written.
2. **Sequential Execution:** You must execute the skills in the exact order specified by the pipeline.
3. **The "Executioner" Mindset (EDD):** The orchestrator never trusts a subagent's claim of completion. After implementation, you MUST execute the **Deterministic Gate** (`eval-gate`) and the **Semantic Audit** (`code-review`) to verify success via fresh environmental signals.
4. **Handoff-First State Passing**: Prioritize passing the `handoff_pointer` between skills. The `handoff.md` document acts as the high-signal "Mission Bridge" that distills intent and decisions.

5. **Interactive Approval Propagation:** By executing skills rather than bare agents, you naturally inherit their interactive approval loops. You MUST honor these user interaction prompts and handle user feedback exactly as defined in the skill's instructions before proceeding to the next step in the pipeline.
6. **Shared Topic Root:** For a multi-phase workflow on the same topic, create `[topic_root] = .lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]` once at the start of the workflow, then pass it downstream as an explicit `topic_root=<path>` override. Downstream workflow skills own their standalone defaults and MUST treat the orchestrated topic root as a caller override.
7. **Strict Phase Ownership:**
   - **Intent Locking:** Brainstorming and Architect phases lock the "What" and "Why".
   - **Empirical Execution:** TDD and Eval-gate phases prove the "How" works.
   - **Semantic Verification:** Code Review proves the "Intent Alignment" is preserved.
8. **No Redundant Re-encoding:** Do not ask a downstream phase to recreate an upstream artifact as a rewritten checklist, summary, or review unless that transformation is the explicit purpose of the phase.
9. **Topic-Root Source of Truth Exception:** `design.md` may live directly at `[topic_root]/design.md` because it is the mission-level source of truth, not a workflow-specific artifact directory. Workflow phase artifacts still belong under `[topic_root]/{workflow_kind}/` unless `artifact_dir=<path>` overrides them.
10. **Domain Context Injection:** When a phase skill's execution instructions require launching an agent or passing state, prepend concise domain context to the task prompt, then pass only approved upstream pointers relevant to that phase.
11. **Eval Gate (Deterministic Gate) Remediation:** After `eval-gate check`, parse the output routing decision:
    - `Route: continue` → Proceed to `code-review` (Semantic Audit)
    - `Route: remediate` → Invoke `tdd-cycle --lightweight issues=[issues_path] topic_root=[topic_root]`.
    - `Route: blocked` → Stop and surface blocker to user.
12. **Code Review (Semantic Audit) Remediation:** When `code-review` is the final phase, invoke it with `orchestrated_final_review=true`. Safe `medium`, `low`, or `minor` findings should be delegated for remediation without asking the user first. Ask for approval only when findings are `blocking`, `high`, security-critical, destructive, risky to fix, or require a product or architecture decision.

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

- **Checkpoint Handoff**: After Step 1 (Brainstorming) or Step 2 (Architect), generate a `handoff.md` in the current phase's artifact directory (e.g., `[topic_root]/brainstorming/handoff.md`).
- **Final Handoff**: At the end of the pipeline, generate a final `handoff.md` in the `review/` or `mission/` directory that serves as the summary and index of all durable artifacts.
- **Pointer Recovery**: If the orchestrator is invoked with a `handoff_pointer`, it MUST read the handoff to recover the `topic_root` and previous state before resuming the pipeline.

Use this prompt shape when injecting domain context:

```text
**[DOMAIN CONTEXT]**
Language/Domain: [e.g., Rust]
Root File: [e.g., Cargo.toml]

**[APPROVED UPSTREAM POINTERS]**
[Include only absolute file path pointers the next phase is expected to consume]

**[TASK]**
[Task summary and user requirements]
```

## Pipeline Flags and Routing

### Manual Override Flags
- `--lightweight`: Force lightweight pipeline (5-phase, skips architect + plan)
- `--heavy`: Force heavy pipeline (7-phase, full workflow)
- Default: Auto-detect from brainstorming complexity classification

### Routing Logic
After brainstorming completes:
1. Check for `--lightweight` or `--heavy` flag override
2. Otherwise, read complexity from design.md frontmatter or brainstorming return value
3. Route to 1a (heavy) or 1b (lightweight)

## Phase Ownership Contract (GDD)

- **`brainstorming` owns Intent Locking (BDD):** Requirement discovery, Given/When/Then scenarios (Intent Contract), success criteria, and complexity classification.
- **`architect` owns Architectural Decisions & High-Level Strategy:** Problem framing, boundaries, invariants, interfaces, ADRs, and high-level execution strategy (touched modules, migration needs).
- **`eval-gate define` owns Deterministic Spec (EDD):** Converting the approved Intent Contract into observable, script-based capability, contract, negative, and regression evals.
- **`tdd-cycle` owns Execution Planning & Implementation:** Vertical slicing. Phase 1 maps the BDD intent into an ordered **Behavior Sequence Map**. Phase 2 executes the Red-Green-Refactor loop.
- **`eval-gate check` owns the Deterministic Gate:** Running the EDD spec against the implementation and producing pass/fail logs based on environmental truth.
- **`code-review` owns the Semantic Audit:** Adversarial review (Skeptic) of architecture, intent alignment, and maintainability gaps not covered by deterministic scripts.

## Standard Pipelines

To execute a step, load the corresponding Skill (e.g., `skill="architect"`) and follow its execution contract.

### 0. Pre-implementation (Research & Reuse)
*Mandatory before any new implementation unless the task is a narrow bugfix with an already reproduced failure.*
- **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns.
- **Library docs second:** Use Context7 or vendor docs to confirm API behavior.
- **Search package registries:** npm, PyPI, crates.io, etc.
- **Tavity only when insufficient:** Use `websearch-tavity` skill for broader web research.
- Prefer adopting or porting a proven approach over writing net-new code.

### 1. Feature Pipeline (`args="feature|refactor"`)

**Step 1:** `brainstorming` (Load skill: `brainstorming`) - *Create `[topic_root]` once for the topic. The phase MUST produce `[topic_root]/design.md` and conclude by invoking the `handoff` skill to generate a `handoff_pointer`. Brainstorming returns complexity and the `handoff_pointer` in its structured response.*

**Routing Decision:** Check `--lightweight` or `--heavy` override flags. If no override, use complexity from brainstorming return value or design.md frontmatter. Route to 1a (heavy) or 1b (lightweight).

#### 1a. Heavy Track (complexity=heavy)

**5 additional phases**: architect → eval-gate define → tdd-cycle → eval-gate check → code-review

- **Step 2:** `architect` (Load skill: `architect`) - *Pass the `handoff_pointer` from brainstorming. records architectural decisions as ADRs and high-level execution strategy.*
- **Step 3:** `eval-gate define` (Load skill: `eval-gate`) - *Pass the current `handoff_pointer`. Defines the **EDD Deterministic Spec**.*
- **Step 4:** `tdd-cycle` (Load skill: `tdd-cycle`) - *Pass the current `handoff_pointer`. Maps BDD scenarios to an execution sequence and executes vertical implementation slices.*
- **Step 5:** `eval-gate check` (Load skill: `eval-gate`) - *The **Deterministic Gate**. Runs the EDD spec against the implementation.*
- **Step 6:** `code-review` (Load skill: `code-review`) - *The **Semantic Audit**. Adversarial review (Skeptic) of intent and architecture. Conclude with a final mission-summary handoff.*

#### 1b. Lightweight Track (complexity=lightweight)

**4 additional phases**: eval-gate define → tdd-cycle → eval-gate check → code-review

- **Step 2:** `eval-gate define` (Load skill: `eval-gate`) - *Defines the **EDD Deterministic Spec** from the Intent Contract.*
- **Step 3:** `tdd-cycle` (Load skill: `tdd-cycle`) - *Executes implementation.*
- **Step 4:** `eval-gate check` (Load skill: `eval-gate`) - *The **Deterministic Gate**.*
- **Step 5:** `code-review` (Load skill: `code-review`) - *The **Semantic Audit**.*

### 2. Bugfix Pipeline (`args="bugfix"`)
- **Step 1:** `tdd-cycle` (Load skill: `tdd-cycle`) - *Create `[topic_root]` once for the topic, execute vertical slices to fix the bug, and conclude with a handoff aggregation.*
- **Step 2:** `build-fix` (Load skill: `build-fix`) - *Execute ONLY IF the bug involves compilation/build failures.*
- **Step 3:** `eval-gate check` (Load skill: `eval-gate`) - *Run evals against the fix and conclude with a handoff summarizing readiness.*
- **Step 4:** `architect` escalation (Load skill: `architect`) - *Execute ONLY IF the bugfix changes architecture. Conclude with an updated handoff.*
- **Step 5:** `code-review` (Load skill: `code-review`) - *Pass the final `handoff_pointer` for the final repository review.*

### 3. Documentation Pipeline (`args="docs"`)
- **Step 1:** `update-docs` (Load skill: `update-docs`) - *Create `[topic_root]` once and conclude with a handoff pointing to the doc changes.*
- **Step 2:** `code-review` (Load skill: `code-review`) - *Pass the `handoff_pointer` for the final quality gate.*
