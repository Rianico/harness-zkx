# Rust Scraper Compact Output

## Stability Warning

The markdown output from cargo-docs-md is **experimental**. The flattening and
link-rewriting logic is tightly coupled to the output format of cargo-docs-md
v0.2.x. If the tool is upgraded, re-run the full pipeline and verify 0 broken
links before relying on the output.

## Version Compatibility (tested as of 2025-05)

| Component | Version | Notes |
|-----------|---------|-------|
| cargo-docs-md | v0.2.4 | Markdown generation from rustdoc JSON |
| Rust nightly | nightly-2025-05+ | Required for rustdoc JSON output |
| rustdoc JSON format | v29 | Unstable, may change across nightly releases |
| rustc | 1.88.0+ | Stable toolchain for runtime |

If cargo-docs-md fails after a nightly update, pin the toolchain:
```bash
rustup toolchain install nightly-2025-05-01
```

## Overview

The Rust scraper produces a compact directory structure by flattening `module/index.md` patterns to `module.md`. Crate roots (top-level `crate/index.md`) are preserved to keep cross-crate links simple.

## Structure

**Before:**
```
ratatui/
├── backend/
│   └── index.md
├── init/
│   └── index.md
├── prelude/
│   └── index.md
└── widgets/
    └── index.md
```

**After:**
```
ratatui/
├── backend.md
├── init.md
├── prelude.md
└── widgets.md
```

Crate roots stay as `crate/index.md`. Nested modules also flatten:
```
ratatui_core/
├── index.md                    # Crate root (preserved)
├── style.md                    # Flattened from style/index.md
├── style/
│   ├── palette.md              # Flattened from style/palette/index.md
│   └── palette/
│       ├── material.md         # Flattened from style/palette/material/index.md
│       └── tailwind.md         # Flattened from style/palette/tailwind/index.md
├── symbols.md                  # Flattened from symbols/index.md
└── symbols/
    ├── bar.md                  # Flattened from symbols/bar/index.md
    └── ...
```

## Link Rewriting

Per-link filesystem-based resolution. For each broken link, the rewriter tries multiple strategies:

1. **`/index.md` -> `.md`**: Flattened module references
2. **Depth adjustment**: Reduce `../` count for files that lost a level
3. **Parent module resolution**: `../index.md` -> `../parentname.md` when parent was flattened
4. **Self-reference cleanup**: `index.md` -> `#` for flattened module breadcrumbs
5. **Submodule directory prefix**: `bar.md` -> `./symbols/bar.md` from `symbols.md`
6. **Cross-crate links**: Preserved via `../crate/index.md` paths

## Implementation

### Methods

1. **`_flatten_structure(output_dir) -> set[str]`**
   - Moves `module/index.md` to `module.md` (skipping crate roots)
   - Returns set of flattened module paths for link rewriting
   - Removes empty directories

2. **`_rewrite_links(output_dir, flattened_modules)`**
   - Per-link resolution using filesystem checks
   - Uses `flattened_modules` to determine depth adjustments
   - Handles SUMMARY.md and crate root cross-crate links

3. **`_verify_links(output_dir)`**
   - Validates all internal markdown links
   - Skips external URLs and known external references (CONTRIBUTING.md)

### Execution Order

```
1. Generate markdown with cargo-docs-md
2. Flatten directory structure
3. Rewrite internal links
4. Cleanup markdown artifacts
5. Verify links
```

## Known Limitations

1. **Deeply nested structures**: Directories with multiple files (not just `index.md`) are not flattened
2. **External references**: Links to files not in the output (CONTRIBUTING.md) are skipped during verification
3. **Tool coupling**: Fix strategies in `_rewrite_links` are empirical, derived from cargo-docs-md v0.2.x output. A major format change would require re-deriving the fix strategies.
4. **rustdoc JSON instability**: The nightly-only JSON format is not stable. Pin nightly toolchain dates if reproducibility matters.
