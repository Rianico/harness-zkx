# 5. Manifest-Driven Orchestration and Provenance Trace

Date: 2026-05-25

## Status

Accepted

derives from [4. Goal-Driven Development (GDD) as Foundational Philosophy](0004-goal-driven-development-gdd-as-foundational-philosophy.md)

refined by [6. Consolidated Orchestration Pipeline](0006-consolidated-orchestration-pipeline.md)

## Context

"Hallucinated Completion" occurs when a model fills a structured response with claims of success that haven't actually occurred in the environment. To prevent this, we need a way to externalize state and track the "How" and "By Whom" of every change.

## Decision

We will use a **Manifest-Driven Orchestration** pattern with a strict **Provenance Trace**.

1.  **Job Manifest:** A deterministic, externalized log (e.g., `manifest.json`) tracks all sub-tasks and their current state.
2.  **Auditor-Recorded Provenance:** The Orchestrator (Auditor) is the sole authority for recording manifest entries. It must take "Observation Turns" to verify file hashes, job IDs, and tool outputs before updating the manifest.
3.  **Trace Granularity:** We will track the full provenance trace, including intermediate "Red/Green" transitions in TDD, rather than just final snapshots.
4.  **Localized Repair:** Use the manifest to enable autonomous repair of specific failing "Work Units" without restarting entire missions.

### Considered Options

- **Rejected: Subagent-Reported Manifests** — subagents can lie about their own work; violates auditor authority.
- **Rejected: Result-Only Snapshots** — loses the audit trail needed for complex debugging; intermediate transitions are invisible.

## Consequences

- Orchestrators must spend context/turns on observing the environment to update the manifest.
- Auditability is significantly increased, making missions resumable and repairable at the sub-task level.
- Higher file-system overhead as manifest files must be maintained throughout the topic lifecycle.
