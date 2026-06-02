# md-to-html: UI/UX & CSS Development Guideline

This document defines the contract between the Markdown "data carriers" (Obsidian-style callouts and frontmatter) and the synthesized HTML/CSS view. Use this as the source of truth for high-fidelity styling.

## 1. Callout-Driven Elements

Callouts are used to carry structured data that requires non-standard rendering.

### 1.1 `[!badge]` (Metadata Badges)
**Source:**
```markdown
> [!badge]
> **Strong** · ports & adapters
```
**Synthesized HTML:**
```html
<div class="md-section-badges">
  <span class="md-tag badge-strong">Strong</span>
  <span class="md-tag md-tag-muted">ports & adapters</span>
</div>
```
**Placement:** Right-adjacent to the H2 title inside `.md-section-header`.
**Styling Requirements:**
- Tight horizontal spacing (`gap: 8px`).
- Integrated look: small text, subtle background, matching the candidate's prominence.
- Enums (`strength_enum`, `category_enum`) provide the CSS classes (e.g., `badge-strong`).

### 1.2 `[!files]` (The File Bar)
**Source:**
```markdown
> [!files]
> - `domain/services/rename_service.py`
> - `output/formatter.py`
```
**Synthesized HTML:**
```html
<div class="md-card-files">
  domain/services/rename_service.py · output/formatter.py
</div>
```
**Placement:** Top of the `.md-card`, before the problem blockquote.
**Styling Requirements:**
- Monospace font (`--font-mono`).
- Meta-color (`--meta` or `--muted`).
- Low horizontal line height to act as a "barcode" of file context.
- Separators (` · `) must be evenly spaced.

### 1.3 `[!legend]` (Architectural Issue Tags)
**Source:**
```markdown
> [!legend]
> leakage · seam · locality
```
**Synthesized HTML:**
```html
<div class="md-card-header-row">
  <h3 class="md-heading-level-3">Title</h3>
  <span class="md-tag md-tag-info swatch-leakage">leakage</span>
  <span class="md-tag md-tag-info swatch-seam">seam</span>
</div>
```
**Placement:** Inside the card header (Row 1), following the H3 title.
**Styling Requirements:**
- Must reflect the "Visual Vocabulary" (swatches).
- `.swatch-[tag]` classes are dynamically generated from frontmatter `legend` definitions (borders, colors, dashes).
- Higher contrast than the generic info tags to indicate they are active architectural "markers".

### 1.4 `[!problem]` (The Hook)
**Source:**
```markdown
> [!problem]
> Domain depends on infrastructure...
```
**Synthesized HTML:**
```html
<blockquote class="md-blockquote">
  <p class="md-paragraph">Problem: Domain depends on infrastructure...</p>
</blockquote>
```
**Placement:** Immediately following the file bar.
**Styling Requirements:**
- Accent border on the left (`border-left: 2px solid var(--accent)`).
- Faint background to pull focus.
- Distinguishable from standard prose blockquotes.

---

## 2. Frontmatter-Driven Styles

### 2.1 The Visual Vocabulary (Legend)
The `legend` frontmatter keys (e.g., `module`, `leakage`) generate a document-level legend and card-level swatches.

**HTML (Document Header):**
```html
<div class="md-legend">
  <div class="md-legend-item">
    <span class="md-legend-swatch swatch-module"></span>
    <span>module</span>
    <span class="md-legend-symbol">(solid box)</span>
  </div>
</div>
```

**CSS Integration:**
The script injects helper classes based on the `css` field in the legend:
- `.swatch-module`: Maps to the visual style of a "module" in diagrams.
- `.md-tag-legend-module`: Used when an issue tag appears in a card.

### 2.2 Table Enums
Data in the "Overview" table columns (`Strength`, `Category`) is automatically wrapped in `md-tag` classes if it matches an enum key.
- Columns: `Strength`, `Category`.
- Colors: Mapped from `strength_enum` and `category_enum`.

---

## 3. General Layout Constraints

- **Vertical-First**: All content within a card (Problem, Solution, Wins, Diagrams) follows a vertical flow. No horizontal splitting except for the H2 badges and H3 legend tags.
- **List Preservation**: Paragraphs within list items (`.md-list-item .md-paragraph`) MUST have `max-width: none` to avoid premature line-wrapping.
- **Diagram Containment**: Mermaid containers (`.md-mermaid-wrap`) must handle overflow gracefully while maintaining `max-width: 100%`.
