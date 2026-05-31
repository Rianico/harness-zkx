# Manifest Engineering: Patterns & Anti-Patterns

This document defines the standard patterns for designing and managing manifests in the LSZ architecture. While different skills may have unique manifest requirements, these patterns ensure consistency, traceability, and robust session recovery.

## Core Patterns

### 1. High-Resolution Granularity (Work Units)
Break down monolithic phases into granular "Work Units."
- **Why:** Enables targeted repair of failing sub-tasks and provides a clear "resumption watermark" during recovery.
- **Implementation:** Use a `units` array within phase objects.
- **Example:** An `eval` phase should have `define`, `check`, and `report` units.

### 2. Lifecycle-Aware Timestamps (Dual-Timestamping)
Distinguish between the start and end of an action.
- **Pattern:** Use `created_at` and `finished_at` instead of a single `timestamp`.
- **Why:** Allows calculating the duration of tasks and identifying "stale" or "hung" processes during session recovery.
- **Requirement:** `created_at` MUST be set when the status is first moved to `in_progress`.

### 3. Strict Provenance Trace
Every change must be attributed to an actor and tied to specific artifacts.
- **Requirement:** Each entry MUST include an `agent_id` and a list of `artifacts` (file paths + SHA-256 hashes).
- **Environmental Truth:** The manifest is a *claim*; the filesystem is the *truth*. Always verify hashes (`sha256sum --check`) when resuming.

### 4. Goal Locking (Pre-allocation)
Pre-populate the manifest with expected units *before* execution.
- **Why:** Prevents "moving the goalposts" (agents skipping difficult tasks) and provides a clear checklist of remaining work.

## Anti-Patterns

| Anti-Pattern | Why it's bad | Corrective Action |
| :--- | :--- | :--- |
| **Vague Timestamps** | A single `timestamp` doesn't tell you if a task is stalled or just started. | Use `created_at` and `finished_at`. |
| **"Prose" Progress** | Storing status as descriptive text (e.g., "I am currently fixing the bug"). | Use rigid enums: `in_progress`, `completed`, `failed`. |
| **Monolithic Phases** | Tracking a 2-hour task as a single manifest entry. | Decompose into 15-minute `units`. |
| **Heroic Resumption** | Resuming work without checking hashes of previous artifacts. | Always run an "Observation Turn" (verify hashes) first. |
| **Implicit Creation** | Creating a phase entry only after it's finished. | Register `in_progress` immediately to lock the `created_at` time. |

## Standard Unit Schema

```json
{
  "unit_id": "string",
  "status": "in_progress | completed | failed",
  "created_at": "ISO-8601 UTC",
  "finished_at": "ISO-8601 UTC | null",
  "provenance": {
    "agent_id": "string",
    "artifacts": [
      { "path": "string", "hash": "sha256" }
    ]
  }
}
```
