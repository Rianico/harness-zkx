---
description: Build and Fix
---

# Command: /build-fix

**Status:** JIT Workflow Command

Resolves build and compilation errors incrementally across any supported language by delegating to the `build-resolver` agent.

**How it works:**
The generic `build-resolver` agent detects the language from the error or project root, loads the appropriate domain rules (e.g., `rules/rust.md`), retrieves the deep expert methodology (e.g., `rust-build-expert`), and incrementally fixes the errors.

**Execution Instruction:**
To execute this workflow, you MUST invoke the Agent tool. Do not attempt to resolve the build yourself in this primary context.

Use the Agent tool with these parameters:
- `subagent_type`: "build-resolver"
- `description`: "Resolve build errors"
- `prompt`: "[Include the specific error output, target files, user constraints, and an explicit instruction for the agent to check the rules/ directory for domain constraints]"

**Usage:**
```bash
/build-fix
```
