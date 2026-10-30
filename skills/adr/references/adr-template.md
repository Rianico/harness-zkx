# ADR Template — Hybrid Nygard + Considered Options

The default template for this skill is a hybrid that keeps Nygard scannability while promoting `Considered Options` to a first-class subsection of `Decision`. It exists so correctness-critical decisions can preserve the rejection proof without paying the `Alternatives Considered` top-level tax that Nygard warns against.

Installed copies (e.g. `docs/adr/templates/template.md`) are generated from the marked region of this file via `bin/sync-template`. Never hand-edit the installed copy; edit this file and re-sync.

> Load once via `read_skill` when creating or reviewing ADRs: `$SKILL_DIR/references/adr-template.md`

## Canonical shape

<!-- TEMPLATE-START -->
# NUMBER. TITLE

Date: DATE

## Status

STATUS

<!-- Lifecycle: Proposed | Accepted | Rejected | Deprecated | Superseded. Keep this section to the status word plus relationship lines (Supercedes, Superceded by, Amends, Amended by, Clarifies, Clarified by, Relates to) inserted by `adr new -s` / `adr link`. Rationale belongs in Context/Decision, never here. -->
## Context

The issue motivating this decision, and any context that influences or constrains the decision. Constraints, forces, measurements, and why this decision is being made now. Value-neutral facts; 1-2 paragraphs.

## Decision

State the chosen decision clearly in 1-3 sentences, active voice ("We will …").

### Considered Options

When trade-offs matter, document rejected alternatives here. Depth scales with the decision:

- **Simple / transport decisions** (1–3 alternatives, e.g. payload shape, tooling): compact bullets:

  - Rejected: Option A — Pros / Cons / Why not

- **Correctness-critical / invariant decisions** (e.g. verification model, session keying): expand each option with structured rationale so a future reader will not re-propose it:

  - **Option name** — rejected: <boundary-based reason with measurement or invariant>

Rules: options sit on the same abstraction level (never technology vs product). List the chosen option first when it clarifies comparison. If no genuine alternative existed, omit this subsection — do not invent pseudo-alternatives.

## Consequences

What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated. Include negative and neutral consequences, not just positive ones. Record load-bearing assumptions and confidence level — anything that would require revisiting this decision if it changed. Link out to deep analysis (`docs/articles/`, `docs/spec/`, issues) instead of pasting it here.
<!-- TEMPLATE-END -->

The marked region above is the installable template — byte-identical to what `bin/sync-template` writes. Everything below is guidance, never installed.

### Depth examples

Compact (transport): `- Rejected: Option A — Pros / Cons / Why not` per alternative.

Expanded (invariant proof, e.g. served-state verification rejecting 6 mechanisms):

- **expected_hashes (model submits hash of every removed line)** — rejected on the model–tool boundary: makes the model supply verification data and multiplies the hash-copy error surface.
- **Position-indexed served state** — rejected: false-rejects when an out-of-range edit shifts positions.
- **Hash-set served state** — rejected: false-accepts when externally-changed content duplicates another served line.

### Why this nesting

`Considered Options` is `###` under `## Decision`, not a top-level `## Alternatives Considered`. This preserves `adr-tools` compatibility (the four Nygard headings remain top-level) while keeping the proof attached to the choice it justifies. Treat `Consequences` as the place for load-bearing assumptions (`linter-only workflow is load-bearing`, `best-effort TOCTOU`, etc.).

## Nygard vs hybrid — when each fits

| Aspect | Strict Nygard | Hybrid (this template) |
|---|---|---|
| `## Decision` | 1–3 sentences + 1–3 compact bullets max | 1–3 sentences + `### Considered Options` at variable depth |
| Proof preservation | Compact bullets lose exhaustive rejection chains | Exhaustive proofs stay attached to the decision |
| Tooling | Pure Nygard, minimal | Still Nygard-top-level compatible; deeper proofs are nested |
| Length | ~1 page forced | 1 page for simple ADRs, 2 pages tolerated for invariant proofs |

**Rule of thumb:** if the rejection reasoning is the reason the ADR exists (e.g. `Served-State Range Verification` rejecting 6 mechanisms), use expanded `### Considered Options`. If the decision is a straightforward transport/format choice (e.g. `Compact JSON edit payload`), compact bullets under `## Decision` are sufficient.

## For agents

- After `adr new` generates the file, preserve `Date:` and any `Supercedes`/`Amends` lines under `## Status`. Rewrite only bodies.
- Do not add top-level `## Alternatives Considered`, `## Positive`, `## Negative`, or `## Risks` — use `### Considered Options` inside `## Decision` and `## Consequences` for trade-offs/risks.
- The installed `templates/template.md` is generated from the marked region above via `bin/sync-template`. Never hand-edit it; edit this file and re-sync.
- Keep ADRs short: one page is the target for simple decisions; correctness proofs may spill to ~2 pages rather than losing the rejection chain. Move deep analysis to `docs/articles/` or `docs/spec/` and link it.

## Examples

- `pi-better-edit` `docs/adr/0001-served-state-range-verification.md` — expanded `Considered Options` (6 options, each with boundary-based rejection)
- `pi-better-edit` `docs/adr/0007-merged-edit-payload-hoisted-path.md` — compact case (payload shape, provider constraints, path-hoisting)
- `everything-claude-code` `docs/adr/0001-record-architecture-decisions.md` — classic Nygard minimal
