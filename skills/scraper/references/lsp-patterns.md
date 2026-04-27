# LSP Scraper Patterns

Specific patterns for handling Microsoft's LSP 3.17 specification.

## Document Structure

- **Source**: Single-page HTML at `https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/`
- **Content container**: `<div class="md-content">` or `<div role="main">`
- **Heading levels**: h2, h3, h4 (skip h1 — it's TOC)
- **Output**: Flat files with numeric prefixes (0001-xxx.md)

## Emoji Anchor Problem

LSP spec headings contain emoji images:

```html
<h4 id="inline-value-request-leftwards_arrow_with_hook">
  Inline Value Request (<img class="emoji" title=":leftwards_arrow_with_hook:" src="...">)
</h4>
```

This creates:
- Anchor IDs with emoji suffixes: `inline-value-request-leftwards_arrow_with_hook`
- Empty parentheses in titles: `Inline Value Request ()`

## Pattern: Clean Emoji Anchors

**Regex pattern:**

```python
EMOJI_ANCHOR_PATTERN = re.compile(r"-{1,2}(arrow_|leftwards_|rightwards_)[\w_]+$")

def _clean_anchor(self, anchor: str) -> str:
    """Remove emoji anchor suffix from anchor ID."""
    if not anchor:
        return anchor
    return self.EMOJI_ANCHOR_PATTERN.sub("", anchor)
```

**Matches:**
- `inline-value-request-leftwards_arrow_with_hook` → `inline-value-request`
- `inline-value-refresh-request--arrow_right_hook` → `inline-value-refresh-request`

## Pattern: Clean Heading Text

```python
for heading in headings:
    # Remove emoji img tags before extracting text
    heading_copy = heading.__copy__()
    for img in heading_copy.find_all("img", class_="emoji"):
        img.decompose()

    heading_text = heading_copy.get_text(strip=True)
    # Clean empty parentheses: "Title ()" -> "Title"
    heading_text = re.sub(r"\s*\(\s*\)", "", heading_text).strip()
```

## Pattern: Internal Link Resolution

Build anchor-to-file map, then rewrite links:

```python
def _build_anchor_map(self) -> dict[str, str]:
    """Build mapping from anchor IDs to local markdown file paths."""
    anchor_map = {}
    for i, section in enumerate(self.sections, 1):
        if section["anchor"]:
            filename = self._make_filename(section, i)
            # Store lowercase for case-insensitive matching
            anchor_map[section["anchor"].lower()] = filename
    return anchor_map

def _convert_links(self, element, anchor_map):
    """Convert anchor links to local file references."""
    for link in element.find_all("a", href=True):
        href = link.get("href", "")
        if href.startswith("#"):
            anchor = self._clean_anchor(href[1:]).lower()
            if anchor in anchor_map:
                link["href"] = anchor_map[anchor]
```

## Pattern: Section Extraction

LSP splits at h4 level for granular files:

```python
def _extract_sections(self, soup):
    headings = content.find_all(["h2", "h3", "h4"])

    for heading in headings:
        # Extract section number: "3.17.1 Title" -> ("3.17.1", "Title")
        section_match = re.match(r"^(\d+(?:\.\d+)*)\.?\s*(.+)$", heading_text)

        # Collect content until next heading at same or higher level
        content_elements = []
        current = heading.next_sibling
        while current:
            if isinstance(current, Tag) and current.name in ["h1", "h2", "h3", "h4"]:
                break
            if isinstance(current, Tag):
                content_elements.append(current)
            current = current.next_sibling
```

## Special Case: Change Log

Change Log section should NOT be split at h4 — keep as single file:

```python
in_change_log = False

for heading in headings:
    if heading.name in ["h2", "h3"]:
        if "change log" in heading_text.lower():
            in_change_log = True
        elif in_change_log:
            in_change_log = False

    # Skip h4 headings inside Change Log (they become content, not sections)
    if in_change_log and heading.name == "h4":
        continue
```

## Output Format

Each file:

```markdown
#### Section Title

**Source:** https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#section-title

> _Since version 3.17.0_

Content...
```

## Verification Commands

```bash
# Check for emoji artifacts
rg 'arrow_|leftwards_|rightwards_' references/lsp-docs/

# Check for empty parentheses
rg '\(\)\s*$' references/lsp-docs/

# Check internal links resolve
rg '\]\(\d{4}-.*\.md\)' references/lsp-docs/ | head -5

# Verify source URLs
rg '\*\*Source:\*\*' references/lsp-docs/ | head -5
```
