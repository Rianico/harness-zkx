---
description: Sequential multi-command orchestration for complex workflows. Routes to `orchestrate-workflow` skill.
argument-hint: "[feature|refactor|bugfix|docs] <task_description>"
allowed-tools:
  - Skill
  - Agent
  - Read
  - Bash
---

# Command: /orchestrate

**Status:** JIT Workflow Command

Executes a sequential pipeline of LSZ Commands (e.g., /architect -> /plan -> /tdd) to complete complex tasks, inheriting all interactive approvals and guardrails while preserving strict phase boundaries.

**How it works:**
The primary LLM acts as the Explorer and Orchestrator. It invokes the `orchestrate-workflow` skill to learn the pipeline sequence, and then sequentially loads and executes the required Commands (via the `Skill` tool), passing the approved file pointer state from one command to the next.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Retrieve Pipeline:** Invoke the `Skill` tool with `skill="orchestrate-workflow"` and the appropriate pipeline argument (e.g., `feature`).
2. **Execute Pipeline:** Execute the steps defined by the skill.
   - For each step, you MUST load the specified Command via the `Skill` tool.
   - You MUST follow the "Execution Instruction" of that loaded Command exactly (including launching its specific sub-agent, following the phases, and handling its `AskUserQuestion` interactive approval loop).
   - Only proceed to the next step in the pipeline AFTER the user has approved the current step's output (e.g., approving the plan).

**Mandatory Context Passing (Pointer-Based):**
Whenever a Command's execution instructions require you to launch an agent or pass state, you MUST pass file path pointers instead of reading prior artifacts into the context window. Prepend the `[DOMAIN CONTEXT]` to the prompt so the sub-agent inherits discovery, then include only the approved upstream pointers relevant to that phase.

Use this structure:
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[APPROVED UPSTREAM POINTERS]**\n[Include only the absolute file path pointers the next phase is expected to consume, such as architecture ADR or execution plan]\n\n**[TASK]**\n[task summarization and user requirements]"

**Phase Ownership Contract:**
- `/architect` owns decisions: problem framing, boundaries, invariants, interfaces, trade-offs, risks, and rejected alternatives.
- `/plan` owns execution: ordered steps, dependency sequencing, touched modules, checkpoints, risks, and explicit out-of-scope items.
- `/tdd` owns implementation validation: tests, implementation progress, and implementation-level verification needed to complete the change.
- `/code-review` owns repository-level review: security, maintainability, correctness gaps not covered by TDD, and overall readiness.

Do not ask downstream phases to recreate upstream artifacts in different prose forms.
