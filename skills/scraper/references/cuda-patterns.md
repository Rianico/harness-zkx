# CUDA API Scraper Patterns

Specific patterns for NVIDIA CUDA Runtime and Driver API documentation.

## Document Structure

- **Source**: Multi-page documentation
  - Runtime: `https://docs.nvidia.com/cuda/cuda-runtime-api/`
  - Driver: `https://docs.nvidia.com/cuda/cuda-driver-api/`
- **Entry points**: `modules.html` (function modules), `annotated.html` (data structures)
- **Output**: `modules/` + `data-structures/` directories

## Pattern: Multi-Page Discovery

Discover all pages from index pages:

```python
def _discover_modules(self) -> list[dict[str, str]]:
    """Discover all module pages from modules.html"""
    soup = self._fetch_with_cache(
        urljoin(self.base_url, "modules.html"),
        "modules.html"
    )

    # Driver API pattern
    pattern = r"group__CUDA__.*\.html"
    # Runtime API pattern
    pattern = r"group__CUDART.*\.html"

    modules = []
    seen = set()
    for link in soup.find_all("a", href=re.compile(pattern)):
        href = link.get("href")
        title = link.get_text(strip=True)
        if href and title and href not in seen:
            seen.add(href)
            modules.append({
                "url": urljoin(self.base_url, href),
                "filename": href,
                "title": title,
            })
    return modules
```

## Pattern: Cleanup Pipeline

CUDA docs have significant redundancy. Apply cleanup in order:

### 1. Remove Duplicate Function TOC

```python
def _remove_toc(self, content: str) -> str:
    """Remove duplicate function TOC from content."""
    lines = content.split("\n")
    cleaned_lines = []
    in_toc = False

    for line in lines:
        # Detect TOC lines: ") [" in line and "](#" in line
        if ") [" in line and "](#" in line and "CUresult" in line:
            in_toc = True
            continue
        if line.strip() == "### Functions":
            in_toc = False
        if not in_toc:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)
```

### 2. Remove Footer

```python
footer_markers = [
    "![](https://docs.nvidia.com/cuda/common/formatting/NVIDIA-LogoBlack.svg)",
    "[Privacy Policy]",
    "Copyright ©",
]
lines = content.split("\n")
for i, line in enumerate(lines):
    if any(marker in line for marker in footer_markers):
        content = "\n".join(lines[:i])
        break
```

### 3. Remove Redundant URLs

```python
# [cudaMalloc](https://docs.nvidia.com/...) -> cudaMalloc
content = re.sub(r"\[([^\]]+)\]\(https://[^)]+\)", r"\1", content)
# Remove empty links
content = re.sub(r"\[\]\(https://[^)]+\)", "", content)
```

### 4. Remove Anchor Links

```python
# [cudaErrorInvalidValue](#cudaErrorInvalidValue) -> cudaErrorInvalidValue
content = re.sub(r"\[([^\]]+)\]\(#[^\)]+\)", r"\1", content)
```

## Pattern: Two-Phase Processing

1. **Scrape phase**: Fetch and convert to markdown, save to cache
2. **Cleanup phase**: Process cached files, save to final output

## Output Structure

```
cuda-runtime-docs/
├── INDEX.md
├── modules/
│   ├── group__cudart__device.md
│   ├── group__cudart__memory.md
│   └── ...
└── data-structures/
    ├── structcudadeviceprop.md
    └── ...
```

## Verification Commands

```bash
# Check file counts
ls cuda-runtime-docs/modules/ | wc -l

# Check for remaining URLs
rg 'https://docs.nvidia.com' cuda-runtime-docs/

# Check size reduction
du -sh cuda-runtime-docs/
```
