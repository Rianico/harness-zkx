---
description: Universal TDD entrypoint. Routes your request to the `tdd-guide` agent and automatically applies language-specific rules.
argument-hint: "<task_description>"
---

# Command: /tdd

**Status:** JIT Workflow Command

Executes the Red-Green-Refactor Test-Driven Development loop for any supported language by delegating to the `tdd-guide` agent.

**How it works:**
The primary LLM discovers the domain and passes that state to the `tdd-guide` agent, which invokes the `tdd-workflow` skill and executes the loop.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "tdd-guide"
- `description`: "Execute TDD loop"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include user requirements, arguments like language/work_type, and instructions]"
