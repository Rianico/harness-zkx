---
description: Sequential multi-agent orchestration for complex workflows. Routes to `orchestrate-workflow` skill.
---

# Command: /orchestrate

**Status:** JIT Workflow Command

Executes a sequential pipeline of native Claude Code sub-agents (e.g., Planner -> TDD -> Reviewer) to complete complex tasks.

**How it works:**
The primary LLM acts as the Orchestrator. It invokes the `orchestrate-workflow` skill to learn the correct pipeline sequence, then sequentially dispatches native sub-agents, passing state between them.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator. Do not attempt to write code or execute the steps yourself.

1. First, invoke the `Skill` tool with `skill="orchestrate-workflow"` and the appropriate pipeline argument (feature, bugfix, or docs).
2. Execute the steps defined by the skill in strict sequence using the `Agent` tool.

**Mandatory Agent Invocation Schema:**
Whenever you call an agent in the sequence, you MUST use exactly this format:
- `subagent_type`: "[target agent, e.g., planner]"
- `description`: "[a short description up to 10 words]"
- `prompt`: "[task summarization, critical checks, user requirements, output from the previous agent in the pipeline, and an explicit instruction for the agent to use its Universal Discovery Phase to find root config files]"

**Usage:**
```bash
/orchestrate feature "Add OAuth2 login"
/orchestrate bugfix "Fix the null pointer exception in the auth middleware"
/orchestrate docs "Update the README with the new API endpoints"
```
