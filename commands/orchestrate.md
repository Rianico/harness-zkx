---
description: Sequential multi-command orchestration for complex workflows. Routes to `orchestrate-workflow` skill.
argument-hint: "[feature|bugfix|docs] <task_description>"
allowed-tools:
  - Skill
  - Agent
  - AskUserQuestion
  - SendMessage
  - Read
  - Bash
---

# Command: /orchestrate

**Status:** JIT Workflow Command

Executes a sequential pipeline of ECC Commands (e.g., /architect -> /plan -> /tdd) to complete complex tasks, inheriting all interactive approvals and guardrails.

**How it works:**
The primary LLM acts as the Explorer and Orchestrator. It invokes the `orchestrate-workflow` skill to learn the pipeline sequence, and then sequentially loads and executes the required Commands (via the `Skill` tool), passing the approved state from one command to the next.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Retrieve Pipeline:** Invoke the `Skill` tool with `skill="orchestrate-workflow"` and the appropriate pipeline argument (e.g., `feature`).
2. **Execute Pipeline:** Execute the steps defined by the skill.
   - For each step, you MUST load the specified Command via the `Skill` tool.
   - You MUST follow the "Execution Instruction" of that loaded Command exactly (including launching its specific sub-agent and handling its `AskUserQuestion` interactive approval loop).
   - Only proceed to the next step in the pipeline AFTER the user has approved the current step's output (e.g., approving the plan).

**Mandatory Context Passing:**
Whenever a Command's execution instructions require you to launch an agent, you MUST prepend the `[DOMAIN CONTEXT]` to the prompt so the sub-agent inherits your discovery, ALONG WITH the output from the previous pipeline step:
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[PREVIOUS STATE]**\n[Include the approved architecture/plan from the previous step]\n\n**[TASK]**\n[task summarization and user requirements]"
