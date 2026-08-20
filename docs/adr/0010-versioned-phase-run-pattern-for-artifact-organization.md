# 10. Versioned Phase-Run Pattern for Artifact Organization

Date: 2026-05-25

## Status

Accepted
Amends [ADR-0007](0007-mission-manifest-schema-and-update-contract.md)

## Context

Implementation remediation often happens multiple times. Storing all artifacts for a phase in a single directory leads to file collisions and a "rough" directory tree (e.g., `tdd-remediation/`). We need a consistent, scalable way to organize artifacts that preserves the full history of every attempt.

## Decision

We will implement the **Versioned Phase-Run Pattern** for all orchestration artifacts.

### 1. The Directory Hierarchy
All phase-specific artifacts MUST be stored in subdirectories following this pattern:
`[topic_root]/[phase_id]/run-[N]/`

Examples:
- `tdd/run-1/`: Initial implementation attempt.
- `tdd/run-2/`: First remediation.
- `eval/run-1/`: Initial verification gate.
- `eval/run-2/`: Post-remediation verification gate.

### 2. Manifest Schema Update
The `Phase` object in `mission_manifest.json` is updated to include a `run_id`:
- `phase_id`: The canonical skill/command name.
- `run_id`: The specific run identifier (e.g., `run-1`, `run-2`).
- `status`: `pass | fail | blocked`.
- `provenance`: (Agent, Timestamp, Artifact hashes).

### 3. Orchestrator Responsibility
- The Orchestrator MUST calculate the next run number by inspecting the existing directories or the manifest.
- The Orchestrator MUST pass the exact `artifact_dir` (including the `run-[N]` suffix) to the downstream skill via the `artifact_dir=<path>` argument.

### Considered Options

- **Rejected: Overwriting files in a single phase folder** — loses provenance history; remediation artifacts collide.
- **Rejected: Timestamped folders** — harder for humans to read and for scripts to increment; lexicographic sort is unreliable.

## Consequences

- Artifact hygiene is significantly improved; the root directory remains clean.
- Remediation history is immutable and easily auditable.
- Orchestration logic becomes slightly more complex as it must manage the run counter.
