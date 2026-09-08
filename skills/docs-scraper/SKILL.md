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

## LLMs.txt Support

**Yes — first-class, with fallback.**

`site` scraper discovers URLs via:
1. `GET /llms.txt` — parses markdown links `[Title](URL)` + bare URLs, respects `## Optional` section (see `references/llms-txt-patterns.md`). Curated, high-signal; preferred when present.
2. `GET /sitemap.xml` — parses `<loc>` tags, recurses into sitemap indexes (depth ≤2), validates URLs. Exhaustive fallback.
3. Deduplication: `llms.txt` wins on overlap; `sitemap.xml` adds only unseen URLs.
4. Detection: `check_llms_txt()` now tries `HEAD /llms.txt` then falls back to `GET` (handles 405/403 on static/CDN hosts).

`site --base-url https://example.com` emits `{urls, source, metrics: {total, llms_txt, sitemap_xml, deduplicated}}`. `fetch_urls()` also writes `metrics.json`. Non-site scrapers (lsp/ptx/cuda/rust/skills) do not use llms.txt — they hit fixed upstream URLs or cargo/docs.rs.

## Fetching Way

### Discovery (site only, `--base-url`)

```
GET /llms.txt  → parse_llms_txt() → structured {url, title, section, optional}
GET /sitemap.xml → parse_sitemap_xml() → <loc> URLs → child sitemaps if index
merge + dedup → {urls, source: ["llms_txt", "sitemap_xml"], metrics}
```

### Fetch (site `urls...`, `site --base-url` with fetch, or any scraper page fetch)

`DocumentationScraper.fetch_page_llm_friendly()` — 6-step cascade, caches to `.cache/<name>/page_<n>.md|.html`:

1. **Accept: text/markdown** — `Accept: text/markdown, text/html` content negotiation (Cloudflare `x-markdown-tokens`, ~80% token savings).
2. **.md extension** — tries `page.md`, `<page>.md`, `<page>/index.md`.
3. **defuddle CLI** — local `defuddle parse <url> --md` (cleaner than html2text, no network).
4. **Jina Reader** — `https://r.jina.ai/<url>` free proxy, no API key.
5. **HTML + html2text** — fallback `fetch_page()` → `convert_to_markdown()` (BeautifulSoup + html2text, `body_width=0`).
6. **Cache reuse** — `.md` / `.html` cache hit short-circuits network unless `--force`.

All fetches go through `_rate_limited_get()`: robots.txt check (`RobotFileParser`, fail-open), crawl-delay + `delay=1.0s` rate limiting, User-Agent rotation (5-browser pool), exponential backoff on 408/429/5xx (Retry-After honoured, capped 60s, `max_retries=3`).

### Other scrapers

- `lsp`/`ptx`/`cuda` — single/multi-page HTML via `_rate_limited_get()` + cached `.cache/<name>/` (e.g. `.cache/lsp/spec.html`).
- `rust` — `cargo-docs-md` pipeline: clone → `cargo +nightly doc` (JSON) → `cargo docs-md --dir` → flatten `module/index.md→module.md` → rewrite links → verify.
- `skills` — `npx -y skills add <repo> --list` + `npx add <repo> --skill` via `skills` CLI, staged to `.lsz/tmp/skill-compose/<run>/stage`.

## Metrics

- **Discovery metrics** (site): `metrics: {total, llms_txt, sitemap_xml, deduplicated, sources}` returned by `discover_urls()` and printed as JSON in `site --base-url` mode.
- **Fetch metrics** (site): `metrics.json` in output dir — `{total, success, blocked, failed, success_rate, total_bytes, avg_bytes, formats: {markdown, html}, elapsed_seconds, base_url}` + `README.md` page index. Format counts track cascade effectiveness (markdown = negotiation/.md/defuddle/jina hit; html = fell through to conversion).
- **CUDA metrics**: `_create_index` + cleanup reports `files: total_original→total_new bytes (reduction%)`, output dir size.
- **Rust metrics**: post-run `Generated N markdown files`, `verify_links` broken-link count, `flattened N files`.
- **Skill quality metrics**: `references/quality-metrics.md` — 6 criteria (Trigger Coverage 20%, Pattern Usefulness 20%, Beginner Friendliness 15%, Documentation Completeness 15%, Navigation Clarity 15%, Graceful Degradation 15%) scored 0-1, compiled by `scripts/compile.py validate-skill/validate-triggers`.

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
