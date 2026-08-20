# 11. Markdown as Canonical Source and HTML as Generated View

Date: 2026-06-02

## Status

Accepted

## Context

AI workflow artifacts use Markdown as the canonical source for LLM-facing prose because it is token-efficient, maintainable, diffable, and easy for agents to parse. Rendering the same artifacts as HTML improves layout, visual hierarchy, interactivity, and style for human readers, but treating HTML as a second source creates divergence and unrecoverable edits.

## Decision

We will use Markdown as the canonical source and HTML as a generated view. Generated HTML views are written beside their Markdown source by default, include provenance linking them to the source and flavor snapshot, and may be refreshed only when provenance shows they were generated from the same source. View flavors are applied through stable structural hooks and explicit role annotations, with Open Design MCP/CLI integrations normalized through flavor adapters before rendering.

### Considered Options

- **Rejected: HTML as canonical source** — not token-efficient for LLM parsing; diffs are noisy; agents cannot reliably maintain presentation markup.
- **Rejected: Single-format (Markdown only)** — loses the human-facing improvements (layout, hierarchy, interactivity) that generated views provide.
- **Rejected: HTML views in a separate directory/tree** — breaks locality and provenance; views beside source preserve the source-view linkage and enable atomic refresh checks.

## Consequences

- HTML views are generated artifacts analogous to database views — they must not modify or replace the Markdown source.
- Views are written beside their Markdown source by default, include provenance to source and flavor snapshot, and are refreshable only when provenance matches the current source.
- View flavors are applied through stable structural hooks and explicit role annotations; Open Design MCP/CLI inputs are normalized through flavor adapters before rendering.
- Markdown remains the agent-maintained contract; HTML is discarded and regenerated on demand.
