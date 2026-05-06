---
name: scraper
description: "Documentation scraper for converting technical docs to LLM-friendly markdown. Use when scraping LSP specification, PTX ISA, CUDA Runtime/Driver API, Rust crate documentation, or other technical docs. For Rust projects (docs.rs, crates.io, GitHub repos), automatically uses cargo-docs-md for cleaner output. Handles emoji anchor cleanup, internal link resolution, section splitting, and caching. Triggers on: scrape LSP, scrape PTX, scrape CUDA, scrape Rust docs, docs.rs, rust documentation, convert HTML to markdown, technical docs to markdown."
argument-hint: "[lsp|ptx|runtime|driver|rust <target>] [--force] [--output-dir <path>]"
---

# Documentation Scraper Skill

Converts technical documentation to LLM-friendly markdown with proper structure, link resolution, and caching.

## Quick Start

```bash
uv run $SKILL_DIR/scripts/scrape.py <doc_type> --output-dir <path>

# Examples
uv run $SKILL_DIR/scripts/scrape.py lsp --output-dir ./references/lsp-docs
uv run $SKILL_DIR/scripts/scrape.py ptx --output-dir ./references/ptx-docs
uv run $SKILL_DIR/scripts/scrape.py runtime --output-dir ./references/cuda-runtime-docs
uv run $SKILL_DIR/scripts/scrape.py driver --output-dir ./references/cuda-driver-docs

# Rust crate documentation (uses cargo-docs-md)
uv run $SKILL_DIR/scripts/scrape.py rust ratatui --output-dir ./references/ratatui-docs
uv run $SKILL_DIR/scripts/scrape.py rust https://github.com/ratatui/ratatui

# Force re-fetch (ignore cache)
uv run $SKILL_DIR/scripts/scrape.py lsp --force
```

## Available Scrapers

| Scraper | Source | Description |
|---------|--------|-------------|
| `lsp` | LSP 3.17 Specification | Single-page spec with emoji anchors |
| `ptx` | PTX ISA Documentation | Single-page ISA reference |
| `runtime` | CUDA Runtime API | Multi-page API documentation |
| `driver` | CUDA Driver API | Multi-page API documentation |
| `rust` | Rust Crates | Uses cargo-docs-md for clean output |

## Rust Documentation

For Rust projects, the scraper uses `cargo-docs-md` which produces cleaner output than web scraping:

### Prerequisites

```bash
# Install Rust nightly (required for JSON output)
rustup toolchain install nightly

# Install cargo-docs-md
cargo install cargo-docs-md --locked
```

### Input Types

```bash
# By crate name (searches GitHub)
uv run $SKILL_DIR/scripts/scrape.py rust ratatui

# By GitHub URL
uv run $SKILL_DIR/scripts/scrape.py rust https://github.com/ratatui/ratatui

# By docs.rs URL
uv run $SKILL_DIR/scripts/scrape.py rust https://docs.rs/ratatui

# Local path
uv run $SKILL_DIR/scripts/scrape.py rust ./my-local-crate
```

### Workspace Support

For workspaces, the scraper filters to workspace crates only (not dependencies):

```bash
# Default: workspace crates only
uv run $SKILL_DIR/scripts/scrape.py rust ratatui --output-dir ./docs
# => 1.1M, 51 files (7 crates)

# Include all dependencies
uv run $SKILL_DIR/scripts/scrape.py rust ratatui --include-deps
# => 30M, 1297 files (346 crates)
```

### Output Quality

The `cargo-docs-md` output includes:
- Nested directory structure mirroring module hierarchy
- Quick Reference tables per module
- Method signatures with deep-link anchors
- Cross-crate links within workspace
- SUMMARY.md for mdBook compatibility
- search_index.json for search functionality

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
uv run $SKILL_DIR/scripts/scrape.py <type> --output-dir /tmp/test-scrape
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
uv run $SKILL_DIR/scripts/scrape.py <type> --output-dir /tmp/test-scrape

# Compare outputs
diff /tmp/test-scrape-prev /tmp/test-scrape
```

### 6. Final Validation

```bash
# Force fresh fetch
uv run $SKILL_DIR/scripts/scrape.py <type> --force --output-dir ./references/<name>-docs

# Run quality checks from checklist above
```

## Iterative Cleanup Discovery

Generated markdown often contains meaningless elements that bloat context. Use a systematic approach to discover and remove them.

### Discovery Script Pattern

After scraping, run detection scripts to find common artifacts:

```bash
# Count occurrences of potential meaningless elements
rg -c '<span id="[^"]+"></span>' /path/to/output
rg -c '<div id="[^"]+"></div>' /path/to/output
rg -c '\[\]\(#' /path/to/output  # Empty anchor links
rg -c '^\s*$' /path/to/output    # Blank lines (check for excess)

# Sample specific patterns
rg '<span id="[^"]+"></span>' /path/to/output -o | head -20
```

### Random Sampling for New Patterns

After automated cleanup, randomly sample files to find additional artifacts:

```bash
# Sample 5 random markdown files
fd -e md . /path/to/output | shuf -n 5 | xargs bat

# Or sample specific directories
fd -e md . /path/to/output/some_dir | shuf -n 3 | xargs less
```

Look for:
- Empty HTML elements (`<span></span>`, `<div></div>`)
- Duplicate content (navigation, footers)
- Excessive whitespace (3+ consecutive blank lines)
- Orphan anchors (links to removed sections)
- Non-rendering markdown (HTML comments, hidden elements)

### Update Cleanup Patterns

When new meaningless elements are discovered:

1. **Add pattern to scraper's `_cleanup_markdown()` method:**
   ```python
   patterns = [
       (r'<span id="[^"]+"></span>\n?', ""),  # Empty anchor spans
       (r'<div id="[^"]+"></div>\n?', ""),    # Empty divs
       (r'\n{3,}', "\n\n"),                    # Excess blank lines
   ]
   ```

2. **Re-run scraper and verify reduction:**
   ```bash
   # Before adding pattern
   rg -c '<span id=' /path/to/output | awk -F: '{sum+=$2} END {print sum}'

   # After adding pattern, re-scrape and check
   uv run $SKILL_DIR/scripts/scrape.py rust <target> --output-dir /tmp/verify
   rg -c '<span id=' /tmp/verify  # Should show 0 or significant reduction
   ```

3. **Document pattern in references/cleanup-patterns.md** for future reference

### Common Meaningless Elements

| Element | Pattern | Source |
|---------|---------|--------|
| Empty anchor spans | `<span id="..."></span>` | rustdoc (cargo-docs-md) |
| Empty divs | `<div id="..."></div>` | Web scrapers |
| Excess blank lines | `\n{3,}` | All scrapers |
| Empty anchor links | `[](#...)` | Link conversion |
| HTML comments | `<!-- ... -->` | Source HTML |

## LLM-Friendly Fetching (New)

Modern websites increasingly support direct markdown delivery:

1. **llms.txt** — Standard file at `/llms.txt` with curated page lists
2. **Accept: text/markdown** — Content negotiation header (Cloudflare, static servers)
3. **.md extension** — Some sites serve markdown at `page.html.md`
4. **Jina Reader** — Free proxy at `r.jina.ai/<url>`

**Token savings**: Up to 80% reduction when markdown is available directly.

### Quick Comparison

| Method | Cost | Best For |
|--------|------|----------|
| Jina Reader | Free | Quick lookups, development |
| Tavily Extract | Metered | Batch (20 URLs), query-focused |
| Accept header | Free | Cloudflare sites |
| llms.txt | Free | Curated documentation |

### When to Use What

- **1-2 URLs, quick lookup**: `curl https://r.jina.ai/<url>` (free, no setup)
- **5+ URLs batch**: `tvly extract url1 url2 ... --json` (parallel, faster)
- **Need relevance filtering**: `tvly extract --query "topic"` (unique feature)
- **Development iteration**: Use `fetch_page_llm_friendly()` with caching

See `references/llms-txt-patterns.md` and `references/tavily-vs-ours-comparison.md` for details.

## Reference Files

Scraper-specific patterns and code examples:

- `references/rust-patterns.md` — Rust crate documentation via cargo-docs-md
- `references/llms-txt-patterns.md` — llms.txt standard, Accept header, markdown fetching
- `references/lsp-patterns.md` — Emoji anchor cleanup, link resolution for LSP spec
- `references/cuda-patterns.md` — Multi-page discovery, cleanup pipeline for CUDA docs
- `references/section-extraction.md` — Common patterns for splitting content
- `references/cleanup-patterns.md` — Removing navigation, footers, duplicate content

When adding a new scraper, check these references for similar document structures.
