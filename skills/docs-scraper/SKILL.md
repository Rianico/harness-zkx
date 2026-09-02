---
name: docs-scraper
description: >-
  Docs pipeline: scrape LSP/PTX/CUDA/Rust/site/skill.sh to LLM markdown + layered skill generation. TRIGGER: scrape docs, auto, to-skill, convert docs to skill, compose skills.
argument-hint: |-
  [auto|lsp|ptx|runtime|driver|rust|site|skills <target>] [--output-dir <path>] [--force] [--base-url <url>] [--staging <path>] [--run <slug>]
  to-skill: <doc-dir|url> [--name <skill>] [--supplementary <paths-or-urls>] [--output-dir <path>]
metadata:
  depends-on: [ai-engineering-expert]
disable-model-invocation: true
---

# Documentation Pipeline

> [!tip] Router
> Source-as-verb: `auto` dispatches by URL/content; explicit `lsp|ptx|runtime|driver|rust|site|skills` overrides. Second route `to-skill` builds a layered skill. Human or `$skill` dispatch only (`disable-model-invocation:true`).

Core = script + converter. Per-source cleanup lives in `references/*` loaded on demand.

## Auto Dispatch

| Input pattern                                                             | Resolved  | Notes                                        |
| ------------------------------------------------------------------------- | --------- | -------------------------------------------- |
| `https://microsoft.github.io/.../lsp/` or `lsp` keyword                   | `lsp`     | LSP 3.17 spec                                |
| `*.ptx` / `docs.nvidia.com/cuda/ptx`                                      | `ptx`     | PTX ISA                                      |
| `docs.nvidia.com/cuda/cuda-runtime`                                       | `runtime` | CUDA Runtime                                 |
| `docs.nvidia.com/cuda/cuda-driver`                                        | `driver`  | CUDA Driver                                  |
| `docs.rs` `crate name` `*.rs` (or explicit `rust https://github.com/...`) | `rust`    | cargo-docs-md (GitHub needs explicit `rust`) |
| `skill.sh` URL / `owner/collection/skill`                                 | `skills`  | npx skills                                   |
| otherwise                                                                 | `site`    | llms.txt/sitemap fallback                    |

Explicit source skips detection: `uv run $SKILL_DIR/scripts/scrape.py site --base-url https://example.com`.

## Quick Start

```bash
# auto — script detects source
uv run $SKILL_DIR/scripts/scrape.py auto https://example.com --output-dir ./references/site-docs
uv run $SKILL_DIR/scripts/scrape.py auto rust ratatui --output-dir ./references/ratatui-docs
uv run $SKILL_DIR/scripts/scrape.py auto https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert

# explicit override
uv run $SKILL_DIR/scripts/scrape.py lsp --output-dir ./references/lsp-docs
uv run $SKILL_DIR/scripts/scrape.py rust https://github.com/ratatui/ratatui

# to-skill — thin bridge (fetch via auto, then delegate to ai-engineering-expert skill-authoring)
uv run $SKILL_DIR/scripts/scrape.py auto https://example.com --output-dir .lsz/tmp/example-raw
# then in subagent: load ai-engineering-expert skill-authoring + generate curated skill at skills/<name>/
```

## Available Scrapers

| Scraper   | Source       | Output                        |
| --------- | ------------ | ----------------------------- |
| `lsp`     | LSP 3.17     | single page, emoji anchors    |
| `ptx`     | PTX ISA      | single page                   |
| `runtime` | CUDA Runtime | multi-page API                |
| `driver`  | CUDA Driver  | multi-page API                |
| `rust`    | Rust crates  | cargo-docs-md                 |
| `site`    | Generic web  | llms.txt/sitemap, CLI globals |
| `skills`  | skill.sh     | npx fetch + stage             |

Details per scraper → `references/*.md`.

## References

- `references/lsp-patterns.md` — emoji anchor cleanup
- `references/cuda-patterns.md` — multi-page discovery
- `references/rust-patterns.md` + `rust-compact-output.md` — cargo-docs-md
- `references/llms-txt-patterns.md` + `tavily-vs-ours-comparison.md` — llms.txt / fetching
- `references/cleanup-patterns.md` + `section-extraction.md` — generic cleanup/splitting
- `references/cli-scrape-standards.md` — CLI globals extraction
- `references/skillsh-compose.md` — skill.sh compose wiring
- `references/module-detection.md` `trigger-extraction.md` `pattern-extraction.md` `extraction-rules.md` `skill-template.md` `quality-metrics.md` `compilation-contract.md` — to-skill pipeline (load only during `to-skill`)

## Docs-to-Skill Pipeline

Two layers: curated `references/<module>.md` (80% queries) + raw `references/<skill>-raw/` (self-contained). No intermediate wiki.

Phase 0 fetch via `scrape.py auto` to `.lsz/tmp` or `references/<name>-raw/`; Phases 1-4 delegate to `ai-engineering-expert` (`skill-authoring`) for module/trigger/pattern extraction and generation. Keep `to-skill` thin — do not duplicate `quality-metrics` here.
