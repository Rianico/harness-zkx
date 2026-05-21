name: handoff
description: "Standard LSZ Handoff methodology. Compacts current session state, decision logs, and artifact pointers into a durable handoff document stored in .lsz/ for the next agent or phase transition."
argument-hint: "[next-phase-description]"
---

# LSZ Handoff Methodology

You are performing a **Phase Handoff**. Your goal is to compress the current session's complexity into a single **Source of Truth** pointer that a fresh agent can use to resume work with 100% fidelity.

## Mandatory Handoff Schema

The handoff document MUST be stored in the project's standard artifact location:
`.lsz/{date}/{topic_creation_time}_{short_topic}/handoff.md`

### 1. Executive Summary
- **Current Objective**: What were we trying to achieve?
- **Status**: DONE | IN_PROGRESS | BLOCKED.
- **Key Outcome**: The single most important result (e.g., "Architecture approved").

### 2. Artifact Trail (The Pointers)
Provide a table of **absolute paths** to all durable artifacts created or modified.

| Artifact | Pointer (Absolute Path) | Role |
| :--- | :--- | :--- |
| **Design** | `/path/to/design.md` | Primary behavioral spec |
| **Lineage** | `/path/to/lineage.md` | Audit trail of execution |
| **Code** | `/path/to/src/` | Implementation root |

### 3. Decisions & Constraints
- List non-obvious decisions made.
- Note technical constraints for the next agent (e.g., "Must use Pydantic v2").

### 4. Next Directive
- Be explicit: "Invoke `tdd-cycle` with `[handoff_pointer]`".
- Define the success criteria for the next phase.

## The Handoff Loop

1. **Identify the Topic Root**: Use the LSZ pattern (`.lsz/{date}/{topic}/`).
2. **Scan the Artifacts**: Gather all pointers generated in this session.
3. **Write the Handoff**: Create `handoff.md` in the topic root.
4. **Final Response**: Return ONLY the absolute path to the handoff document.

## Principles

- **Pointer Passing Only**: Never embed the content of a 500-line design in the handoff. Pass the path.
- **Carmack Signal**: High technical signal, low filler.
- **Context Hygiene**: The handoff should allow the next agent to IGNORE the previous chat history.
