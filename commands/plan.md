---
description: Interactive planner. Assesses risks and creates step-by-step implementation plans using AskUserQuestion for approval.
argument-hint: "<task_description>"
---

# Command: /plan

**Status:** JIT Workflow Command

Invokes the `planner` agent to create a comprehensive implementation plan before writing any code. Uses interactive prompts for approval.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "planner"
- `description`: "Generate implementation plan"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include the user's feature request and constraints.]"
