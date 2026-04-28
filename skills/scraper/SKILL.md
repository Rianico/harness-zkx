---
name: scraper
description: "Documentation scraper for converting technical docs to LLM-friendly markdown. Use when scraping LSP specification, PTX ISA, CUDA Runtime/Driver API, or other technical documentation. Handles emoji anchor cleanup, internal link resolution, section splitting, and caching. Triggers on: scrape LSP, scrape PTX, scrape CUDA, documentation scraper, convert HTML to markdown, technical docs to markdown."
argument-hint: "[lsp|ptx|runtime|driver] [--force] [--output-dir <path>]"
---

# Documentation Scraper Skill

Converts technical documentation to LLM-friendly markdown with proper structure, link resolution, and caching.

## Quick Start

```bash
cd skills/scraper/scripts
uv run scrape.py <doc_type> --output-dir <path>

# Examples
uv run scrape.py lsp --output-dir ../references/lsp-docs
uv run scrape.py ptx --output-dir ../references/ptx-docs
uv run scrape.py runtime --output-dir ../references/cuda-runtime-docs
uv run scrape.py driver --output-dir ../references/cuda-driver-docs

# Force re-fetch (ignore cache)
uv run scrape.py lsp --force
```

## Available Scrapers

| Scraper | Source | Description |
|---------|--------|-------------|
| `lsp` | LSP 3.17 Specification | Single-page spec with emoji anchors |
| `ptx` | PTX ISA Documentation | Single-page ISA reference |
| `runtime` | CUDA Runtime API | Multi-page API documentation |
| `driver` | CUDA Driver API | Multi-page API documentation |

## Best Practices

The scraper implements production-ready web scraping best practices:

### Rate Limiting

- **Default delay**: 1.0 second between requests
- **Configurable**: Pass `delay` parameter to constructor
- **Purpose**: Avoid overwhelming target servers

### Retry Logic

- **Exponential backoff**: Automatically retries on transient failures
- **Default**: 3 retries with exponential backoff
- **Retry-After header**: Respects server-specified wait times for 429 responses

### Robots.txt Compliance

- **Enabled by default**: Checks robots.txt before scraping
- **Respects Crawl-Delay**: Uses server-specified delay if present
- **Honors disallow**: Skips URLs blocked by robots.txt
- **Disable with**: `respect_robots_txt=False`

### User-Agent Rotation

- **Default pool**: Common browser user agents
- **Rotation**: Random selection per request to avoid detection
- **Custom pool**: Pass your own list via `user_agent_pool` parameter

### Error Handling

- **Specific exceptions**: `ScraperConnectionError`, `ScraperTimeoutError`, `ScraperHTTPError`
- **Clear error messages**: Includes URL and context for debugging

### Constructor Parameters

```python
BaseScraper(
    delay=1.0,              # Seconds between requests
    max_retries=3,          # Retry attempts for transient failures
    respect_robots_txt=True,  # Check robots.txt compliance
    timeout=30.0,           # Request timeout in seconds
    user_agent_pool=None,   # Custom user agent list
)
```

## Caching

- **Default**: Uses cached HTML (fast iteration on processing logic)
- **`--force`**: Clear cache and re-fetch from network
- **Manual**: Delete `.cache/` directory

## Output Quality Checklist

Before considering a scrape complete, verify:

- [ ] **Titles are clean** — No emoji artifacts, empty parentheses, or navigation cruft
- [ ] **Source URLs are valid** — Click a few to verify they resolve
- [ ] **Internal links resolve** — Links to other sections point to local `.md` files
- [ ] **No orphan anchors** — `[](#anchor)` patterns should be converted or removed
- [ ] **Section splits are sensible** — Not too granular, not too monolithic
- [ ] **Code blocks preserved** — Syntax highlighting markers intact
- [ ] **Tables are readable** — Markdown tables render correctly

## Common Issues & Fixes

### Issue: Emoji artifacts in titles

**Symptom**: `#### Inline Value Request ()` or `--arrow_right_hook` in URLs

**Cause**: LSP spec uses emoji images in headings that create messy anchor IDs

**Fix**: Strip emoji images before extracting text, clean anchor IDs with regex pattern

### Issue: Internal links broken

**Symptom**: `[`Location`](#location)` doesn't resolve to local file

**Cause**: Anchor links not converted to file paths

**Fix**: Build anchor-to-filename map during extraction, rewrite links during save

### Issue: Duplicate content

**Symptom**: Same content appears in multiple files or sections

**Cause**: Multi-page docs have duplicate TOCs, navigation, cross-references

**Fix**: Identify and remove during cleanup phase (see CUDA reference)

### Issue: Wrong section granularity

**Symptom**: Files too large (hard to navigate) or too small (fragmented)

**Cause**: Splitting at wrong heading level

**Fix**: Adjust which heading level triggers new file (h3 vs h4)

## Iterative Development Workflow

When creating or refining a scraper:

### 1. Inspect the Source

```bash
# Check HTML structure
curl -s <doc-url> | grep -E '<h[1-4]|id="' | head -50

# Look for content container
curl -s <doc-url> | grep -E 'class=".*content|role="main"'
```

Identify:
- Content container (div with class/id)
- Heading levels used
- Anchor ID format
- Navigation elements to remove

### 2. Initial Scrape

Run with cache enabled for fast iteration:

```bash
uv run scrape.py <type> --output-dir /tmp/test-scrape
```

### 3. Inspect Output

```bash
# Check file structure
eza -T /tmp/test-scrape

# Check for artifacts
rg '\[\]\(#' /tmp/test-scrape      # Empty anchor links
rg '\(\)\s*$' /tmp/test-scrape     # Empty parentheses
rg '\*\*Source:\*\*' /tmp/test-scrape  # Verify source URLs

# Sample a few files
cat /tmp/test-scrape/0001-*.md
```

### 4. Identify Patterns

Common patterns to handle:
- Emoji/special characters in anchors → `references/lsp-patterns.md`
- Multi-page discovery → `references/cuda-patterns.md`
- Section number extraction → `references/section-extraction.md`
- Content cleanup → `references/cleanup-patterns.md`

### 5. Refine and Re-run

```bash
# Edit scraper logic
# Re-run (uses cache, so fast)
uv run scrape.py <type> --output-dir /tmp/test-scrape

# Compare outputs
diff /tmp/test-scrape-prev /tmp/test-scrape
```

### 6. Final Validation

```bash
# Force fresh fetch
uv run scrape.py <type> --force --output-dir ./references/<name>-docs

# Run quality checks from checklist above
```

## LLM-Friendly Fetching (New)

Modern websites increasingly support direct markdown delivery:

1. **llms.txt** — Standard file at `/llms.txt` with curated page lists
2. **Accept: text/markdown** — Content negotiation header (Cloudflare, static servers)
3. **.md extension** — Some sites serve markdown at `page.html.md`

**Token savings**: Up to 80% reduction when markdown is available directly.

See `references/llms-txt-patterns.md` for implementation patterns.

## Reference Files

Scraper-specific patterns and code examples:

- `references/llms-txt-patterns.md` — llms.txt standard, Accept header, markdown fetching
- `references/lsp-patterns.md` — Emoji anchor cleanup, link resolution for LSP spec
- `references/cuda-patterns.md` — Multi-page discovery, cleanup pipeline for CUDA docs
- `references/section-extraction.md` — Common patterns for splitting content
- `references/cleanup-patterns.md` — Removing navigation, footers, duplicate content

When adding a new scraper, check these references for similar document structures.
