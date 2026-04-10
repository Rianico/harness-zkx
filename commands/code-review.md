---
description: Code Review Command. Assesses code quality, security, and maintainability.
argument-hint: "<optional_focus_area>"
allowed-tools:
  - Agent
  - AskUserQuestion
---

# Command: /code-review

**Status:** JIT Workflow Command

Executes a universal code review workflow by delegating to the `code-reviewer` agent, followed by interactive resolution.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator and follow these steps sequentially:

1. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "code-reviewer"
- `description`: "Conduct code review"
- `prompt`: "**[DOMAIN CONTEXT]**\nLanguage/Domain: [e.g., Rust]\nRoot File: [e.g., Cargo.toml]\n\n**[TASK]**\n[Include task summarization, files to review, and critical checks]"

2. **Interactive Resolution:** Once the `code-reviewer` agent returns its report, you MUST present the findings to the user and prompt them using the `AskUserQuestion` tool:

**AskUserQuestion Tool Input:**
```json
{
  "questions": [{
    "question": "Code review complete. How would you like to handle the findings?",
    "header": "Review Resolution",
    "multiSelect": false,
    "options": [
      { "label": "Approve & Continue", "description": "No blocking issues, proceed with the workflow." },
      { "label": "Delegate Fixes", "description": "Automatically fix the identified issues." },
      { "label": "Manual Fix", "description": "I will fix these manually." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve & Continue**: Acknowledge and proceed.
- If **Delegate Fixes**: Launch the `tdd-cycle` skill (or appropriate agent) with the review report to implement the fixes.
- If **Manual Fix**: Wait for the user to make changes, then they can re-run the review.
