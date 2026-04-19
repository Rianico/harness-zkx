---
name: orchestrate-workflow
description: Defines the standard execution pipelines (Feature, Refactor, Bugfix, Docs). Use this skill to orchestrate multiple LSZ Commands in a sequential workflow.
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
*Mandatory before any new implementation.*
- **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns.
- **Library docs second:** Use Context7 or vendor docs to confirm API behavior.
- **Search package registries:** npm, PyPI, crates.io, etc.
- **Tavity only when insufficient:** Use `websearch-tavity` skill for broader web research.
- Prefer adopting or porting a proven approach over writing net-new code.

### 1. Feature Pipeline (`args="feature|refactor"`)
- **Step 1:** `/architect` (Load skill: `architect`) - *Create `[topic_root]` once for the topic and pass it into downstream commands after approval. This phase defines the architecture decision record only.*
- **Step 2:** `/plan` (Load skill: `plan`) - *Pass the approved architecture pointer and the existing `[topic_root]` into the planner. This phase converts the ADR into an execution plan only.*
- **Step 3:** `/tdd` (Load skill: `tdd-cycle`) - *Pass the approved execution plan pointer and the existing `[topic_root]` into the TDD orchestrator. This phase should focus on tests, implementation, and implementation-level verification only.*
- **Step 4:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]`; this is the repository-level review gate for security, maintainability, broader correctness gaps, and overall readiness after implementation.*

### 2. Bugfix Pipeline (`args="bugfix"`)
- **Step 1:** `/tdd` (Load skill: `tdd-cycle`) - *Create `[topic_root]` once for the topic, then use incremental mode to write a failing test for the bug and fix it.*
- **Step 2:** `/build-fix` (Load skill: `build-fix`) - *Execute ONLY IF the bug involves compilation/build failures that TDD couldn't resolve.*
- **Step 3:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]`.*

### 3. Documentation Pipeline (`args="docs"`)
- **Step 1:** `/update-docs` (Load skill: `update-docs`) - *Create `[topic_root]` once for the topic.*
- **Step 2:** `/code-review` (Load skill: `code-review`) - *Pass the existing `[topic_root]`.*
