---
description: Interactive workflow to sync project docs or generate architecture codemaps.
argument-hint: "[codemaps|project-docs|all]"
---

# Command: /update-docs

**Status:** JIT Workflow Command

Executes an interactive workflow to update project documentation (e.g., CONTRIBUTING.md, .env docs) or generate token-lean architectural codemaps.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "doc-updater"
- `description`: "Update documentation"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include any user arguments.]"
