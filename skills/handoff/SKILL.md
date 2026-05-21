name: handoff
description: "Standard LSZ Handoff methodology. Compacts current session state, decision logs, and artifact pointers into a durable handoff document stored in .lsz/ for the next agent or phase transition."
argument-hint: "[next-phase-description]"
---

# LSZ Handoff Methodology

You are performing a **Phase Handoff**. Your goal is to compress the current session's complexity into a single **Source of Truth** pointer (`handoff.md`) that a fresh agent can use to resume work with 100% fidelity.

## Mandatory Handoff Schema

The handoff document MUST be stored in the project's standard artifact location:
`.lsz/{date}/{topic_creation_time}_{short_topic}/handoff.md`

### 1. Executive Summary (LSZ Standard)
Inherit and refine the `## Summary` sections from the skills executed in this session.
- **Current Objective**: What were we trying to achieve?
- **Status**: DONE | IN_PROGRESS | BLOCKED (Map from `## Route`).
- **Key Outcome**: The single most important result.

### 2. Artifact Trail (LSZ Standard)
Extract all paths from the `## Artifacts` sections of previous responses. Provide a table of **absolute paths**.

| Artifact | Pointer (Absolute Path) | Role |
| :--- | :--- | :--- |
| **Design** | `/path/to/design.md` | Primary behavioral spec |
| **Lineage** | `/path/to/lineage.md` | Audit trail of execution |
| **Implementation** | `/path/to/summary.md` | Implementation progress |

### 3. Decisions & Constraints
- List non-obvious decisions made.
- Note technical constraints for the next agent.

### 4. Next Directive (LSZ Standard)
- Be explicit: "Invoke the [Next Skill] (e.g., `architect`, `tdd-cycle`, `update-docs`) with `handoff_pointer=[handoff_path]`".
- Define the specific success criteria for the next agent to meet.

## The Handoff Loop

1. **Identify the Topic Root**: Use the LSZ pattern or the `topic_root` passed by the orchestrator.
2. **Scan for Artifacts**: Gather all `## Artifacts` returned by skills/agents in the current context.
3. **Write the Handoff**: Create `handoff.md` in the topic root.
4. **Final Response**:
   ```markdown
   ## Summary
   Handoff generated for [Topic].
   ## Artifacts
   - [base_dir]/handoff.md
   ## Route
   continue
   ```

## Principles

- **Pointer Passing Only**: Never embed the content of a 500-line design in the handoff. Pass the path.
- **Carmack Signal**: High technical signal, low filler.
- **Context Hygiene**: The handoff should allow the next agent to IGNORE the previous chat history.
