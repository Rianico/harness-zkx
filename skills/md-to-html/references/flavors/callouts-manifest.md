# Callouts Manifest

Authoritative list of every callout type the `md-to-html` renderer recognizes. This is the source of truth for callout semantics, usage, and implementation. The renderer's `_process_callouts` method and the flavor CSS are the two implementing surfaces — both must stay in sync with this manifest.

## How to Use This Document

- **Consuming skills (markdown authors)** — see the [[#callout-type-reference|Callout Type Reference]] for what each type means and when to use it
- **Flavor implementers (CSS authors)** — see the [[#flavor-implementer-checklist|Flavor Implementer Checklist]] for the CSS classes each callout requires
- **Renderer maintainers** — any change to callout types must update this manifest, `render.py`, `RENDERING-CONTRACT.md`, and all flavor `style.css` files

## Callout-as-Data-Carrier

Callouts in md-to-html use Obsidian's `> [!TYPE]` syntax as a routing mechanism. The callout type is the routing key — the renderer detects it, extracts the body, and routes it to the appropriate HTML renderer. This is distinct from standard Obsidian callouts used for prose emphasis (`> [!info]`, `> [!danger]`, etc.).

**Principle:** If it's data (structured information the renderer should treat specially), use a callout. If it's decorative emphasis for the reader, use standard markdown.

---

## Callout Card Order

Within a card section (`## N. Title`), callouts must appear in this fixed order:

```
> [!badge]       ← 1. Classification (strength + category)
> [!files]       ← 2. Involved files
> [!legend]      ← 3. Glossary term tags
> [!problem]     ← 4. Problem statement
```

`[!warning]` and `[!note]` can appear anywhere after the core four, typically before or after diagrams.

**Why this order:** Badge and metadata come first (scanning), then the problem (context), then annotations like warnings and notes (qualifiers). This matches how humans read: "what is this?" → "what's wrong?" → "what else should I know?"

---

## Callout Type Reference

### `[!badge]` — Classification Tags

**Purpose:** Classify the card along two dimensions: strength (signal) and category (scope).

**Semantics:**
- **Strength** answers: "How strong is the recommendation evidence?"
- **Category** answers: "What kind of change is this?"

**When to use:** Every numbered section (`## N. Title`) must open with exactly one `[!badge]` callout containing one strength value and one category value.

**When NOT to use:** Non-numbered sections (Top Recommendation, Glossary). Badges only make sense when classifying a candidate/recommendation.

**Body format:** Two values separated by ` · ` (middle dot, U+00B7):
```
> [!badge]
> Strong · in-process
```
The first value must match a key in `frontmatter.strength_enum`. The second must match a key or label in `frontmatter.category_enum`.

**HTML output:**
```html
<div class="md-section-badges">
  <span class="md-tag badge-strong">Strong</span>
  <span class="md-tag md-tag-success">in-process</span>
</div>
```
Placed in the section header, right-adjacent to the H2 title.

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-section-badges` | Flex container for badges (gap: 8px) |
| `.md-tag` | Base tag/chip styling |
| `.badge-strong` | Strong recommendation variant |
| `.badge-worth` | Worth exploring variant |
| `.badge-speculative` | Speculative variant |
| `.md-tag-success` | In-process / safe-to-change category |
| `.md-tag-warn` | Needs-caution category |
| `.md-tag-muted` | External / limited-scope category |
| `.md-tag-info` | Fallback for unmatched items |

---

### `[!files]` — Related File Paths

**Purpose:** List the files involved in or affected by this candidate/recommendation.

**Semantics:**
- Answers: "Which files would I need to touch to implement this?"

**When to use:** Every numbered section should include this callout when file paths are known. Place immediately after `[!badge]`.

**When NOT to use:** When a candidate has no associated files (conceptual candidates). Do not use for listing documentation or reference files — those belong in prose.

**Body format:** Each file on a separate line, prefixed with `- \`` and closed with `` ` ``:
```
> [!files]
> - `domain/services/rename_service.py`
> - `output/formatter.py`
```
Files are joined with ` · ` (middle dot) in the output.

**HTML output:**
```html
<div class="md-card-files">
  domain/services/rename_service.py · output/formatter.py
</div>
```
Placed at the top of the `.md-card`, before the problem blockquote.

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-card-files` | Monospaced file list (meta color, tight leading) |

---

### `[!legend]` — Glossary Term Tags

**Purpose:** Tag the card with glossary terms that appear in the diagrams or analysis for this candidate.

**Semantics:**
- Answers: "Which concepts from the glossary apply to this candidate?"
- Each term should have an entry in `frontmatter.glossary` and an optional entry in `frontmatter.legend` (for diagram symbol styling)

**When to use:** When a card's diagrams or analysis reference glossary terms. Place after `[!files]`.

**When NOT to use:** Do NOT tag every term from the glossary — only the subset relevant to this specific candidate. Do NOT use as a general tag cloud.

**Body format:** Terms separated by ` · ` (middle dot):
```
> [!legend]
> leakage · seam · locality
```
Terms are looked up in `frontmatter.glossary` for tooltip definitions.

**HTML output:**
```html
<div class="md-card-legend-row">
  <span class="md-legend-key-item legend-tag-leakage" data-tooltip="dependency that crosses a seam">leakage</span>
  <span class="md-legend-key-item legend-tag-seam" data-tooltip="where an interface lives">seam</span>
</div>
```
Placed inside the card, below the file list.

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-card-legend-row` | Flex container for per-card legend tags |
| `.md-legend-key-item` | Individual legend pill (shared with header legend) |
| `.legend-tag-{key}::before` | Colored dot via dynamic inline CSS (key from `frontmatter.legend`) |
| `[data-tooltip]` | Glossary definition on hover |

---

### `[!problem]` — Problem Statement

**Purpose:** State the problem this candidate addresses.

**Semantics:**
- Answers: "What is wrong with the current state?"
- The renderer prepends "Problem: " to the content automatically

**When to use:** Every numbered section should include a `[!problem]` callout. Place after `[!legend]`.

**When NOT to use:** Non-numbered sections. Do not use for describing solutions (use `**Solution:**` prose instead).

**Body format:** Free text (single line or multi-line):
```
> [!problem]
> Domain depends on infrastructure via raw imports
```

**HTML output:**
```html
<blockquote class="md-blockquote">
  <p class="md-paragraph">Problem: Domain depends on infrastructure via raw imports</p>
</blockquote>
```

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-blockquote` | Accent left border, faint background, serif font |

---

### `[!warning]` — Warning / Conflict Annotation

**Purpose:** Flag a risk, conflict, or caution about this candidate.

**Semantics:**
- Answers: "What should I be careful about with this candidate?"
- Typical use: ADR conflicts, migration risks, known limitations

**When to use:** When a candidate has a known risk or conflicts with an existing decision. Can appear multiple times per card. Place after `[!problem]` or between diagrams.

**When NOT to use:** For neutral annotations (use `[!note]`). For the problem statement itself (use `[!problem]`).

**Body format:** Free text:
```
> [!warning]
> Contradicts ADR-0007. Must coordinate with team Alpha.
```

**HTML output:**
```html
<blockquote class="md-blockquote md-blockquote-warn">
  <p class="md-paragraph">Contradicts ADR-0007. Must coordinate with team Alpha.</p>
</blockquote>
```

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-blockquote-warn` | Amber left border, warm yellow background |

---

### `[!note]` — Neutral Annotation

**Purpose:** Add a neutral contextual note about this candidate.

**Semantics:**
- Answers: "What else should I know about this candidate?"
- Typical use: implementation status, related work, design notes

**When to use:** When a candidate has supplementary information that isn't a risk or problem. Can appear multiple times per card. Place after `[!problem]` or between diagrams.

**When NOT to use:** For warnings or risks (use `[!warning]`). For the problem statement (use `[!problem]`).

**Body format:** Free text:
```
> [!note]
> This completes ADR-0028 intent. First phase already in progress.
```

**HTML output:**
```html
<blockquote class="md-blockquote md-blockquote-note">
  <p class="md-paragraph">This completes ADR-0028 intent. First phase already in progress.</p>
</blockquote>
```

**Required CSS classes:**
| Class | Purpose |
|-------|---------|
| `.md-blockquote-note` | Accent left border, warm surface background |

---

## Flavor Implementer Checklist

When creating a new flavor, implement CSS for all callout outputs. The renderer produces the same HTML structure regardless of flavor — only the CSS changes.

### Must implement — core callout classes

- [ ] `.md-section-badges` — flex container for badge row
- [ ] `.md-tag` — base tag/chip
- [ ] `.badge-strong` — strong recommendation badge
- [ ] `.badge-worth` — worth-exploring badge
- [ ] `.badge-speculative` — speculative badge
- [ ] `.md-tag-success` — success/positive category tag
- [ ] `.md-tag-warn` — warning category tag
- [ ] `.md-tag-muted` — muted/neutral category tag
- [ ] `.md-tag-info` — info/fallback category tag
- [ ] `.md-card-files` — file path listing
- [ ] `.md-card-legend-row` — per-card legend term container
- [ ] `.md-legend-key-item` — individual legend term pill
- [ ] `.md-legend-key-item::before` — colored dot pseudo-element (size/shape; color is set via dynamic inline CSS)
- [ ] `.md-blockquote` — base blockquote (accent left border)
- [ ] `.md-blockquote-warn` — warning blockquote variant
- [ ] `.md-blockquote-note` — note blockquote variant
- [ ] `.md-paragraph` — paragraph text (used inside blockquotes)
- [ ] `[data-tooltip]` — tooltip hover trigger
- [ ] `[data-tooltip]::after` — tooltip bubble

### Must implement — supporting classes

These classes are used by callout outputs but also have broader scope:

- [ ] `.md-section-header` — section header (contains `.md-section-badges`)
- [ ] `.md-card` — card container (contains file list, legend row, blockquotes)
- [ ] `.md-heading-level-2` — H2 styling (badges align with H2 in section header)
- [ ] `.md-heading-level-3` — H3 styling (legend terms align with H3 in card header)

### Adding a new callout type

When a new callout type is introduced, follow this checklist:

1. **Define the type in this manifest** — name, purpose, semantics, body format, HTML output, CSS classes
2. **Add the type to `render.py`** — update the callout regex in `_process_callouts` and add the handler branch
3. **Update `RENDERING-CONTRACT.md`** — add new CSS classes to the machine-readable manifest
4. **Update all flavor `style.css` files** — each flavor must style the new output
5. **Update `element-mapping.md`** — add the callout to the element mapping table
6. **Update `authoring-guide.md`** — add usage guidance for consuming skills
7. **Add tests** — update `SAMPLE_MD` in `conftest.py` and add test methods
8. **Sync the example file** — update `examples/sample-report.md` to exercise the new callout, keeping it a complete demo of all supported types
9. **Render the example** — run `render.py` on `sample-report.md` and verify the HTML output
10. **Run the validator** against each flavor to confirm coverage

**Sync rule:** `tests/md-to-html/conftest.py` (SAMPLE_MD) and `examples/sample-report.md` must always exercise every callout type in this manifest. The test fixture proves correctness; the example file proves it renders for human review. If one gains a callout without the other, the contract is broken.

**Design rule:** New callout types should be structurally distinct — a different HTML output or a genuinely different semantic role. Do not create a new callout type when an existing one with different body text would suffice. A callout type is a routing key, not a styling variant.
