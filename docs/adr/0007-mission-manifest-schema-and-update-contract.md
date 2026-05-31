# 7. Mission Manifest Schema and Update Contract

Date: 2026-05-25

## Status

Accepted
Amends [ADR-0005](0005-manifest-driven-orchestration-and-provenance-trace.md)

amended by [8. Goal Locking and Aggregated Manifest Hierarchy](0008-goal-locking-and-aggregated-manifest-hierarchy.md)

## Context

While ADR-0005 established the concept of Manifest-Driven Orchestration, we need a specific, parseable schema and a clear update contract to ensure consistency across different skills and orchestrators. This schema must support "Provenance Trace" and "Localized Repair" as non-negotiable requirements.

## Decision

We will implement a standardized `mission_manifest.json` at the root of every orchestrated mission topic.

### 1. The Schema
The manifest must follow this JSON structure:
- `mission_id`: ISO timestamp + short topic.
- `status`: `in_progress | completed | failed | remediate`.
- `intent_hash`: SHA-256 of the primary BDD/Design document.
- `phases`: An array of phase objects, each containing:
  - `phase_id`: Skill/Command name.
  - `status`: `pass | fail | blocked`.
  - `units`: (Optional) Granular sub-tasks (e.g., specific BDD scenarios) with their own `status` and `provenance`.
  - `provenance`: `agent_id`, `timestamp`, and `artifacts` (file paths + SHA-256 hashes).
  - `evidence`: Pointer to raw tool logs (e.g., test output).

### 2. The "Auditor-Only" Update Contract
- **Authority:** Only the Orchestrator (Auditor/Executioner) is authorized to write to the manifest.
- **Verification Loop:** Before recording a `pass` status, the Auditor must verify the hashes of all claimed artifacts and the exit status of the evidence-producing tool.
- **Atomic Writes:** The manifest must be updated immediately after each phase or unit verification, ensuring the mission is resume-ready at any point.

- Rejected: Embedding the manifest inside `handoff.md` (markdown is harder to parse deterministically than JSON).
- Rejected: Allowing subagents to write their own manifest entries (violates the "Executioner" mindset).

## Consequences

- Orchestration skills must now include logic for JSON manifest manipulation.
- Missions are fully resumable; a new agent can recover the exact state by reading the manifest and verifying file hashes.
- Provides a high-fidelity audit trail for debugging why a specific "Work Unit" failed.
