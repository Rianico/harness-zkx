# Rendering Contract — HTML → CSS Class Map

The `md-to-html` renderer produces a **deterministic** HTML structure from any markdown file that follows the frontmatter schema in `MD-REPORT.md`. This document lists every CSS class, HTML structure, and data attribute the renderer generates, so new flavor authors know exactly what they need to style.

A flavor must provide **one file**: `<flavor>/style.css`. Optionally, `<flavor>/reference/tokens.css` can provide design-token overrides for non-kami flavors.

## Asset pipeline

The renderer writes these files alongside the output HTML:

| File | Source | Purpose |
|------|--------|---------|
| `{stem}_assets/report.css` | `flavors/{flavor}/style.css` | All static CSS for the flavor |
| `{stem}_assets/mermaid.min.js` | `assets/mermaid.min.js` | Mermaid diagram renderer |
| `{stem}_assets/zoom.js` | `assets/zoom.js` | Zoom/pan/fullscreen controls |

Only dynamic content is inlined in the HTML: `.legend-tag-{key}::before { background: {color}; }` rules and `mermaid.initialize(...)`.

---

## Root wrapper

```html
<article class="md-document flavor-{name}">
```

The `flavor-` class lets a flavor scope its rules without leaking.

---

## Header block (`<header class="md-header">`)

### Eyebrow + title + subtitle

```html
<header class="md-header">
  <span class="md-eyebrow">Architecture Review</span>
  <h1 class="md-heading-level-1">llm-lsp-cli</h1>
  <p class="md-subtitle">6 refactoring candidates ranked by leverage, locality, and risk</p>
```

| Class | Element | Comes from |
|-------|---------|------------|
| `.md-eyebrow` | `span` | `frontmatter.title` |
| `.md-heading-level-1` | `h1` | `frontmatter.project` |
| `.md-subtitle` | `p` | Derived from `statistics.candidates` |

### Statistics dashboard

Only present when `frontmatter.statistics` has values.

```html
<div class="md-dashboard">
  <div class="md-dashboard-group">
    <div class="md-stat-card">
      <span class="md-stat-label">Candidates</span>
      <span class="md-stat-value">6</span>
    </div>
  </div>
  <div class="md-dashboard-group">
    <div class="md-stat-card badge-strong">
      <span class="md-stat-label">Strong</span>
      <span class="md-stat-value">3</span>
    </div>
    ...
  </div>
</div>
```

| Class | Role |
|-------|------|
| `.md-dashboard` | Flex container for stat groups |
| `.md-dashboard-group` | Groups related stat cards (total vs. strength) |
| `.md-stat-card` | Individual stat card (flex:1, dashed border) |
| `.md-stat-label` | Stat label (uppercase, small) |
| `.md-stat-value` | Stat number (large, bold) |
| `.badge-strong` / `.badge-worth` / `.badge-speculative` | Optional tint class on stat card |

### Meta block

Presents `frontmatter` fields: `repository`, `branch`, `reviewed`, `files_scanned`, `model`, plus derived `total_lines_reviewed` and `files_involved`.

```html
<div class="md-meta">
  <div class="md-meta-item">
    <span class="md-meta-label">Repository</span>
    <span class="md-meta-value">llm-lsp-cli</span>
  </div>
  ...
</div>
```

| Class | Role |
|-------|------|
| `.md-meta` | Flex container (wrapping, gap) |
| `.md-meta-item` | Label+value pair |
| `.md-meta-label` | Uppercase label |
| `.md-meta-value` | Value text |
| `.md-tabular` | Added to numeric values (tab-nums) |

### Enum legend strip

Present when `frontmatter.strength_enum` or `frontmatter.category_enum` exists.

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
    <span class="md-tag md-tag-success">in-process</span>
    <span class="md-tag md-tag-muted">mock</span>
  </div>
</div>
```

| Class | Role |
|-------|------|
| `.md-enum-bar` | Container for all enum rows (flex column) |
| `.md-enum-row` | Single enum type row (flex row) |
| `.md-enum-label` | "Strength:" / "Category:" label |
| `.md-tag` | Base tag/badge class |
| `.badge-strong` / `.badge-worth` / `.badge-speculative` | Strength badge variant |
| `.md-tag-success` / `.md-tag-warn` / `.md-tag-muted` / `.md-tag-info` | Tag color variant |
| `[data-tooltip]` | Category tag may have tooltip with description (see Tooltips section) |

### Legend key

Present when `frontmatter.legend` exists.

```html
<div class="md-legend-key">
  <span class="md-legend-key-label">Legend</span>
  <span class="md-legend-key-item legend-tag-module" data-tooltip="anything with an interface and an implementation">module</span>
  <span class="md-legend-key-item legend-tag-seam" data-tooltip="where an interface lives">seam</span>
  ...
</div>
```

| Class | Role |
|-------|------|
| `.md-legend-key` | Flex container for legend label + items |
| `.md-legend-key-label` | "Legend" label (uppercase) |
| `.md-legend-key-item` | Individual legend pill |
| `.md-legend-key-item::before` | Colored dot (8×8px, border-radius: 50%) |
| `.legend-tag-{key}::before` | **Dynamic**: sets `background: {color}` via inline `<style>` |
| `[data-tooltip]` | Glossary definition on hover (see Tooltips section) |

**Legend dot colors** are generated from `frontmatter.legend[key].css`:
- `border-slate-400` → `#94a3b8`
- `border-red-500` → `#ef4444`
- `border-emerald-600` → `#059669`

These are the only supported colors. A flavor must handle the `.legend-tag-{key}::before` selector (the dynamic inline CSS sets `background`, flavor CSS handles `::before` size/shape).

---

## Section structure (`<section class="md-section">`)

### Numbered sections (candidate cards)

```html
<section class="md-section md-section-level-1" id="lspclient-decomposition">
  <div class="md-section-header">
    <span class="md-section-num">01</span>
    <h2 class="md-heading-level-2">LSPClient Decomposition</h2>
    <div class="md-section-badges">
      <span class="md-tag badge-strong">Strong</span>
      <span class="md-tag md-tag-success">in-process</span>
    </div>
  </div>
  <div class="md-card">
    <!-- card content -->
  </div>
</section>
```

| Class | Role |
|-------|------|
| `.md-section` | Section wrapper |
| `.md-section-level-1` / `.md-section-level-2` / `.md-section-level-3` | Depth margin |
| `.md-section-header` | Number + heading + badges row |
| `.md-section-num` | Zero-padded number (e.g. "01") |
| `.md-section-badges` | Strength + category badge container |
| `.md-card` | White card container for content |

### Non-numbered sections (Top Recommendation, Glossary)

```html
<section class="md-section">
  <h2 class="md-heading-level-2" id="glossary">Glossary</h2>
  <div class="md-card">
    <!-- card content -->
  </div>
</section>
```

When h2 is a direct child of `.md-section` (no `.md-section-header` wrapper), the flavor should provide a visual separator between heading and card body. Kami uses `margin-bottom + border-bottom` on `.md-section > .md-heading-level-2`.

---

## Card content

### Callout blocks

From `> [!warning]` and `> [!note]` callouts in the markdown:

```html
<blockquote class="md-blockquote md-blockquote-warn">
  <p class="md-paragraph">ADR note: Completes ADR-0028 intent</p>
</blockquote>
```

| Class | Trigger |
|-------|---------|
| `.md-blockquote` | Base blockquote |
| `.md-blockquote-warn` | `[!warning]` callout |
| `.md-blockquote-note` | `[!note]` callout |

### Problem blockquote

```html
<blockquote class="md-blockquote">
  <p class="md-paragraph">Problem: Two independent code paths for every LSP method</p>
</blockquote>
```

### File list

```html
<div class="md-card-files">lsp/client.py · lsp/constants.py</div>
```

Monospaced dot-separated file paths.

### Per-card legend row

From `> [!legend]` callouts inside a section:

```html
<div class="md-card-legend-row">
  <span class="md-legend-key-item legend-tag-leakage" data-tooltip="dependency that crosses a seam">leakage</span>
  <span class="md-legend-key-item legend-tag-shallow_module" data-tooltip="interface nearly as complex as the implementation">shallow module</span>
</div>
```

Uses the same `.md-legend-key-item` and `.legend-tag-{key}` classes as the header legend, but scaled slightly smaller via `.md-card-legend-row` context.

### Mermaid diagram

```html
<div class="md-mermaid-wrap">
  <div class="md-mermaid-viewport">
    <pre class="mermaid">graph TD ...</pre>
  </div>
  <div class="md-mermaid-zoom">
    <button class="zoom-in">+</button>
    <button class="zoom-out">−</button>
    <button class="zoom-fullscreen">⛶</button>
  </div>
</div>
```

| Class | Role |
|-------|------|
| `.md-mermaid-wrap` | Outer container (relative positioned for zoom buttons) |
| `.md-mermaid-viewport` | Overflow-hidden viewport (scrolls when zoomed) |
| `pre.mermaid` | Mermaid diagram source (rendered by mermaid library) |
| `.md-mermaid-zoom` | Zoom control button stack (opacity:0 on wrap hover) |
| `.zoom-in` / `.zoom-out` / `.zoom-fullscreen` | Click targets for JS zoom controls |
| `[data-zoom]` | **Dynamic**: set on wrap when scale != 1, enables scrolling viewport |

### List items

```html
<ul class="md-list">
  <li class="md-list-item">
    <p class="md-paragraph">locality: normalization lives in one module</p>
  </li>
</ul>
```

| Class | Note |
|-------|------|
| `.md-list-item .md-paragraph` | Flavor should set `max-width: none` to prevent premature wrapping |

### Paragraphs

```html
<p class="md-paragraph">...</p>
```

`70ch` max-width recommended.

### Table

```html
<table class="md-table">
  <thead>
    <tr><th>Candidate</th><th>Strength</th><th>Category</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><a class="md-overview-link" href="#lspclient-decomposition">LSPClient Decomposition</a></td>
      <td><span class="md-tag badge-strong">Strong</span></td>
      <td><span class="md-tag md-tag-success" data-tooltip="pure computation, no I/O">in-process</span></td>
    </tr>
  </tbody>
</table>
```

| Class | Role |
|-------|------|
| `.md-overview-link` | Anchor link to candidate section (underline-on-hover) |
| `.md-tag` | Strength/category badge in table cells |
| `.md-tabular` | Tabular-nums on numeric cells |
| `[data-tooltip]` | Category descriptions (see Tooltips) |

---

## Glossary

```html
<section class="md-section">
  <hr class="md-hr">
  <h2 class="md-heading-level-2" id="glossary">Glossary</h2>
  <div class="md-card">
    <dl class="md-glossary">
      <dt class="md-glossary-term">Module</dt>
      <dd class="md-glossary-def">anything with an interface and an implementation</dd>
    </dl>
  </div>
</section>
```

| Class | Role |
|-------|------|
| `.md-glossary` | Grid (dt:160px, dd:1fr) |
| `.md-glossary-term` | Term cell |
| `.md-glossary-def` | Definition cell |

---

## Headings (typography)

```html
<h1 class="md-heading-level-1">...</h1>   <!-- Report title / page title -->
<h2 class="md-heading-level-2">...</h2>   <!-- Section titles -->
<h3 class="md-heading-level-3">...</h3>   <!-- Sub-section titles -->
<h4 class="md-heading-level-4">...</h4>   <!-- Detail column headings -->
```

---

## Inline elements

| Class | On | Role |
|-------|----|------|
| `.md-code` | `<code>` | Inline code (accent color, bg tint) |
| `.md-mono` | Any | Monospace font family |
| `.md-tabular` | Any | Tabular-nums variant |
| `.md-hr` | `<hr>` | Horizontal rule (flavor may style or use defaults) |

---

## Tooltip contract

Elements with `data-tooltip` attribute should show a popup on hover:

```html
<span data-tooltip="anything with an interface and an implementation">module</span>
```

| Class | Behavior |
|-------|----------|
| `[data-tooltip]` | `position: relative; cursor: help` |
| `[data-tooltip]::after` | `content: attr(data-tooltip)` — the tooltip bubble |
| `[data-tooltip]:hover::after` | Visible state (opacity:1, visibility:visible, translateY:0) |

The tooltip pseudo-element should be:
- Positioned above the element (`bottom: calc(100% + gap)`)
- Animated (opacity + translateY transition)
- Backdrop-blurred (glass effect recommended but not required)
- `width: max-content; max-width: 340px`

Note: `::before` is used for the legend dot on `.md-legend-key-item`. Only `::after` is used for tooltips — no pseudo-element conflict.

---

## JS data attributes (dynamic)

| Attribute | On | Set by |
|-----------|----|--------|
| `[data-zoom]` | `.md-mermaid-wrap` | zoom.js when scale != 1 |
| `[data-tooltip]` | legend items, category tags | render.py from glossary/category descriptions |

---

## Mermaid override contract

When styling mermaid diagrams, selectors must be scoped under `.md-mermaid-wrap`:

```
.md-mermaid-wrap .node rect       → node backgrounds & borders
.md-mermaid-wrap .edgePath path   → edge lines
.md-mermaid-wrap marker path      → arrowheads
.md-mermaid-wrap .edgeLabel       → edge labels
.md-mermaid-wrap .nodeLabel       → node labels
.md-mermaid-wrap .cluster rect    → subgraph backgrounds
```

These override Mermaid's inline SVG styles — `!important` is expected and appropriate here.

---

## Responsive breakpoints

The flavor should handle these standard breakpoints:

| Width | Changes |
|-------|---------|
| `768px` | Container padding reduces; glossary collapses to single column |
| `480px` | Card padding reduces |

Container queries (`@container`): some components (`.md-detail-grid`, `.md-diagram-grid`, `.md-summary-row`) use container queries rather than viewport media queries.

---

## CSS custom properties (design tokens)

A flavor should define these `:root` variables:

```css
:root {
  /* Backgrounds */
  --bg: #f5f4ed;
  --surface: #faf9f5;
  --surface-warm: #e8e6dc;

  /* Foreground */
  --fg: #141413;      /* Primary text (NOT --text) */
  --fg-2: #3d3d3a;    /* Secondary text */
  --muted: #504e49;    /* Muted text */
  --meta: #6b6a64;    /* Metadata/label text */

  /* Borders */
  --border: #e8e6dc;
  --border-soft: #e5e3d8;

  /* Accent */
  --accent: #1b365d;
  --accent-on: #faf9f5;
  --accent-light: #2d5a8a;

  /* Semantic */
  --success: #4a6b3a;
  --warn: #8a6b1f;
  --danger: #8a3a30;

  /* Tag backgrounds */
  --tag-bg-faint: #eef2f7;
  --tag-bg-soft: #e4ecf5;

  /* Typography */
  --font-display: Charter, Georgia, serif;
  --font-body: Charter, Georgia, serif;
  --font-mono: "JetBrains Mono", "SF Mono", Consolas, monospace;

  /* Font sizes */
  --text-xs: 11px;
  --text-sm: 12px;
  --text-base: 14px;
  --text-md: 15px;
  --text-lg: 17px;
  --text-xl: 22px;
  --text-2xl: 32px;

  /* Leading */
  --leading-display: 1.1;
  --leading-body: 1.55;

  /* Tracking */
  --tracking-eyebrow: 1.2px;
  --tracking-label: 0.4px;

  /* Radii */
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  /* Elevation */
  --elev-raised: 0 4px 24px rgba(0, 0, 0, 0.05);

  /* Motion */
  --motion-base: 200ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);

  /* Layout */
  --container-max: 1120px;
  --container-gutter: 64px;
}
```

The variable `--text` does NOT exist — use `--fg` for foreground color.

---

## Creating a new flavor

1. Create `flavors/{name}/style.css` with the above CSS custom properties and all listed classes
2. Optionally `flavors/{name}/reference/tokens.css` for `:root` token overrides (only read when flavor != "kami")
3. Render with `-f {name}`

**Minimal checklist of CSS sections a flavor must define:**
- [ ] `:root` design tokens
- [ ] Reset and typography (`*.md-heading-level-*`, `.md-paragraph`, `.md-eyebrow`, `.md-subtitle`)
- [ ] Header (`.md-header`, `.md-meta`, `.md-dashboard`, `.md-enum-bar`, `.md-legend-key`)
- [ ] Section structure (`.md-section`, `.md-section-header`, `.md-card`)
- [ ] Card content (`.md-blockquote`, `.md-card-files`, `.md-card-legend-row`)
- [ ] Mermaid wrapping (`.md-mermaid-wrap`, `.md-mermaid-zoom`, `pre.mermaid`, zoom buttons)
- [ ] Tags and badges (`.md-tag`, `.badge-*`, `.md-tag-*`)
- [ ] Tables (`.md-table`, `.md-overview-link`)
- [ ] Tooltip (`[data-tooltip]::after`)
- [ ] Glossary (`.md-glossary`, `.md-glossary-term`, `.md-glossary-def`)
- [ ] Lists (`.md-list`, `.md-list-item`)
- [ ] Responsive (`@media (max-width: 768px)`)
- [ ] Print (`@media print`)

---

## Required classes (machine-readable)

This section is parsed by `scripts/validate_flavor.py`. Do not change the comment markers.

<!-- required-classes:start -->
# ── Root ──
.md-document
# ── Typography ──
.md-heading-level-1
.md-heading-level-2
.md-heading-level-3
.md-heading-level-4
.md-paragraph
.md-eyebrow
.md-subtitle
.md-tabular
# ── Header ──
.md-header
.md-dashboard
.md-dashboard-group
.md-stat-card
.md-stat-label
.md-stat-value
.md-meta
.md-meta-item
.md-meta-label
.md-meta-value
.md-enum-bar
.md-enum-row
.md-enum-label
.md-legend-key
.md-legend-key-label
.md-legend-key-item
.md-legend-key-item::before
# ── Sections & Cards ──
.md-section
.md-section-level-1
.md-section-level-2
.md-section-level-3
.md-section-header
.md-section-num
.md-section-badges
.md-card
.md-card-legend-row
.md-card-files
.md-blockquote
.md-blockquote-warn
.md-blockquote-note
# ── Lists ──
.md-list
.md-list-item
.md-list-item .md-paragraph
# ── Mermaid ──
.md-mermaid-wrap
.md-mermaid-viewport
.mermaid
.md-mermaid-zoom
# ── Tags / Badges ──
.md-tag
.md-tag-success
.md-tag-warn
.md-tag-muted
.md-tag-info
.badge-strong
.badge-worth
.badge-speculative
# ── Tables ──
.md-table
.md-overview-link
# ── Glossary ──
.md-glossary
.md-glossary-term
.md-glossary-def
# ── Inline elements ──
.md-code
.md-hr
# ── Attribute selectors ──
[data-tooltip]
[data-tooltip]::after
[data-zoom]
# ── Design tokens ──
--bg
--surface
--surface-warm
--fg
--fg-2
--muted
--meta
--border
--border-soft
--accent
--accent-on
--accent-light
--success
--warn
--danger
--tag-bg-faint
--tag-bg-soft
--font-display
--font-body
--font-mono
--text-xs
--text-sm
--text-base
--text-md
--text-lg
--text-xl
--text-2xl
--leading-display
--leading-body
--tracking-eyebrow
--tracking-label
--radius-xs
--radius-sm
--radius-md
--radius-lg
--radius-xl
--elev-raised
--motion-base
--ease-standard
--container-max
--container-gutter
<!-- required-classes:end -->
