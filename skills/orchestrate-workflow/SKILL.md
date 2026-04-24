---
name: orchestrate-workflow
description: Orchestrate multi-step LSZ workflows for feature development, refactors, bug fixes, and documentation updates. Defines the command sequence across architect, plan, TDD, build-fix, update-docs, and code-review, with approval checkpoints, shared topic roots, and pointer-based state passing.
argument-hint: "[feature|refactor|bugfix|docs]"
---

# Orchestration Workflow Skill

You have invoked the Orchestration Workflow Skill. This skill defines the strict sequence of LSZ Commands you must execute to complete complex software engineering tasks.

## Orchestration Rules
1. **Command Execution, Not Bare Agents:** You MUST NOT invoke the `Agent` tool directly unless instructed by a specific Command's execution rules. Instead, you must load the Command's methodology via the `Skill` tool, then execute its workflow exactly as written.
2. **Sequential Execution:** You must execute the commands in the exact order specified by the pipeline.
3. **Pointer-Based State Passing:** Pass approved artifact pointers between commands instead of restating prior artifacts in prose. Each downstream phase should receive only the upstream pointers it is expected to consume.
4. **Interactive Approval Propagation:** By executing Commands rather than bare agents, you naturally inherit their `AskUserQuestion` interactive approval loops. You MUST honor these UI prompts and handle user feedback exactly as defined in the Command's instructions before proceeding to the next step in the pipeline.
5. **Shared Topic Root:** For a multi-phase workflow on the same topic, create `[topic_root] = .lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]` once at the start of the workflow, then pass and reuse that same `[topic_root]` across downstream commands. Later phases MUST create only their workflow-specific subdirectory under the existing topic root.
6. **Strict Phase Ownership:** Preserve distinct responsibilities across phases. Architect defines decisions and boundaries. Plan defines execution order and scope. TDD defines tests and implementation validation. Code review defines repository-level review and readiness.
7. **No Redundant Re-encoding:** Do not ask a downstream phase to recreate an upstream artifact as a rewritten checklist, summary, or review unless that transformation is the explicit purpose of the phase.

## Standard Pipelines

To execute a step, load the corresponding Skill (e.g., `skill="architect"`) and follow its "Execution Instruction" section.

### 0. Pre-implementation (Research & Reuse)
*Mandatory before any new implementation unless the task is a narrow bugfix with an already reproduced failure.*
- **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns.
- **Library docs second:** Use Context7 or vendor docs to confirm API behavior.
- **Search package registries:** npm, PyPI, crates.io, etc.
- **Tavity only when insufficient:** Use `websearch-tavity` skill for broader web research.
- Prefer adopting or porting a proven approach over writing net-new code.

### 1. Feature Pipeline (`args="feature|refactor"`)
- **Step 1:** `brainstorming` (Load skill: `brainstorming`) - *Create `[topic_root]` once for the topic. The phase MUST produce `[topic_root]/design.md` as the source of truth before implementation. The design must include understanding summary, assumptions, non-functional requirements, decision log, behavior specification, output examples or golden examples, negative requirements, acceptance criteria, and open questions.*
- **Step 2:** `/architect` (Load skill: `architect`) - *Pass the approved `design.md` pointer and existing `[topic_root]`. This phase records the architecture decision for feature/refactor work as an ADR. It must preserve the design contract and record trade-offs, boundaries, invariants, and rejected alternatives only.*
- **Step 3:** `/plan` (Load skill: `plan`) - *Pass the approved `design.md`, approved ADR pointer, and existing `[topic_root]`. This phase converts the design and ADR into an execution plan without weakening or reinterpreting acceptance criteria.*
- **Step 4:** `/eval define` - *Pass the approved `design.md`, ADR, execution plan, and existing `[topic_root]`. The eval definition must be derived from `design.md`, include concrete capability checks, regression checks, negative requirements, and golden examples where present, then stop for explicit user review and approval before implementation begins.*
- **Step 5:** Load skill: `tdd-cycle` - *Pass the approved execution plan, approved eval definition, approved `design.md`, and existing `[topic_root]` into the TDD orchestrator. This phase owns tests, implementation, and implementation-level verification only.*
- **Step 6:** `/eval check` - *Run the approved eval definition against the implementation. If all required evals pass, continue to code review. If any eval fails, return to `tdd-cycle` with pointers to `design.md`, the eval definition, the eval failure log, and the current implementation summary. Retry remediation at most twice before stopping and surfacing the blocker.*
- **Step 7:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]`, approved upstream artifact pointers, and eval pass log. This is the repository-level review gate for security, maintainability, broader correctness gaps, and overall readiness after implementation and eval verification.*

### 2. Bugfix Pipeline (`args="bugfix"`)
- **Step 1:** Load skill: `tdd-cycle` - *Create `[topic_root]` once for the topic, then use incremental mode to write a failing test for the bug and fix it.*
- **Step 2:** `/build-fix` (Load skill: `build-fix`) - *Execute ONLY IF the bug involves compilation/build failures that TDD couldn't resolve.*
- **Step 3:** `/eval check` - *Execute if an eval already exists for the affected behavior or if the bugfix changes an externally visible contract. A failing eval returns to `tdd-cycle` remediation with the eval failure log. Do not create a new ADR for ordinary bugfixes.*
- **Step 4:** `/architect` escalation - *Execute ONLY IF the bugfix changes architecture, public contracts, data models, policy, or long-lived behavior. In that case, create an ADR under the existing `[topic_root]`, then update the plan/eval pointers before continuing.*
- **Step 5:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]` plus any test, build, eval, or ADR pointers created during the fix.*

### 3. Documentation Pipeline (`args="docs"`)
- **Step 1:** `/update-docs` (Load skill: `update-docs`) - *Create `[topic_root]` once for the topic.*
- **Step 2:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]`. Document-only work normally does not require ADR or eval unless it changes a normative workflow contract.*
