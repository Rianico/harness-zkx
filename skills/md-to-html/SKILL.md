---
name: md-to-html
description: >-
  Convert structured Markdown into styled HTML using the kami design system. The authoritative source for writing markdown that deterministically converts to curated HTML. Use when generating human-readable reports from LLM-authored markdown, or for skill guidance on script-friendly MD.
argument-hint: |-
  <source.md> [-o output.html] [-f flavor]
---

# md-to-html

Convert structured Markdown into styled, human-readable HTML using the kami design system. This skill is the authoritative source of truth for "how to write markdown that converts deterministically to HTML."

## When to Target This Format

Markdown files are primarily for LLM consumption. Normal markdown works everywhere — Obsidian, GitHub, any viewer.

**Add the extra structure only when the file also needs curated HTML display for humans.** The structure is optional overhead; pay it only when the HTML output justifies it.

When a skill needs HTML output, point it to the [Authoring Guide](references/authoring-guide.md). That document is the textbook — every pattern it describes is guaranteed by the renderer implementation.

## The Contract

Three mechanisms bridge markdown and HTML. The renderer looks for these and only these:

| Mechanism | Markdown | Purpose |
|-----------|----------|---------|
| **Frontmatter** | YAML between `---` fences | Data: metadata, enums, glossary, statistics |
| **Callouts** | `> [!type]` blockquotes | Structured elements: badges, files, legend, problem, warnings |
| **Mermaid** | ` ```mermaid ``` ` fences | Diagrams: graph, sequence, flowchart |

Everything else — headings, paragraphs, lists, bold, code, tables — passes through as standard markdown with typographic CSS classes applied.

## Usage

```bash
uv run python3 skills/md-to-html/scripts/render.py <source.md> [-o output.html] [-f <flavor>]
```

### Arguments

- `source`: Path to the source Markdown file.
- `-o, --output`: Optional output path (defaults to same name as source with `.html` extension). When provided, the HTML links to the skill's own CSS and JS via relative paths instead of inlining them.
- `-f, --flavor`: Design system flavor (default: `kami`). Supported: `kami`, `minimal`.

The HTML output is **repository-local** — it references CSS and JS from the skill's `assets/` and `flavors/` directories rather than copying them alongside the output. Open the HTML from within the repo tree for full styling. Without `-o`, everything is inlined for standalone use.

### Invoking from Another Skill

When a skill needs to render HTML, it invokes md-to-html via the Skill tool — never by hardcoding the script path:

```
Skill tool (md-to-html):
  args: "<source.md> -o <output.html> -f kami"
```

The md-to-html skill owns its script location. Callers declare what they need; the skill resolves how.

## Teaching Consuming Skills

When another skill or agent needs to write markdown that renders as HTML:

1. **Point them to the [Authoring Guide](references/authoring-guide.md)** — the complete textbook for writing compatible markdown
2. **The [Element Mapping](references/element-mapping.md)** is the precise contract — what each markdown element produces in HTML
3. **The [Callouts Manifest](references/flavors/callouts-manifest.md)** lists every supported callout type, its semantics, and when to use it
4. **Key principle**: frontmatter carries data, callouts carry structured elements, Mermaid carries diagrams. Everything else is standard markdown.

A skill only needs to follow the card section order and use the supported callout types. The renderer handles the rest.

## Verification

When developing or modifying a flavor's `style.css`, run the validator to ensure the CSS covers every class, attribute selector, and design token in the rendering contract:

```bash
uv run python3 skills/md-to-html/scripts/validate_flavor.py <flavor>
```

The validator parses the machine-readable manifest from `references/flavors/RENDERING-CONTRACT.md` and reports any missing selectors or tokens. A passing validator is required before committing CSS changes.

To list all required items without running a check:

```bash
uv run python3 skills/md-to-html/scripts/validate_flavor.py --list
```

The self-consistency tests in `tests/md-to-html/test_contract.py` also verify that every class in rendered HTML is documented in the contract and vice versa — run the full suite after contract or renderer changes:

```bash
uv run pytest tests/md-to-html/ -q
```

### Asset Integrity

The `assets/` directory contains immutable files — third-party libraries and skill-owned scripts that must never be manually edited. To verify asset integrity against the locked manifest:

```bash
uv run python3 skills/md-to-html/scripts/verify_assets.py
```

This compares SHA-256 hashes of every file in `assets/` against `assets/MANIFEST.json`. If a file has been modified, deleted, or added without updating the manifest, the check fails.

After intentionally updating an asset (e.g., upgrading mermaid.min.js to a new version), regenerate the manifest:

```bash
uv run python3 skills/md-to-html/scripts/verify_assets.py --update
```

Then manually edit `assets/MANIFEST.json` to record the new `source` and `version` before committing.

## Directory Layout

The skill's directory splits into three zones: skill internals, shared assets, and documentation for consuming skills.

```
skills/md-to-html/
├── SKILL.md               # Skill definition (entry point)
├── references/            # Documentation for consuming skills
│   ├── authoring-guide.md      # Textbook: how to write compatible MD
│   ├── element-mapping.md      # Precise MD→HTML contract
│   ├── frontmatter-rendering-design.md
│   └── flavors/                # Flavor definitions (skill internal)
│       ├── callouts-manifest.md    # Callout type spec + implementer checklist
│       ├── RENDERING-CONTRACT.md   # CSS class manifest for verification
│       ├── kami/style.css      # Kami design system stylesheet
│       ├── kami/reference/     # Kami design reference (DESIGN.md, tokens.css, components.html)
│       ├── minimal/style.css   # Minimal design system stylesheet
│       └── minimal/reference/  # Minimal design reference
├── assets/                # Immutable shared files — consumed by generated HTML
│   ├── mermaid.min.js     # Mermaid diagram renderer (CDN-fetched, do not edit)
│   ├── zoom.js            # Zoom/pan/fullscreen controls (skill-owned, do not edit)
│   └── MANIFEST.json      # SHA-256 manifest for asset integrity verification
└── scripts/               # Implementation (skill internal)
    ├── render.py          # The renderer
    ├── validate_flavor.py # Contract conformance checker
    └── verify_assets.py   # Asset integrity verifier
```

The `assets/` directory is the **immutable shared boundary** — files there are
referenced by generated HTML via relative paths. These files must never be
manually edited. Third-party libraries (mermaid.min.js) are fetched from CDN
and pinned by hash. Skill-owned scripts (zoom.js) are authored in this repo
but treated as immutable artifacts once committed. Run `verify_assets.py` to
confirm integrity before and after any intentional asset change.

The test suite lives at the project root under `tests/md-to-html/` per
project convention.

## Reference Files

| File | Role |
|------|------|
| [Authoring Guide](references/authoring-guide.md) | Textbook for consuming skills — how to write compatible MD |
| [Element Mapping](references/element-mapping.md) | Precise MD→HTML contract — every element, its output, validation rules |
| [Callouts Manifest](references/flavors/callouts-manifest.md) | Authoritative list of all callout types, usage semantics, and flavor implementer checklist |
| [scripts/render.py](scripts/render.py) | The renderer implementation |
| [scripts/validate_flavor.py](scripts/validate_flavor.py) | CSS contract conformance checker |
| [scripts/verify_assets.py](scripts/verify_assets.py) | Asset integrity verifier |
| [assets/](assets/) | Immutable shared files — referenced by generated HTML (mermaid.min.js, zoom.js) |
| [assets/MANIFEST.json](assets/MANIFEST.json) | SHA-256 manifest for asset integrity |
| [references/flavors/kami/](references/flavors/kami/) | Kami design system (style.css + reference docs) |
| [references/flavors/minimal/](references/flavors/minimal/) | Minimal design system |
| [references/flavors/RENDERING-CONTRACT.md](references/flavors/RENDERING-CONTRACT.md) | Machine-readable CSS class manifest for flavor validation |
