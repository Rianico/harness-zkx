---
description: Code Review
argument-hint: "<optional_focus_area>"
---

# Command: /code-review

**Status:** JIT Workflow Command

Executes a universal code review workflow by delegating to the `code-reviewer` agent.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "code-reviewer"
- `description`: "Conduct code review"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include task summarization, files to review, and critical checks]"
