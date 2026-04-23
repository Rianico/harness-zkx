---
name: architecture-decision-records
description: Manage architecture decision records with the `adr` CLI. Use for initializing an ADR repository, creating, linking, superseding, listing, and reading ADRs; for deciding whether a new decision relates to older ADRs; and for keeping ADR content short, historical, and compatible with adr-tools templates and status/link behavior.
argument-hint: [init [dir]|create <title>|link <source> <forward-link> <target> <reverse-link>|supersede <old-ref...> <new-title>|list|read <ref|query>]
---

# Architecture Decision Records

Manage ADRs through the installed `adr` command, with AI helping classify relationships, draft concise content, and explain existing decisions.

This skill is reusable by other skills and agents. It does not own a parallel ADR system. The `adr` CLI is the system of record for numbering, filenames, template application, status updates, and link mechanics.

## When to Use

Use this skill when:
- the user says "ADR this", "record this decision", or "why did we choose X?"
- a design or planning workflow reaches a meaningful architectural decision
- a new decision might amend, clarify, relate to, or supersede an older ADR
- another skill or agent needs to list, read, or explain existing ADRs
- another skill or agent needs to create a new ADR without inventing its own format or lifecycle rules

## Supported Operations

### `init [dir]`
Initialize an ADR repository through `adr init`, using the default adr-tools location when no directory is provided.

### `create <title> [--supersede <ref> ...] [--link <target:forward:reverse> ...]`
Create a new ADR through `adr new`, then rewrite the generated file content to fit the actual decision while preserving adr-tools structure and relationship metadata.

### `link <source> <forward-link> <target> <reverse-link>`
Create a relationship between two existing ADRs through `adr link`.

### `supersede <old-ref...> <new-title>`
Create a new ADR that supersedes one or more older ADRs through `adr new -s`.

### `list`
List existing ADRs through `adr list`.

### `read <ref|query>`
Read ADRs by exact reference first, then fall back to keyword search and explanation when the request is phrased as a question such as "why did we choose X?"

## Core Rules

- Always use the installed `adr` command as the backend for ADR lifecycle operations.
- Never invent your own numbering or filename scheme. Let `adr` create filenames like `0001-the-first-decision.md`.
- Keep the default ADR shape Nygard-core when the repository has not customized the template:
  - `## Status`
  - `## Context`
  - `## Decision`
  - `## Consequences`
- If the ADR repository already has `templates/template.md`, respect that template instead of forcing the default shape.
- Keep ADRs short. One page is the target. Move deep analysis to separate documents if needed.
- Treat accepted ADRs as historical records. Prefer creating a new ADR with `-s` or `-l` over rewriting old decisions.
- Preserve adr-tools relationship semantics exactly. If `adr` inserts `Supercedes`, `Superceded by`, `Amends`, or `Clarifies` links, do not break or relocate them.
- When reading ADRs, include lineage and linked relationships when relevant.
- Prefer a quick repository scan before creating a new ADR so related records are not missed.
- Do not create trivial ADRs for local implementation details, naming choices, or minor refactors without architectural significance.

## Default Template Shape

Optimize for the adr-tools-compatible Nygard core template:

```markdown
# NUMBER. TITLE

Date: DATE

## Status

STATUS

## Context

The issue motivating this decision, and any context that influences or constrains the decision.

## Decision

State the chosen decision clearly in 1-3 sentences. When trade-offs matter, include 1-3 compact rejected alternatives under this section instead of adding a heavyweight top-level alternatives section.

## Consequences

What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated.
```

If the ADR repository already has `templates/template.md`, respect it. After `adr` generates the file, preserve the generated structure required by that repository template and keep adr-tools status/link insertion behavior intact.

## Init Workflow

When asked to initialize ADRs:
- Run `adr init` with the provided directory if one was given
- Use the adr-tools default location if no directory is specified
- After initialization, read the created template and first ADR if the caller needs explanation or follow-up edits
- Do not create a parallel README or index scheme outside what the repository already uses

## Pre-Create Discovery Pass

Before creating a new ADR, do a lightweight scan to decide whether the new decision is:
- a brand new ADR
- a superseding ADR
- an amending or clarifying ADR
- a related ADR that should be linked

Use this cheap discovery sequence:
1. Run `adr list`
2. Run `rg` against ADR titles and bodies using keywords from the requested decision
3. Read the best candidate ADR files if relationship classification is still unclear

Bias toward relationship-aware creation instead of isolated creation.

## Relationship Heuristics

Use these heuristics when choosing between plain creation, supersession, and links:

- **Supersede** when an older decision is being replaced and should no longer be treated as the active decision.
- **Amends** when the earlier ADR still stands but needs a meaningful extension or correction.
- **Clarifies** when the newer ADR explains or narrows the interpretation of an older ADR without replacing it.
- **Related link** when there is architectural coupling but no lifecycle replacement.

If the relationship is obvious from the repository scan, proceed with the right `adr` command. If it is materially ambiguous, surface the likely candidates and ask for confirmation.

## Create Workflow

When asked to create an ADR:

1. Extract the decision title and core intent.
2. Run the pre-create discovery pass.
3. Decide whether to use:
   - `adr new <title>`
   - `adr new -s <ref> ... <title>`
   - `adr new -l "<target>:<forward>:<reverse>" ... <title>`
   - or both `-s` and `-l` together
4. Run the `adr` command to generate the numbered file. In non-interactive or agent workflows, ensure editor invocation will not block the session before post-processing the file.
5. Read the generated file.
6. Rewrite only the section bodies so the ADR becomes concise, specific, and historically useful.
7. Preserve:
   - file path
   - numbering
   - title format created by `adr`
   - `Date:` line
   - `## Status` heading
   - any inserted relationship lines under `## Status`
8. Keep content terse and concrete:
   - `Context`: constraints, forces, and why this decision is being made now
   - `Decision`: the chosen direction in clear language, plus 1-3 compact rejected alternatives when they materially clarify the trade-off
   - `Consequences`: trade-offs, operational impact, and risks that actually matter

Use this compact pattern inside `Decision` when alternatives are important:
```markdown
## Decision

We will use X for Y because it best satisfies A and B under constraint C.

- Rejected: Option A
  - Pros: ...
  - Cons: ...
  - Why not: ...
- Rejected: Option B
  - Pros: ...
  - Cons: ...
  - Why not: ...
```

Do not add heavyweight sections such as `Alternatives Considered`, `Positive`, `Negative`, or `Risks` unless the existing repository template already requires them. Prefer compact rejected-alternative bullets inside `Decision` when that reasoning is important.

## Link Workflow

When asked to link ADRs:
- Prefer `adr link <source> <forward-link> <target> <reverse-link>`
- Use exact references if available; otherwise resolve references from `adr list` output plus targeted reads
- After linking, read the affected ADRs if needed to confirm the relationship was inserted as expected

## Supersede Workflow

When asked to supersede:
- Use `adr new -s <ref> ... <new-title>`
- Prefer supersession over editing the old ADR's decision text
- After creation, verify that the older ADR now contains `Superceded by [...]` and the new ADR contains `Supercedes [...]`
- Then rewrite the new ADR's section bodies while keeping those relationship lines intact

## List Workflow

When asked to list ADRs:
- Run `adr list`
- Return the ADR paths or a short human summary if that is more helpful
- If useful, group likely related ADRs around the user's query

## Read Workflow

When asked to read or explain ADRs:
1. Try exact lookup first by number, partial filename, or direct path
2. If exact lookup is not enough, run keyword fallback:
   - `adr list`
   - `rg` for keywords from the query
   - read the most relevant ADRs
3. Summarize:
   - the decision
   - the context that led to it
   - the current status
   - related lineage such as `Supercedes`, `Superceded by`, `Amends`, `Clarifies`
4. If no ADR matches, say so directly and suggest recording one if appropriate

## Writing Guidance

A good ADR produced by this skill should be:
- specific rather than generic
- concise rather than exhaustive
- honest about trade-offs
- include compact rejected alternatives in `Decision` when they help future readers understand why the chosen option won
- readable in a couple of minutes
- useful to a future engineer who needs the why, not just the what

Prefer compact prose over bullet sprawl unless the repository's existing template clearly prefers bullets.

## Integration Guidance

When another skill or agent invokes this skill:
- use this skill as the ADR authority instead of inventing local ADR conventions
- rely on `create`, `link`, `supersede`, `list`, and `read` operations
- preserve the repository's existing adr-tools setup and template if present
- prefer historical continuity through relationships over in-place rewrites of older ADRs
