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

**Manifest**:
A deterministic, externalized log (e.g., `manifest.json`) that tracks sub-tasks, job IDs, and the current state of a mission. It prevents "hallucinated completion" by anchoring the AI to verifiable evidence.

**Provenance**:
The traceable record of how an artifact was created, including file hashes, timestamps, and the specific agent/tool responsible for each transition. It enables auditability and localized repair.

**Artifact Hygiene**:
The discipline of organizing, deduplicating, and consolidating project files to prevent context bloat and discovery failures.

**Artifact Root**:
The git-ignored storage location for workflow-generated artifacts, conventionally under `.lsz/`. Artifact roots preserve phase outputs without making generated files part of the repository's canonical source.
_Avoid_: Repository root, committed source tree.

**Respect Tool Feedback**:
The principle that automated tool signals (LSP diagnostics, linters, tests) are authoritative blockers that must be resolved before a task is complete.

**LLM-facing Text**:
Text whose primary consumer is an AI agent or model. Markdown is the default format for LLM-facing text because it preserves readable structure with low maintenance and parsing overhead.
_Avoid_: Human-facing presentation artifacts.

**Human-facing Artifact**:
An artifact whose primary consumer is a human reader, reviewer, or operator. HTML is preferred only when rich layout, visual hierarchy, or interactivity materially improves comprehension.
_Avoid_: LLM-facing source text.

**Generated View**:
A human-facing rendering derived from a canonical source artifact, analogous to a database view over underlying data. Generated views illustrate source content in a desired format but do not modify or replace the source; by default, an HTML view is written beside its Markdown source unless the user specifies another output path.
_Avoid_: Source of truth.

**View Provenance**:
The metadata embedded in a generated view that identifies its canonical source, generator, generation time, and source hash. View provenance makes drift between a view and its source detectable.
_Avoid_: Implicit source relationship.

**View Refresh**:
The act of regenerating a generated view from its canonical source. A view refresh may overwrite an existing view only when provenance shows it was generated from the same source; unprovenanced or differently sourced files require explicit user intent.
_Avoid_: Blind overwrite.

**Canonical Source**:
The durable artifact that agents read, edit, version, and reuse as working context. Markdown is the canonical source format for prose-heavy AI workflow artifacts.
_Avoid_: Generated view.

**Renderer**:
A converter that derives a generated view from a canonical source without changing the source's substantive content. Renderers may improve presentation but do not summarize, reinterpret, add, or remove meaning unless explicitly asked.
_Avoid_: Editor, summarizer.

**View Flavor**:
A curated presentation style applied to a generated view. View flavors change layout, typography, spacing, color, and navigation without changing canonical source content; the initial core flavors are `plain`, `dense-review`, `technical-spec`, and `executive-report`.
_Avoid_: Content transformation.

**Flavor Adapter**:
A normalizer that converts external design sources, such as an Open Design MCP or CLI, into the renderer's stable view flavor contract. Flavor adapters keep external design tooling separate from canonical Markdown and generated view semantics.
_Avoid_: Renderer-specific design lock-in.

**Flavor Snapshot**:
A resolved, deterministic view flavor definition used by the renderer to generate HTML. Flavor snapshots record enough identity, version, or hash information for a generated view to be reproduced or diagnosed.
_Avoid_: Live design dependency.

**View Control**:
A non-mutating interactive affordance in a generated view, such as a style switcher, table-of-contents toggle, copy button, search filter, or print control. View controls improve human inspection without changing canonical source content.
_Avoid_: Content editor, hidden state.

**Structural Hook**:
A stable, renderer-emitted styling hook derived from Markdown's native structure, such as headings, paragraphs, lists, tables, code blocks, blockquotes, links, and images. Structural hooks let view flavors style generated views without inferring new meaning from the content.
_Avoid_: Guessed semantic role.

**Role Annotation**:
An explicit Markdown-readable marker that gives a source section a presentation role, such as an Obsidian-style callout or task checkbox. Role annotations allow richer generated views without requiring the renderer to guess meaning.
_Avoid_: Custom opaque syntax, inferred role.

## Context Load

**Context Load**:
The permanent token and attention cost a skill's `description` imposes on every turn by sitting in the initial skill-list metadata. Paid regardless of invocation class.
_Avoid_: Token cost, context bloat.

**Invocation Class**:
Whether a skill is reachable by model inference (`implicit-allowed`) or only by explicit name (`explicit-only`). Controls selection, not metadata presence.
_Avoid_: Invocation mode, trigger mode.

**Description Budget**:
The adopted character limit for a skill `description`, enforced by the static guard in `validate-deps.py`. Codex has a global 8,000-char initial-list budget and shortens descriptions before omitting skills.
_Avoid_: Description length, char limit.

**Selection Mode**:
How the runtime decides to load a skill: autonomously (description match) or by name (user types it or another skill invokes it via `$skill`).
_Avoid_: Discovery mode, pick mode.

**Metadata Cost**:
The context consumed by a skill's name and description being listed in the initial available-skills inventory. Distinct from selection — paid even when implicit invocation is disabled.
_Avoid_: Listing cost, inventory cost.

**Static Guard**:
A CI-time script (`validate-deps.py context-check`) that parses every `SKILL.md` and sibling `agents/openai.yaml`, failing on missing descriptions, budget violations, invocation-class mismatches, or platform drift.
_Avoid_: Linter, validator.

**Runtime Trace**:
A recorded invocation log from a Codex surface proving that explicit-only skills are not implicitly loaded but remain explicitly reachable via `$skill`.
_Avoid_: Invocation receipt, trace log.

**Compatibility Field**:
A frontmatter key recognized by one platform (e.g., `disable-model-invocation`) that has no defined semantics in the target Codex runtime. Must be paired with the supported platform mechanism.
_Avoid_: Legacy field, foreign key.

**80/20 Principle**:
A recursive content-architecture rule: a SKILL.md holds the 20% of knowledge that solves 80% of problems; references hold the deep 80%. Applied at every level — parent spine, subskills, references.
_Avoid_: Pareto content, essential-first.

**Platform Adapter**:
A script-generated mapping from Claude Code canonical frontmatter to a target platform's mechanism (e.g., `disable-model-invocation: true` → `allow_implicit_invocation: false` in `agents/openai.yaml`).
_Avoid_: Sync layer, shim.

**Router Skill**:
A skill with `metadata.manage` that enumerates hidden subskills via `argument-hint`; its `description` is the sole always-loaded pointer (1× ~280c forever), leaves with `managed-by` pay 0 `Metadata Cost` and are loaded via `Read` not `Skill`. See `skills/ai-engineering-expert`. _Avoid_: explicit `router: true` flag (duplicate of `manage`), per-leaf injection.

**Argument Hint**:
The `argument-hint: |-` block scalar enumerating router domains (`skill-authoring -- ... | writing -- ...`). Lives outside 300c `Description Budget`, carries inventory for Codex autocomplete (Pi: injected via `skill-router-injector.ts` extension). _Avoid_: duplicating hint in description verbs.
