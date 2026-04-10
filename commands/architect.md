---
description: Interactive architectural design and review. Assesses system design against modern patterns (Clean Arch, DDD, Microservices).
argument-hint: "<task_description>"
allowed-tools:
  - Agent
  - AskUserQuestion
---

# Command: /architect

**Status:** JIT Workflow Command

Invokes the `architect` agent to design new systems, refactor large components, or perform structural reviews of your codebase.

**Execution Instruction:**
To execute this workflow, you MUST act as the Orchestrator and follow these steps sequentially:

1. **Dispatch:** Invoke the Agent tool with these parameters:
- `subagent_type`: "architect"
- `description`: "Perform architectural design"
- `prompt`: "**\[DOMAIN CONTEXT\]**\n  Language/Domain: \[e.g., Rust\]\n  Root File: \[e.g., Cargo.toml\]\n**\[Comprehensive Analysis\]**\n  [Already known information and analysis]\n\n**[TASK]**\n[Include the user's architectural request, constraints, and explicit instructions for the agent to load the `architecture-expert` skill.]"

2. **Interactive Approval:** Once the `architect` agent returns its architectural proposal (either as text or a saved file), you MUST present the proposal to the user and prompt them using the `AskUserQuestion` tool with the following schema:

**AskUserQuestion Tool Input:**
```json
{
  "questions": [{
    "question": "Review the generated architectural design. How would you like to proceed?",
    "header": "Architecture Review",
    "multiSelect": false,
    "options": [
      { "label": "Approve Design", "description": "Proceed with this architecture." },
      { "label": "Modify Design", "description": "Provide feedback to adjust components, patterns, or trade-offs." },
      { "label": "Reject & Exit", "description": "Discard the design and exit." }
    ]
  }]
}
```

3. **Handle User Response:**
- If **Approve Design**: Acknowledge the approval and proceed with the next steps.
- If **Modify Design**: Ask the user what they want to change via standard chat. Once they reply, invoke a **NEW** `architect` agent (do NOT resume the old one). Pass the context of the previous architecture design, comprehensive information and analysis, as well as the user's feedback in the `prompt`.
- If **Reject & Exit**: Acknowledge the rejection and exit the workflow.

**Usage:**
```bash
/architect "Design a microservice architecture for the new payment gateway"
/architect "Review our current src/ directory for Clean Architecture violations"
```
