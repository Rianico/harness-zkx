---
name: orchestrate-workflow
description: Defines the standard execution pipelines (Feature, Bugfix, Docs). Use this skill to orchestrate multiple ECC Commands in a sequential workflow.
argument-hint: "[feature|bugfix|docs]"
---

# Orchestration Workflow Skill

You have invoked the Orchestration Workflow Skill. This skill defines the strict sequence of ECC Commands you must execute to complete complex software engineering tasks.

## Orchestration Rules
1. **Command Execution, Not Bare Agents:** You MUST NOT invoke the `Agent` tool directly unless instructed by a specific Command's execution rules. Instead, you must load the Command's methodology via the `Skill` tool, then execute its workflow exactly as written.
2. **Sequential Execution:** You must execute the commands in the exact order specified by the pipeline.
3. **State Passing:** You must retain the context/output of the previous command (e.g., the approved architectural design or the approved plan) and include it in the execution of the subsequent command.
4. **Interactive Approval Propagation:** By executing Commands rather than bare agents, you naturally inherit their `AskUserQuestion` interactive approval loops. You MUST honor these UI prompts and handle user feedback exactly as defined in the Command's instructions before proceeding to the next step in the pipeline.

## Standard Pipelines

To execute a step, load the corresponding Skill (e.g., `skill="architect"`) and follow its "Execution Instruction" section.

### 0. Pre-implementation (Research & Reuse)
*Mandatory before any new implementation.*
- **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns.
- **Library docs second:** Use Context7 or vendor docs to confirm API behavior.
- **Search package registries:** npm, PyPI, crates.io, etc.
- **Tavity only when insufficient:** Use `websearch-tavity` skill for broader web research.
- Prefer adopting or porting a proven approach over writing net-new code.

### 1. Feature Pipeline (`args="feature"`)
- **Step 1:** `/architect` (Load skill: `architect`)
- **Step 2:** `/plan` (Load skill: `plan`) - *Pass the approved architecture into the planner.*
- **Step 3:** `/tdd` (Load skill: `tdd-cycle`) - *Pass the approved plan into the TDD orchestrator.*
- **Step 4:** `/code-review` (Load skill: `code-review`) - *Use code-reviewer agent immediately after writing code.*

### 2. Bugfix Pipeline (`args="bugfix"`)
- **Step 1:** `/tdd` (Load skill: `tdd-cycle`) - *Use incremental mode to write a failing test for the bug and fix it.*
- **Step 2:** `/build-fix` (Load skill: `build-fix`) - *Execute ONLY IF the bug involves compilation/build failures that TDD couldn't resolve.*
- **Step 3:** `/code-review` (Load skill: `code-review`)

### 3. Documentation Pipeline (`args="docs"`)
- **Step 1:** `/update-docs` (Load skill: `update-docs`)
- **Step 2:** `/code-review` (Load skill: `code-review`)
