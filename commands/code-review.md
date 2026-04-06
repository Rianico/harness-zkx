---
description: Code Review
---

# Command: /code-review

**Status:** JIT Workflow Command

Executes a universal code review workflow by delegating to the `code-reviewer` agent.

**How it works:**
The `code-reviewer` agent analyzes the project, loads the appropriate domain rules (e.g., `rules/python.md`), retrieves the deep expert skill if necessary, and then conducts the review.

**Execution Instruction:**
To execute this workflow, you MUST invoke the Agent tool. Do not attempt to conduct the review yourself in this primary context.

Use the Agent tool with these parameters:
- `subagent_type`: "code-reviewer"
- `description`: "Conduct code review"
- `prompt`: "[Include task summarization, files to review, critical checks from the user, and an explicit instruction for the agent to check the rules/ directory for domain constraints]"

**Usage:**
```bash
/code-review
/code-review "focus on security"
```
