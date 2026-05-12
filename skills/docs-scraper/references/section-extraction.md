# Section Extraction Patterns

Common patterns for splitting documentation into sections.

## Pattern: Find Content Container

Documentation typically wraps content in a specific container:

```python
def _find_content(self, soup):
    """Find main content container."""
    selectors = [
        {"class": "md-content"},      # MkDocs (LSP)
        {"role": "main"},             # Semantic HTML
        {"class": "document"},        # Doxygen (CUDA)
        {"class": "body"},            # Fallback
    ]

    for selector in selectors:
        content = soup.find("div", selector) or soup.find("main", selector)
        if content:
            return content

    return soup.find("body")
```

## Pattern: Extract Section Number

Many docs use numbered sections: "3.17.1 Title"

```python
def _parse_heading(self, heading_text: str) -> tuple[str, str]:
    """Extract section number and title from heading."""
    match = re.match(r"^(\d+(?:\.\d+)*)\.?\s*(.+)$", heading_text)
    if match:
        return match.group(1), match.group(2)
    return "", heading_text
```

## Pattern: Collect Section Content

Gather all content between current heading and next heading:

```python
def _collect_content(self, heading: Tag, stop_level: int) -> list[Tag]:
    """Collect content elements until next heading."""
    content_elements = []
    current = heading.next_sibling

    while current:
        if isinstance(current, Tag) and current.name in ["h1", "h2", "h3", "h4"]:
            current_level = int(current.name[1])
            if current_level <= stop_level:
                break
        if isinstance(current, Tag):
            content_elements.append(current)
        current = current.next_sibling

    return content_elements
```

## Pattern: Flat Output (LSP)

For granular, LLM-friendly files, create flat structure with numeric prefixes:

```python
def run(self):
    sections = self._extract_sections(soup)

    for i, section in enumerate(sections, 1):
        filename = f"{i:04d}-{self.sanitize_filename(section['title'])}.md"
        self._save_section(section, self.output_dir / filename)
```

## Pattern: Category Output (CUDA)

For multi-page docs, organize by type:

```python
def run(self):
    modules = self._discover_modules()
    structures = self._discover_structures()

    for module in modules:
        filename = self.sanitize_filename(module["filename"]) + ".md"
        self.scrape_page(module, output_dir / "modules" / filename)
```

## File Naming Convention

```python
def sanitize_filename(self, name: str, section_num: str = "") -> str:
    """Convert title to safe filename."""
    name = re.sub(r"^\d+(\.\d+)*\.?\s*", "", name)  # Remove section number
    name = re.sub(r"#.*$", "", name)                # Remove anchors
    name = re.sub(r"[^\w\s\-_.]", "", name)         # Remove special chars
    name = re.sub(r"\s+", "-", name)                # Spaces to hyphens
    name = name.lower().strip("-")

    if section_num:
        name = f"{section_num}-{name}"

    return name or "index"
```

## Output Format

Each file includes header with source attribution:

```markdown
#### Section Title

**Source:** https://original-url/#anchor

Content...
```
