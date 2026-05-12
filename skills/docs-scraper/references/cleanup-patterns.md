# Cleanup Patterns

Common patterns for cleaning scraped documentation.

## Remove Navigation Elements

```python
NAV_CLASSES = [
    "headerlink",
    "viewcode-link",
    "navigation",
    "related",
    "md-nav",
    "breadcrumb",
]

for class_name in NAV_CLASSES:
    for elem in soup.find_all(class_=class_name):
        elem.decompose()
```

## Remove Anchor Links

```python
for link in element.find_all("a", href=True):
    href = link.get("href", "")
    if href.startswith("#"):
        # If resolves to local file, convert
        if href[1:] in anchor_map:
            link["href"] = anchor_map[href[1:]]
        else:
            # Remove link wrapper, keep text
            link.replace_with(link.get_text())
```

## Remove Empty Elements

```python
# Remove empty anchor links (no text, no image)
for link in element.find_all("a"):
    if not link.get_text(strip=True) and not link.find("img"):
        link.decompose()
```

## Remove Footer

```python
FOOTER_MARKERS = [
    "Privacy Policy",
    "Copyright ©",
    "Edit this page",
]

lines = content.split("\n")
for i, line in enumerate(lines):
    if any(marker in line for marker in FOOTER_MARKERS):
        content = "\n".join(lines[:i])
        break
```

## Remove Redundant URLs

```python
# [Function Name](https://docs.nvidia.com/...) -> Function Name
content = re.sub(r"\[([^\]]+)\]\(https://[^)]+\)", r"\1", content)

# Remove empty links: [](url) -> (nothing)
content = re.sub(r"\[\]\([^)]+\)", "", content)
```

## Remove Special Characters

```python
# Zero-width spaces
content = content.replace("​", "")

# Non-breaking spaces
content = content.replace("\xa0", " ")

# Remove inherited markers
content = re.sub(r" \[inherited\]", "", content)
```

## Clean Whitespace

```python
# Remove trailing whitespace from lines
content = "\n".join(line.rstrip() for line in content.split("\n"))

# Collapse multiple blank lines
content = re.sub(r"\n{4,}", "\n\n\n", content)

# Remove leading/trailing blank lines
content = content.strip()
```

## Verification Commands

```bash
# Check for remaining URLs
rg 'https?://' references/

# Check for anchor links
rg '\]\(#' references/

# Check for footer artifacts
rg -i 'privacy|copyright' references/

# Check file sizes
du -sh references/*/
```
