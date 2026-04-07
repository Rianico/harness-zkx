---
description: Build and Fix
argument-hint: "<optional_error_context>"
---

# Command: /build-fix

**Status:** JIT Workflow Command

Resolves build and compilation errors incrementally across any supported language by delegating to the `build-resolver` agent.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`) to determine the domain.
2. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "build-resolver"
- `description`: "Resolve build errors"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include the specific error output, target files, and user constraints]"
