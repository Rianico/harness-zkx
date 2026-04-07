---
description: Interactive architectural design and review. Assesses system design against modern patterns (Clean Arch, DDD, Microservices).
argument-hint: "<task_description>"
---

# Command: /architect

**Status:** JIT Workflow Command

Invokes the `architect` agent to design new systems, refactor large components, or perform structural reviews of your codebase.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "architect"
- `description`: "Perform architectural design"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include the user's architectural request, constraints, and explicit instructions for the agent to load the `architecture-expert` skill.]"

**Usage:**
```bash
/architect "Design a microservice architecture for the new payment gateway"
/architect "Review our current src/ directory for Clean Architecture violations"
```
