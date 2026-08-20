# ADR Template — Hybrid Nygard + Considered Options

The default template for this skill is a hybrid that keeps Nygard scannability while promoting `Considered Options` to a first-class subsection of `Decision`. It exists so correctness-critical decisions can preserve the rejection proof without paying the `Alternatives Considered` top-level tax that Nygard warns against.

> Load once via `read_skill` when creating or reviewing ADRs: `$SKILL_DIR/references/adr-template.md`

## Canonical shape

```markdown
# NUMBER. TITLE

Date: DATE

## Status

STATUS — plus adr-tools relationship lines (Supercedes / Superceded by / Amends / Clarifies) when present

## Context

The issue motivating this decision, and any context that influences or constrains the decision.
Constraints, forces, measurements, and why this decision is being made now.

## Decision

State the chosen decision clearly in 1-3 sentences.

### Considered Options

When trade-offs matter, document rejected alternatives here. Use the depth the decision warrants:

- **Simple / transport decisions** (1–3 alternatives, e.g. payload shape, tooling): compact bullets under `## Decision` are enough:

  - Rejected: Option A — Pros / Cons / Why not
  - Rejected: Option B — Pros / Cons / Why not

- **Correctness-critical / invariant decisions** (e.g. verification model, session keying, anchor canon): expand each option with structured rationale so a future reader will not re-propose it:

  - **expected_hashes (model submits hash of every removed line)** — rejected on the model–tool boundary: makes the model supply verification data and multiplies the hash-copy error surface.
  - **Position-indexed served state** — rejected: false-rejects when an out-of-range edit shifts positions.
  - **Hash-set served state** — rejected: false-accepts when externally-changed content duplicates another served line.

### Why this nesting

`Considered Options` is `###` under `## Decision`, not a top-level `## Alternatives Considered`. This preserves `adr-tools` compatibility (the four Nygard headings remain top-level) while keeping the proof attached to the choice it justifies. Treat `Consequences` as the place for load-bearing assumptions (`linter-only workflow is load-bearing`, `best-effort TOCTOU`, etc.).

## Consequences

What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated.
Record trade-offs, operational impact, and assumptions that would require revisiting the decision if they change.
```

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
- If the repo already has `templates/template.md`, respect it. This file documents the default for repos without a custom template.
- Keep ADRs short: one page is the target for simple decisions; correctness proofs may spill to ~2 pages rather than losing the rejection chain. Move deep analysis to `docs/articles/` or `docs/spec/` and link it.

## Examples

- `pi-better-edit` `docs/adr/0001-served-state-range-verification.md` — expanded `Considered Options` (6 options, each with boundary-based rejection)
- `pi-better-edit` `docs/adr/0007-merged-edit-payload-hoisted-path.md` — compact case (payload shape, provider constraints, path-hoisting)
- `everything-claude-code` `docs/adr/0001-record-architecture-decisions.md` — classic Nygard minimal
