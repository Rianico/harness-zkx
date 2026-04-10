---
description: Interactive planner. Assesses risks and creates step-by-step implementation plans using AskUserQuestion for approval.
argument-hint: "<task_description>"
allowed-tools:
  - Agent
  - AskUserQuestion
---

# Command: /plan

**Status:** JIT Workflow Command

Invokes the `planner` agent to create a comprehensive implementation plan before writing any code. Uses interactive prompts for approval.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator and follow these steps sequentially:

1. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "planner"
- `description`: "Generate implementation plan"
- `prompt`: "**\[DOMAIN CONTEXT\]**\n  Language/Domain: \[e.g., Rust\]\n  Root File: \[e.g., Cargo.toml\]\n**\[Comprehensive Analysis\]**\n  [Already known information and analysis]\n\n**\[TASK\]**\n  \[Include the user's feature request and constraints.\]"

2. **Interactive Approval:** Once the `planner` agent returns its report containing the path to the generated plan, you MUST present the plan to the user and prompt them using the `AskUserQuestion` tool with the following schema:

**AskUserQuestion Tool Input:**
```json
{
  "questions": [{
    "question": "Review the generated plan at the provided file path. How would you like to proceed?",
    "header": "Plan Approval",
    "multiSelect": false,
    "options": [
      { "label": "Approve Plan", "description": "Proceed with the generated plan." },
      { "label": "Modify Plan", "description": "Provide feedback to adjust the phases or architecture." },
      { "label": "Reject & Exit", "description": "Discard the plan and exit." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve Plan**: Acknowledge the approval and proceed with the next steps of the user's overall request.
- If **Modify Plan**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `planner` agent. Pass the file path of the previous plan, comprehensive information and analysis, as well as the user's feedback in the `prompt`.
- If **Reject & Exit**: Acknowledge the rejection and exit the workflow.
