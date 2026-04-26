---
description: Run multi-step LSZ software workflows across architecture, planning, TDD, build repair, docs, and code review. Use for feature work, refactors, bug fixes, and documentation changes that need sequential skill orchestration with approvals and pointer-based handoff.
argument-hint: "[feature|refactor|bugfix|docs] <task_description>"
allowed-tools:
  - Skill
  - Agent
  - AskUserQuestion
  - Read
  - Bash
---

# Command: /orchestrate

**Status:** JIT Workflow Entry Point

Executes a sequential pipeline of LSZ skills (e.g., `architect` -> `plan` -> `tdd-cycle`) to complete complex tasks, inheriting all interactive approvals and guardrails while preserving strict phase boundaries.

**How it works:**
The primary LLM acts as the Explorer and Orchestrator. It invokes the `orchestrate-workflow` skill to learn the pipeline sequence, and then sequentially loads and executes the required skills via the `Skill` tool, passing approved file pointers from one phase to the next.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Retrieve Pipeline:** Invoke the `Skill` tool with `skill="orchestrate-workflow"` and the appropriate pipeline argument (e.g., `feature`).
2. **Execute Pipeline:** Execute the steps defined by the skill.
   - For each step, you MUST load the specified skill via the `Skill` tool.
   - You MUST follow the loaded skill's execution contract exactly, including launching its specified sub-agent, following its phases, and handling its `AskUserQuestion` interactive approval loop.
   - Only proceed to the next step in the pipeline AFTER the user has approved the current step's output (e.g., approving the plan).

**Mandatory Context Passing (Pointer-Based):**
Whenever a skill's execution instructions require you to launch an agent or pass state, you MUST pass file path pointers instead of reading prior artifacts into the context window. Prepend the `[DOMAIN CONTEXT]` to the prompt so the sub-agent inherits discovery, then include only the approved upstream pointers relevant to that phase.

Use this structure:
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[APPROVED UPSTREAM POINTERS]**\n[Include only the absolute file path pointers the next phase is expected to consume, such as architecture ADR or execution plan]\n\n**[TASK]**\n[task summarization and user requirements]"

**Phase Ownership Contract:**
- `brainstorming` owns requirement discovery: source-of-truth design capture, examples, negative requirements, acceptance criteria, assumptions, and open questions.
- `architect` owns decisions: problem framing, boundaries, invariants, interfaces, trade-offs, risks, and rejected alternatives.
- `plan` owns execution: ordered steps, dependency sequencing, touched modules, checkpoints, risks, and explicit out-of-scope items.
- `eval define` owns acceptance checks: converting the approved source of truth into reviewed capability, contract, negative, and regression evals.
- `tdd-cycle` owns implementation validation: tests, implementation progress, and implementation-level verification needed to complete the change.
- `eval check` owns spec-compliance verification: checking the implementation against the approved eval definition and producing pass/fail logs.
- `code-review` owns repository-level review: security, maintainability, correctness gaps not covered by TDD/evals, and overall readiness.

**Final Review Remediation Policy:**
When `code-review` is the final phase of an `/orchestrate` pipeline, invoke it with `orchestrated_final_review=true`. In that mode, safe `medium`, `low`, or `minor` findings should be delegated to an implementation subagent for remediation without asking the user first. Ask for user approval only when findings are `blocking`, `high`, security-critical, destructive or risky to fix, or require a product/architecture decision.

The orchestrator owns transitions between phases. If `eval check` is not READY, return to `tdd-cycle` remediation with pointers to the source of truth, eval definition, eval log, and implementation artifacts. Do not proceed to `code-review` until required evals pass or the workflow explicitly stops as blocked.

Do not ask downstream phases to recreate upstream artifacts in different prose forms.
