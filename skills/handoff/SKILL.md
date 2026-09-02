---
name: handoff
description: >-
  Handoff the decisions, designs, and user intent. Acts as a context aggregator that distills 'Goal', 'Reason', and 'Intent' from the current session and provided artifacts to ensure subsequent agents understand the human context without re-reading full specs or chat history.
argument-hint: |-
  [intent-or-goal-description] [artifacts=path1,path2]
disable-model-invocation: true

---

# LSZ Handoff Methodology

You are performing a **Phase Handoff**. Your goal is to capture the **Goal, Reason, and Intent** of the current session. The resulting `handoff.md` is a **Context Aggregator** that should be high-signal enough to stand in for the full documents or chat history during the initial context load of the next phase.

## Mandatory Handoff Schema

The handoff document MUST be stored in the current phase's artifact location:
`[artifact_dir]/handoff.md`

- **Context Placement**: If `artifact_dir` is not explicitly provided, default to the topic root: `.lsz/{date}/{topic}/handoff.md`.
- **Conflict Prevention**: In multi-phase missions, each phase (e.g., `brainstorming`, `tdd`, `review`) should have its own `handoff.md` within its respective subdirectory to preserve the audit trail and prevent overwrites.

### 1. Goal & Reason (The "Why")
- **Primary Goal**: The ultimate objective.
- **User Intent**: Specific concerns or requirements the user emphasized.
- **Core Reasoning**: Why this specific path was chosen.

### 2. Distilled Context (The "What")
If `artifacts` were provided, read them and extract:
- **Key Decisions**: The "hard-to-reverse" choices from the design/plan.
- **Behavioral Summary**: A high-level summary of the BDD scenarios or implemented behaviors.
- **Constraints/Blockers**: Essential technical boundaries or unresolved issues.

### 3. Artifact Trail (The Pointers)
Provide a table of **absolute paths** to the durable artifacts for deep reference.

| Artifact | Pointer (Absolute Path) | Role |
| :--- | :--- | :--- |
| **Design/Spec** | `/path/to/design.md` | Full source of truth |
| **Implementation** | `/path/to/...` | Implementation summary |

### 4. Next Directive
- **Success Criteria**: What does "done" look like for the next agent?
- **Suggested Action**: e.g., "Invoke `eval-gate` with `handoff_pointer=[path]`".

## The Handoff Loop

1. **Identify the Topic Root**: Use the LSZ pattern `.lsz/{date}/{topic}/`.
2. **Scan Artifacts**: If `artifacts=` is provided, use `Read` to extract the "Why" and "Critical Decisions" from them.
3. **Synthesize Intent**: Review the current session to capture the user's explicit preferences and reasoning.
4. **Write the Handoff**: Create `handoff.md` in the topic root.
5. **Final Response**: Return a standard LSZ response with the summary and the path to the handoff document.

## Principles

- **Context Displacement**: Aim to make the `handoff.md` the *only* thing the next agent needs to read to understand the mission's intent.
- **Pointer-Based Handoff**: Always pass absolute paths to the full files; never embed 500-line specs in the handoff.
- **Carmack Signal**: Technical depth, zero fluff.
