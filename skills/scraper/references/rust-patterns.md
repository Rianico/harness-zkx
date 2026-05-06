# Rust Documentation Patterns

Patterns for generating LLM-friendly markdown from Rust crate documentation.

## Tool Chain

| Tool | Purpose | Install |
|------|---------|---------|
| `rustup` | Rust toolchain manager | https://rustup.rs |
| `nightly` | Rust nightly toolchain | `rustup toolchain install nightly` |
| `cargo-docs-md` | Rustdoc JSON to markdown | `cargo install cargo-docs-md --locked` |

## Workflow

### 1. Detect Rust Project

```python
from scrapers.rust import detect_rust_project

# Check URL patterns
is_rust, reason = detect_rust_project(url="https://docs.rs/ratatui")
# => (True, "docs.rs URL indicates Rust crate: ratatui")

# Check local path
is_rust, reason = detect_rust_project(path=Path("./my-crate"))
# => (True, "Found Cargo.toml at ./my-crate")
```

### 2. Resolve Target

Input types supported:
- **Crate name**: `"ratatui"` — searches GitHub for matching repo
- **GitHub URL**: `"https://github.com/ratatui/ratatui"` — clones directly
- **docs.rs URL**: `"https://docs.rs/ratatui"` — extracts crate name, searches GitHub
- **Local path**: `"./my-crate"` — uses existing source

### 3. Generate Documentation

```bash
# From crate name
uv run scrape.py rust ratatui --output-dir ./docs/ratatui

# From GitHub URL
uv run scrape.py rust https://github.com/ratatui/ratatui --output-dir ./docs

# From local path
uv run scrape.py rust ./my-local-crate --output-dir ./docs
```

## Workspace Handling

### Detecting Primary Crate

For workspaces, the scraper attempts to detect the primary crate:

1. Check if directory name matches a workspace member
2. Return first non-example member
3. Use `--primary-crate` to override

```bash
# Explicit primary crate for workspace
uv run scrape.py rust https://github.com/ratatui/ratatui \
    --primary-crate ratatui \
    --output-dir ./docs/ratatui
```

### Filtering Workspace Crates

By default, only workspace crates are included (not dependencies):

```bash
# Include only workspace crates (default)
uv run scrape.py rust ratatui

# Include all dependencies
uv run scrape.py rust ratatui --include-deps
```

Size comparison for ratatui workspace:
- Full (346 crates): 30M, 1297 files
- Filtered (7 crates): 1.1M, 51 files

## Output Structure

```
output-dir/
├── crate_name/
│   ├── index.md          # Crate root documentation
│   ├── module/
│   │   └── index.md      # Module documentation
│   └── submodule/
│       └── index.md
├── crate_name_core/      # Workspace member crates
│   └── ...
├── SUMMARY.md            # mdBook-compatible summary
└── search_index.json     # Search index for all items
```

## Output Quality

### What's Preserved

- Module structure (nested directories)
- Quick Reference tables per module
- Method signatures with anchors
- Code examples with syntax highlighting
- Cross-crate links (within workspace)
- Breadcrumb navigation

### What's Filtered

- Private items (with `--exclude-private`)
- Blanket trait implementations (default)
- Trivial derive implementations (optional)

## Common Issues

### Issue: Rust version mismatch

**Symptom**: `rustc X.Y.Z is not supported by the following packages`

**Cause**: Nightly toolchain outdated

**Fix**: Update nightly
```bash
rustup update nightly
```

### Issue: cargo-docs-md not found

**Symptom**: `error: no such command: docs-md`

**Cause**: Tool not installed

**Fix**: Install with locked dependencies
```bash
cargo install cargo-docs-md --locked
```

### Issue: Missing GitHub repository

**Symptom**: `Could not find GitHub repository for crate 'xxx'`

**Cause**: Crate name doesn't match repo name

**Fix**: Provide full GitHub URL
```bash
uv run scrape.py rust https://github.com/owner/repo-name
```

## Integration Example

```python
from pathlib import Path
from scrapers.rust import RustScraper

scraper = RustScraper(
    target="ratatui",
    output_dir=Path("./docs/ratatui"),
    primary_crate="ratatui",  # For workspaces
    include_deps=False,       # Only workspace crates
    full_method_docs=True,    # Include full method docs
    exclude_private=True,     # Skip private items
)
scraper.run()
```

## Comparison: cargo-docs-md vs Web Scraping

| Aspect | cargo-docs-md | Web Scraping |
|--------|---------------|--------------|
| Source | Rust source code | docs.rs HTML |
| Quality | Clean, structured | May need cleanup |
| Dependencies | Only if requested | Always included |
| Offline | Yes | No |
| Speed | Build + convert | Network fetch |
| Best for | Active development | Archived crates |
