---
description: Sequential multi-agent orchestration for complex workflows. Routes to `orchestrate-workflow` skill.
argument-hint: "[feature|bugfix|docs] [--heavy] <task_description>"
---

# Command: /orchestrate

**Status:** JIT Workflow Command

Executes a sequential pipeline of native Claude Code sub-agents (e.g., Planner -> TDD -> Reviewer) to complete complex tasks.

**How it works:**
The primary LLM acts as the Explorer and Orchestrator. It first discovers the project domain, then invokes the `orchestrate-workflow` skill to learn the pipeline sequence, and sequentially dispatches native sub-agents while explicitly passing the discovered state.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. 

1. **Explore:** Analyze the directory structure (`ls -la` or `Glob`) and find the root configuration file (e.g., `Cargo.toml`, `pyproject.toml`, or `README.md`). Determine the domain.
2. **Retrieve Pipeline:** Invoke the `Skill` tool with `skill="orchestrate-workflow"` and the appropriate pipeline argument.
3. **Dispatch:** Execute the steps defined by the skill.

**Mandatory Agent Invocation Schema:**
Whenever you call an agent, you MUST prepend the `[DOMAIN CONTEXT]` to the prompt so the sub-agent inherits your discovery:
- `subagent_type`: "[target agent, e.g., planner]"
- `description`: "[a short description]"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[task summarization, user requirements, output from the previous agent in the pipeline]"
