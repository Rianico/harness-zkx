name: handoff
description: "Handoff the decisions, designs, and user intent so subsequent agents understand the goals, reasoning, and context of the work. Ensures that the 'why' behind the design is preserved alongside the technical pointers."
argument-hint: "[intent-or-goal-description]"
---

# LSZ Handoff Methodology

You are performing a **Phase Handoff**. Your goal is to capture the **Goal, Reason, and Intent** of the current session so that the next agent doesn't just see *what* was done, but understands *why* it was done and what the user is trying to achieve.

## Mandatory Handoff Schema

The handoff document MUST be stored in: `.lsz/{date}/{topic}/handoff.md`

### 1. Goal & Reason (The "Why")
- **Primary Goal**: What is the ultimate objective of this feature or fix?
- **User Intent**: What specific concerns or requirements did the user emphasize?
- **Core Reasoning**: Why was this specific architectural path or design chosen?

### 2. Decisions & Concerns
- **Key Decisions**: List the "hard-to-reverse" choices made in this session.
- **Constraints**: What are we specifically avoiding or respecting?
- **Open Questions**: What still needs to be clarified with the user?

### 3. Artifact Trail (The "Evidence")
Provide a table of **absolute paths** to the durable artifacts that represent the "What."

| Artifact | Pointer (Absolute Path) | Role |
| :--- | :--- | :--- |
| **Design/Spec** | `/path/to/design.md` | Decisions & Behavioral specs |
| **Lineage** | `/path/to/lineage.md` | Audit trail of execution |

### 4. Next Directive
- **Success Criteria**: What does "done" look like for the next phase?
- **Suggested Next Step**: "Invoke [Skill] with `handoff_pointer=[path]` to continue [Task]."

## The Handoff Loop

1. **Synthesize Intent**: Review the conversation to identify the user's primary concerns and the reasoning behind the current design.
2. **Collect Pointers**: Gather all relevant artifacts (`design.md`, implementation summaries, etc.).
3. **Write the Handoff**: Create a narrative-driven `handoff.md` that bridges the gap between the design and implementation.
4. **Final Response**: Return a standard LSZ response with the summary and the path to the handoff document.


## Principles

- **Pointer Passing Only**: Never embed the content of a 500-line design in the handoff. Pass the path.
- **Carmack Signal**: High technical signal, low filler.
- **Context Hygiene**: The handoff should allow the next agent to IGNORE the previous chat history.
