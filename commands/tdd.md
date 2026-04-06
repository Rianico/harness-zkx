---
description: Universal TDD entrypoint. Routes your request to the `tdd-guide` agent and automatically applies language-specific rules.
---

# Command: /tdd

**Status:** JIT Workflow Command

Executes the Red-Green-Refactor Test-Driven Development loop for any supported language by delegating to the `tdd-guide` agent.

**How it works:**
The generic `tdd-guide` agent detects the language, loads the appropriate domain rules, **invokes the mandatory `tdd-workflow` skill**, retrieves testing expertise, and enforces the TDD loop.

**Execution Instruction:**
To execute this workflow, you MUST invoke the Agent tool. Do not attempt to write the tests or execute the loop yourself in this primary context.

Use the Agent tool with these parameters:
- `subagent_type`: "tdd-guide"
- `description`: "Execute TDD loop"
- `prompt`: "[Include user requirements, target features, arguments like language/work_type, an instruction to invoke the mandatory `tdd-workflow` skill, and an instruction to check the rules/ directory]"

**Usage:**
```bash
/tdd "Add an auth middleware"
/tdd work_type="bugfix" language="python" "Fix the login route"
```
