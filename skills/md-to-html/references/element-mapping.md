# Element Mapping: MD to HTML Contract

Precise contract between markdown input and HTML output. Use this to understand exactly what `render.py` produces for each markdown element.

## Element Mapping Table

| Markdown Element | HTML Output | Script Action |
|---|---|---|
| `frontmatter.title` | `<span class="md-eyebrow">` | Direct insertion |
| `frontmatter.project` | `<h1 class="md-heading-level-1">` | Direct insertion |
| `frontmatter.repository` | `<div class="md-meta-item">` | Label-value pair in header |
| `frontmatter.branch` | `<div class="md-meta-item">` | Label-value pair in header |
| `frontmatter.reviewed` | `<div class="md-meta-item">` | Label-value pair (falls back to `date`) |
| `frontmatter.files_scanned` | `<div class="md-meta-item">` | Label-value pair in header |
| `frontmatter.model` | `<div class="md-meta-item">` | Label-value pair in header |
| `frontmatter.statistics` | `<div class="md-dashboard">` | Renders stat cards (total / by-strength / effort) |
| `frontmatter.legend` | `<div class="md-legend">` | Swatch spans with CSS classes from legend entries |
| `frontmatter.glossary` | `<dl class="md-glossary">` | Term/definition pairs at page bottom |
| `frontmatter.strength_enum` | `<div class="md-enum-row">` | Renders as tag chips in header, colors "Strength" table cells |
| `frontmatter.category_enum` | `<div class="md-enum-row">` | Renders as tag chips in header, colors "Category" table cells |
| `## N. Title` | `<section class="md-section">` | Number extracted, section created |
| `> [!badge]` | `<span class="md-tag {css}">` | Splits on `·`, maps each part via enums |
| `> [!files]` | `<div class="md-card-files">` | Strips `- ` prefix and backticks, joins with ` · ` |
| `> [!legend]` | `<span class="md-tag md-tag-info swatch-{term}">` | Splits on `·`, creates swatch badges |
| `> [!problem]` | `<blockquote class="md-blockquote">` | Wraps with "Problem:" prefix |
| `> [!warning]` | `<blockquote class="md-blockquote md-blockquote-warn">` | Amber left border, warm background |
| `> [!note]` | `<blockquote class="md-blockquote md-blockquote-note">` | Accent left border, warm surface background |
| `**Solution:**` | `<p class="md-paragraph">` | Standard markdown — no special synthesis |
| `**Wins:**` | `<p class="md-paragraph">` + `<ul class="md-list">` | Standard markdown — list rendering fix applied |
| ` ```mermaid ``` ` | `<pre class="mermaid">` inside `<div class="md-mermaid-wrap">` | Code content copied verbatim |
| `## Overview` table | `<table class="md-table">` | Standard markdown table; numeric cells get `md-tabular` |
| `## Top Recommendation` | `<h2>` + `<p>` | Standard markdown — no special synthesis |
| Standard `#`-`####` | `<h1>`-`<h4>` with `md-heading-level-N` | Class mapping |
| Standard `p`, `ul`, `ol`, `li` | Same elements with `md-{element}` classes | Class mapping |
| Standard `blockquote` | `<blockquote class="md-blockquote">` | Class mapping |
| Standard `code` | `<code class="md-code">` | Class mapping (unless inside `<pre>`) |

## Frontmatter Key Types

| Key | Type | Required | Values |
|---|---|---|---|
| `title` | string | Yes | Document title |
| `project` | string | Yes | Project/repo name |
| `strength_enum` | map | Yes | `Strong`, `Worth exploring`, `Speculative` → `{ css: "..." }` |
| `category_enum` | map | Yes | `in_process`, `local_substitutable`, `ports_and_adapters`, `mock` → `{ label: "...", description: "..." }` |
| `legend` | map | No | Term → `{ symbol: "...", css: "..." }` |
| `glossary` | map | No | Term → definition string |
| `statistics` | object | No | `candidates`, `strong`, `worth_exploring`, `speculative`, `total_lines_reviewed`, `files_involved` — rendered as dashboard cards |
| `repository` | string or dict | No | `org/repo` format or `{ value, css }` dict |
| `branch` | string | No | Branch name |
| `reviewed` | string | No | ISO-8601 datetime with timezone |
| `date` | string | No | ISO date (fallback for `reviewed`) |
| `files_scanned` | int | No | Total files read during review |
| `model` | string | No | Model name used for generation |
| `tags` | array | No | String tags (not rendered) |

## Callout HTML Output Specs

The [Callouts Manifest](flavors/callouts-manifest.md) is the authoritative source for callout semantics, usage guidance, and the complete flavor implementer checklist. This section documents the precise HTML output the renderer produces for each callout type — use the manifest for "why" and "when," use this section for "what HTML."

### `[!badge]`

```html
<div class="md-section-badges">
  <span class="md-tag badge-strong">Strong</span>
  <span class="md-tag md-tag-muted">ports & adapters</span>
</div>
```

Placement: Right-adjacent to the H2 title inside `.md-section-header`. Tight horizontal spacing (`gap: 8px`). Enum values (`strength_enum`, `category_enum`) provide the CSS classes.

### `[!files]`

```html
<div class="md-card-files">
  domain/services/rename_service.py · output/formatter.py
</div>
```

Placement: Top of the `.md-card`, before the problem blockquote. Monospace font, meta-color, low horizontal line height. Separators (` · `) evenly spaced.

### `[!legend]`

```html
<div class="md-card-header-row">
  <h3 class="md-heading-level-3">Title</h3>
  <span class="md-tag md-tag-info swatch-leakage">leakage</span>
  <span class="md-tag md-tag-info swatch-seam">seam</span>
</div>
```

Placement: Inside the card header, following the H3 title. `.swatch-{tag}` classes generated from frontmatter `legend` definitions.

### `[!problem]`

```html
<blockquote class="md-blockquote">
  <p class="md-paragraph">Problem: Domain depends on infrastructure...</p>
</blockquote>
```

Placement: Immediately following the file bar. Accent border on the left, faint background.

### `[!warning]`

```html
<blockquote class="md-blockquote md-blockquote-warn">
  <p class="md-paragraph">Contradicts ADR-0007...</p>
</blockquote>
```

Amber left border (`var(--warn)`), warm yellow background (`#fefce8`).

### `[!note]`

```html
<blockquote class="md-blockquote md-blockquote-note">
  <p class="md-paragraph">Completes ADR-0028 intent.</p>
</blockquote>
```

Accent left border (`var(--accent)`), warm surface background.

## Layout Constraints

These constraints are guaranteed by the kami flavor's CSS. Consuming skills can rely on them.

- **Vertical-first**: All content within a card (Problem, Solution, Wins, Diagrams) follows a vertical flow. No horizontal splitting except for H2 badges and H3 legend tags.
- **List preservation**: Paragraphs within list items (`.md-list-item .md-paragraph`) have `max-width: none` to avoid premature line-wrapping.
- **Diagram containment**: Mermaid containers (`.md-mermaid-wrap`) handle overflow gracefully while maintaining `max-width: 100%`.
- **Section numbering**: `## N. Title` headings render with a zero-padded number badge (`.md-section-num`).

## Validation Rules

Scripts deriving HTML from markdown should enforce:

1. Overview table rows must have 6 columns: `#`, `Strength`, `Candidate`, `Files`, `Lines`, `Category`
2. Every Strength value in the overview table must exist in `strength_enum`
3. Every Category value in the overview table must exist in `category_enum` (matched against both keys and label values)
4. `## N. Title` headings must match overview table row `#` column (1-indexed)
5. Each `## N. Title` section must contain, in order: `> [!badge]`, `> [!files]`, `> [!legend]`, `> [!problem]`, `**Solution:**` paragraph, and `**Wins:**` list
6. `statistics.strong` + `statistics.worth_exploring` + `statistics.speculative` must cover all candidate IDs from the overview table
7. All diagrams must use Mermaid blocks — no prose-based or hand-built diagram representations
