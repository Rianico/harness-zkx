# LSZ Architecture

This project defines and implements the LSZ (Layered Skill-first) architecture, a design for building robust, context-efficient AI agents.

## Language

**Skill**:
The primary unit of reusable methodology and workflow logic. Skills define the WHAT and the HOW of a task.
_Naming_: Use **Nouns** for Domain Knowledge (bare nouns for facts like `adr`, or `[topic]-expert` for expertise) and **Verbs/Prepositional Phrases** for Actions/Workflows (e.g., `handoff`, `to-prd`).
_Avoid_: Thin wrappers, logic-heavy agents.

**Agent**:
A lean execution engine defined by a persona, a tool boundary, and a focused role. Agents define the WHO and the TOOLS.
_Avoid_: Storing long workflow instructions in agents.

**Orchestration**:
The process of sequencing and managing multi-phase, multi-party workflows.
_Naming_: Use **Present Participles** (V-ing) for continuous orchestration processes (e.g., `orchestrating`, `brainstorming`).
_Avoid_: Hero-mode orchestrators that do implementation work directly.

**Handoff**:
A distilled document (`handoff.md`) used as a Mission Bridge to preserve intent, reasoning, and artifact pointers between phases.
_Avoid_: History hoarding, prose-only summaries.

**Artifact Hygiene**:
The discipline of organizing, deduplicating, and consolidating project files to prevent context bloat and discovery failures.

**Respect Tool Feedback**:
The principle that automated tool signals (LSP diagnostics, linters, tests) are authoritative blockers that must be resolved before a task is complete.
