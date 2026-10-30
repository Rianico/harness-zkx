---
name: adr
description: >-
  ADR lifecycle manager via the `adr` CLI. Creates, links, supersedes, and verifies decision records. Use when recording architectural decisions, weighing trade-offs, or diagnosing ADR drift.
argument-hint: |-
  [init [dir]|create <title>|link <source> <forward-link> <target> <reverse-link>|supersede <old-ref...> <new-title>|list|read <ref|query>]
---

# Architecture Decision Records

Manage ADRs through the installed `adr` command. The model classifies relationships, drafts concise content, and explains existing decisions.

This skill is reusable by other skills and agents. It owns no parallel ADR system. The `adr` CLI remains the system of record for numbering, filenames, templates, status updates, and link mechanics.

## Philosophy and Invariants

Route every lifecycle operation through the installed `adr` command. Never invent numbering or filename schemes.

The log is append-only. Bodies freeze once accepted. Change history only through new records, `adr new -s`, or `adr link`.

Status values are `Proposed`, `Accepted`, `Rejected`, `Deprecated`, and `Superseded`. Keep `## Status` to the status word plus relationship lines.

Write the ADR as `Proposed` before implementing when possible. Mark `Accepted` on agreement. Record brownfield decisions retroactively with the original decision date.

Keep one decision per record. Split phased decisions into linked records. State low confidence in Consequences to flag future reconsideration.

A reversal is a new record via `adr new -s`. The old record keeps its body and gains a `Superceded by` line.

The repository `templates/template.md` wins when present. Otherwise install the canonical shape with `$SKILL_DIR/bin/sync-template`. Never hand-edit the installed copy.

Edit `$SKILL_DIR/references/adr-template.md` and re-sync instead. That file owns nesting, depth, and examples.

Prefix `PATH` with `$SKILL_DIR/bin` so the fail-loudly shim guards `adr`. It refuses directory-touching commands (exit 2) when no ADR directory resolves. It passes everything else through untouched.

Fresh worktrees may lack gitignored `.adr-dir` until the asynchronous post-start copy lands. Remedy: run `adr init docs/adr` or wait for the copy, then retry.

Exit 64 means the real `adr` is missing or shim recursion was detected. Set `ADR_REAL` to the real binary path. Set `ADR_ALLOW_DEFAULT=1` (exactly `1`) for deliberate `doc/adr` projects.

Mechanics and exit codes live in `$SKILL_DIR/bin/adr`. Tests live in `tests/adr/`.

Use exactly these verbs. Never invent custom verbs.

| Forward (in the new ADR) | Reverse (inserted into the old ADR) | Use when |
|---|---|---|
| `Supercedes` | `Superceded by` | old decision is replaced; via `adr new -s` only |
| `Amends` | `Amended by` | old ADR still stands, needs extension or correction |
| `Clarifies` | `Clarified by` | new ADR narrows the interpretation of the old one |
| `Relates to` | `Relates to` | architectural coupling, no lifecycle change |

Write one link line per relation. Never duplicate the same relation to the same target.
The CLI spells it `Supercedes` with a double 'e'. Never normalize the spelling. Tool parsing depends on the exact bytes.

## When to Use

- The user says "ADR this", "record this decision", or "why did we choose X?"
- A design or planning workflow reaches an architectural decision.
- A new decision may amend, clarify, relate to, or supersede an older ADR.
- Another skill or agent needs to list, read, explain, or create ADRs.
- A drifted ADR log needs unification.

Offer an ADR only when all three hold. Missing any one means a design-doc entry, a code comment, or nothing.

1. Hard to reverse: changing course later costs real effort.
2. Surprising without context: a future reader will ask why.
3. The result of a real trade-off: genuine alternatives existed.

Qualifying topics include architectural shape, integration patterns, lock-in technology choices, boundary ownership, deliberate deviations, invisible constraints, and non-obvious rejections.

Skip trivial records for local details, naming, or minor refactors.

## Phase 1 — Establish Repository

1. Run `adr init` with the given directory, or the default location otherwise.
2. Read the created template and first ADR when the caller needs follow-up edits.
3. Create no parallel README or index scheme outside the repository layout.

Completion: `adr list` exits 0 inside the repository.

## Phase 2 — Discover Relationships

1. Run `adr list` to see existing records.
2. Search titles and bodies with `rg` using keywords from the request.
3. Read the best candidate files when classification stays unclear.
4. Classify the outcome as brand-new, superseding, amending, clarifying, or related.
5. Bias toward relationship-aware creation over isolated creation.

Completion: the relationship class is named before any `adr new` runs.

Use these heuristics to pick the class.

- Supersede when an older decision stops being the active decision.
- Amend when the earlier ADR stands but needs extension or correction.
- Clarify when the new ADR narrows an older interpretation without replacing it.
- Link with `Relates to` for architectural coupling without lifecycle change.

Proceed directly when the relationship is obvious from the scan. Surface candidates and ask when the choice is materially ambiguous.

Ask with this dialog when ambiguity blocks creation.

```yaml
Dialog:
  header: "ADR Relationship"
  question: "This new decision may relate to existing ADRs. What is the relationship?"
  multipleChoice: false
  options:
    - label: "Supersede [ADR-X]"
      description: "Replace an older ADR as the active decision"
    - label: "Amend [ADR-X]"
      description: "Extend or correct an earlier ADR"
    - label: "Link to [ADR-X]"
      description: "Related but not superseding or amending"
    - label: "Standalone"
      description: "No relationship to existing ADRs"
```

## Phase 3 — Create, Link, or Supersede

### Create

1. Extract the decision title and core intent.
2. Run the Phase 2 discovery pass first.
3. Pick `adr new`, `adr new -s`, `adr new -l`, or both flags together.
4. Generate the file with `EDITOR=true adr new` so the editor never blocks.
5. Read the generated file.
6. Rewrite section bodies only, preserving paths, numbering, titles, dates, and status lines.
7. Write value-neutral Context, a 1-3 sentence Decision, and Consequences with trade-offs and assumptions.
8. Keep the record near one page. Move deep analysis to linked documents.
9. Preserve inserted `Supercedes`, `Amends`, `Clarifies`, and `Relates to` lines exactly.

Document rejected alternatives in `### Considered Options` when trade-offs matter. Use compact bullets for simple choices and expanded proof for invariant decisions.

Omit the subsection when no genuine alternative existed. Never invent pseudo-alternatives.

Add no top-level alternatives, positive, negative, or risks sections. Keep proofs nested under Decision and trade-offs in Consequences.

Follow the canonical shape in `$SKILL_DIR/references/adr-template.md`.

Completion: the new file keeps its generated structure and relationship lines.

### Link

- Link with `adr link` using exact references from `adr list`.
- Confirm insertion by reading the affected records.

### Supersede

- Create the replacement with `adr new -s <ref> <new-title>`.
- Prefer supersession over editing the old decision text.
- Verify the old record gained `Superceded by` and the new one holds `Supercedes`.
- Rewrite the new bodies while keeping relationship lines intact.

## Phase 4 — Read and Explain

The CLI has no `read` subcommand. Reading means inspecting the files found via `adr list` or `rg`.

1. Try exact lookup first by number, partial filename, or direct path.
2. Fall back to `adr list`, keyword `rg`, and reading the best matches.
3. Summarize the decision, its context, its status, and its lineage.
4. Group related ADRs around the query when that helps.
5. Report no match directly and suggest recording one when appropriate.

Completion: the answer names status plus lineage, or states that no ADR matches.

## Integration Guidance

Treat this skill as the ADR authority. Invent no local ADR conventions.

Rely on create, link, supersede, list, and read operations.

Preserve the existing adr-tools setup and repository template.

Prefer historical continuity through relationships over in-place rewrites.

Unify a drifted log via `$SKILL_DIR/references/remediation.md` (inventory, remap, audit, verify).

## References

- [adr-template.md](references/adr-template.md) — canonical hybrid template and depth guidance. Use when drafting or reviewing ADR bodies.
- [remediation.md](references/remediation.md) — drifted-log unification procedure. Use when a log predates the canonical template or shows dangling links.
- `$SKILL_DIR/bin/adr` — fail-loudly shim source and exit-code contract. Use when diagnosing refused commands or exit 2 and 64.
- `$SKILL_DIR/bin/sync-template` — template installer from the marked region. Use when a repository template is missing or stale.
