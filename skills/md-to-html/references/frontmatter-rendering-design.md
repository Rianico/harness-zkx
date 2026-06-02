---
name: frontmatter-rendering-design
description: "Design for splitting frontmatter into common message and functional elements"
metadata:
  type: design
---

# Frontmatter Rendering Design

## Understanding Summary

- Split frontmatter into two categories: **common message** (repository, branch, reviewed, files_scanned, model — display as meta overview) and **functional elements** (enums, glossary, statistics — handled with dedicated rendering)
- Statistics dashboard: visual card-based layout using existing `statistics` keys
- Enum visibility: `strength_enum` and `category_enum` displayed as header legend strip + applied to table cells
- Glossary: enhanced two-column treatment at page bottom
- Metadata items can carry optional `css` class for visual identification

## Assumptions

- All `statistics` keys are numeric (int)
- `strength_enum` keys match statistics sub-keys (`strong`, `worth_exploring`, `speculative`)
- Table "Strength" column values match `strength_enum` keys exactly; "Category" column matches by key or label
- Frontmatter schema is backward-compatible — no breaking changes

## Decision Log

| # | Decision | Chosen |
|---|----------|--------|
| 1 | Scope | Full redesign (all three) |
| 2 | Statistics data | Existing keys only |
| 3 | Header order | Dashboard first, meta below |
| 4 | Dashboard layout | Grouped (total / by-strength / effort) |
| 5 | Enum rendering | Header legend strip |
| 6 | Glossary treatment | Enhanced bottom section |
| 7 | Enum on table cells | Yes — color-coded tags |
| 8 | Metadata css hints | Optional `css` field on meta keys |

## Final Design

### Header Layout (top to bottom)

1. Eyebrow + project title
2. Subtitle
3. **Statistics dashboard** — grouped stat cards (total | strength | effort)
4. **Meta block** — repository, branch, reviewed, files_scanned, model (with optional css hints)
5. **Enum legend strip** — strength_enum + category_enum as color-coded chips
6. **Legend swatches** — diagram symbol legend (unchanged)

### Statistics Dashboard

```html
<div class="md-dashboard">
  <div class="md-dashboard-group">
    <div class="md-stat-card">
      <span class="md-stat-label">Candidates</span>
      <span class="md-stat-value">24</span>
    </div>
  </div>
  <div class="md-dashboard-group">
    <div class="md-stat-card badge-strong">...</div>
    <div class="md-stat-card badge-worth">...</div>
    <div class="md-stat-card badge-speculative">...</div>
  </div>
  <div class="md-dashboard-group">
    <div class="md-stat-card">Lines: 1,906</div>
    <div class="md-stat-card">Files: 3</div>
  </div>
</div>
```

### Enum Legend Strip

```html
<div class="md-enum-bar">
  <div class="md-enum-row">
    <span class="md-enum-label">Strength:</span>
    <span class="md-tag badge-strong">Strong</span>
    <span class="md-tag badge-worth">Worth exploring</span>
    <span class="md-tag badge-speculative">Speculative</span>
  </div>
  <div class="md-enum-row">
    <span class="md-enum-label">Category:</span>
    <span class="md-tag md-tag-muted">in-process</span>
    <span class="md-tag md-tag-muted">local-substitutable</span>
    ...
  </div>
</div>
```

### Table Cell Enum Coloring

- Detect "Strength" column by header text → wrap `td` text in `<span class="md-tag {strength_enum.css}">`
- Detect "Category" column → wrap in `<span class="md-tag {category_enum.css}">`
- Lookup by key first, then by label

## BDD Scenarios

**Scenario 1: Standard architecture review with all frontmatter fields**

Given an MD file with `statistics` (candidates, strong, worth_exploring, speculative, total_lines_reviewed, files_involved), `strength_enum`, `category_enum`, and `glossary`
When the file is rendered
Then the HTML header contains (in order): subtitle, dashboard with grouped stat cards, meta block, enum legend strip, legend swatches

**Scenario 2: Minimal frontmatter (no statistics, no enums)**

Given an MD file with only `title` and `project` in frontmatter
When the file is rendered
Then no dashboard or enum bar is present in the header
And the meta block shows only available fields
And the document still renders without errors

**Scenario 3: Table cells with enum coloring**

Given an overview table with "Strength" and "Category" columns
When rendered
Then each Strength cell text is wrapped in `<span class="md-tag {css}">` matching `strength_enum`
And each Category cell text is wrapped in `<span class="md-tag {css}">` matching `category_enum`
And cells with no enum match remain as plain text

## Complexity: lightweight
