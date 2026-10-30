---
name: docs-scraper
description: >-
  Docs scraper and skill compiler for LSP, PTX, CUDA, docs sites, and books. Builds two-layer skills behind deterministic quality gates. Use when scraping unfamiliar docs, fixing stale pages, or composing skills from skill.sh.
argument-hint: |-
  [auto|lsp|ptx|runtime|driver|rust|site|skills|book] [--output-dir <path>] [--force] [--base-url <url>] [--staging <path>] [--run <slug>]
  to-skill <doc-dir|url> [--name <skill>] [--supplementary <paths-or-urls>] [--fold-into <skill-dir>] [--output-dir <path>]
metadata:
  depends-on: [ai-engineering-expert]
disable-model-invocation: true
---

# Docs Scraper

> [!tip] Router
> Routes name the source. `auto` dispatches by URL or content. Explicit `lsp|ptx|runtime|driver|rust|site|skills|book` overrides — `book` ingests local PDF/EPUB/DOCX/MD/TXT files. The `to-skill` route stages raw docs and emits the generation brief. Human or `$skill` dispatch only (`disable-model-invocation:true`).

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
| `.pdf` `.epub` `.docx` `.md` `.txt` file paths                                | `book`    | Monolithic document ingestion              |
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

# to-skill — stage raw docs + emit the generation brief (convert pipeline entry)
uv run $SKILL_DIR/scripts/scrape.py to-skill ./my-docs --name my-skill
# then: follow <output>/<name>/GENERATION-BRIEF.md (LLM convert), run the compile.py gates it names
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
| `book`    | Monolithic docs | PDF/EPUB/DOCX→MD, deterministic cleanup |
| `skills`  | skill.sh     | npx fetch + stage             |

Details per scraper → `references/*.md`.

## Fetching Way

### Discovery (site only, `--base-url`)

llms.txt is first-class with a fallback: `GET /llms.txt` is preferred when present (curated, high-signal). `sitemap.xml` is the exhaustive fallback. `llms.txt` wins on overlap.

```
GET /llms.txt  → parse_llms_txt() → structured {url, title, section, optional}
GET /sitemap.xml → parse_sitemap_xml() → <loc> URLs → child sitemaps if index
merge + dedup → {urls, source: ["llms_txt", "sitemap_xml"], metrics}
```

`check_llms_txt()` tries `HEAD /llms.txt`, then falls back to `GET` (handles 405/403 on static/CDN hosts). Fixed-source scrapers (`lsp|ptx|runtime|driver|rust|skills|book`) never use llms.txt — they hit fixed upstream URLs, cargo, or local files. See `references/llms-txt-patterns.md`.

### Fetch (site `urls...`, `site --base-url` with fetch, or any scraper page fetch)

`DocumentationScraper.fetch_page_llm_friendly()` — 6-step cascade, caches to `.cache/<name>/page_<n>.md|.html`:

1. **Accept: text/markdown** — `Accept: text/markdown, text/html` content negotiation (Cloudflare `x-markdown-tokens`, ~80% token savings).
2. **.md extension** — tries `page.md`, `<page>.md`, `<page>/index.md`.
3. **defuddle CLI** — local `defuddle parse <url> --md` (cleaner than html2text, no network).
4. **Jina Reader** — `https://r.jina.ai/<url>` free proxy, no API key.
5. **HTML + html2text** — fallback `fetch_page()` → `convert_to_markdown()` (BeautifulSoup + html2text, `body_width=0`).
6. **Cache reuse** — `.md` / `.html` cache hit short-circuits network unless `--force`.

All fetches go through `_rate_limited_get()`: robots.txt check (`RobotFileParser`, fail-open), crawl-delay, and `delay=1.0s` rate limiting. It rotates a 5-browser User-Agent pool. It retries 408/429/5xx with exponential backoff, honouring Retry-After up to 60s (`max_retries=3`).

### Other scrapers

- `lsp`/`ptx`/`runtime`/`driver` — single/multi-page HTML via `_rate_limited_get()` + cached `.cache/<name>/` (e.g. `.cache/lsp/spec.html`).
- `rust` — `cargo-docs-md` pipeline: clone → `cargo +nightly doc` (JSON) → `cargo docs-md --dir` → flatten `module/index.md→module.md` → rewrite links → verify.
- `skills` — `npx -y skills add <repo> --list` + `npx add <repo> --skill` via `skills` CLI, staged to `.lsz/tmp/skill-compose/<run>/stage`.
- `book` — monolithic local-file ingestion: extraction cascade `docling → pdftotext → pypdf` (PDF), zipfile+BS4 (EPUB), zipfile+XML (DOCX). Deterministic `clean_pdftotext()` strips running headers/footers (page-repetition >50%), edge page numbers (Arabic+Roman), joins hyphen-wraps. Sliced into heading-anchored chunks (`--max-tokens`). Output routed through `sanitize.py` (zero-width/bidi/Trojan Source + prompt injection scan).

Sanitize is a utility, not a scraper route: `uv run $SKILL_DIR/scripts/sanitize.py <file> [--check]` strips invisible/zero-width/bidi codepoints and reports injection patterns.

## Metrics

- **Discovery metrics** (site): `metrics: {total, llms_txt, sitemap_xml, deduplicated, sources}` returned by `discover_urls()` and printed as JSON in `site --base-url` mode.
- **Fetch metrics** (site): `metrics.json` in output dir — `{total, success, blocked, failed, success_rate, total_bytes, avg_bytes, formats: {markdown, html}, elapsed_seconds, base_url}` + `README.md` page index. Format counts track cascade effectiveness (markdown = negotiation/.md/defuddle/jina hit, html = fell through to conversion).
- **CUDA metrics**: `_create_index` + cleanup reports `files: total_original→total_new bytes (reduction%)`, output dir size.
- **Rust metrics**: post-run `Generated N markdown files`, `verify_links` broken-link count, `flattened N files`.
- **Skill quality metrics**: `references/quality-metrics.md` — 6 criteria (Trigger Coverage 20%, Pattern Usefulness 20%, Beginner Friendliness 15%, Documentation Completeness 15%, Navigation Clarity 15%, Graceful Degradation 15%) scored 0-1, compiled by `scripts/compile.py validate-skill/validate-triggers`.
- **Sanitization & STE-100** (deterministic, no AI): `compile.py` runs `lint_injections()` + STE-100 checks (`lint_banned_words()`, `lint_phrasal_verbs()`, `lint_sentence_lengths()`, `lint_semicolons()`, `lint_nominalizations()`) on `SKILL.md` body and reference files. `sanitize.py` strips threat codepoints before compilation.

## References

- `references/lsp-patterns.md` — emoji anchor cleanup
- `references/cuda-patterns.md` — multi-page discovery (`runtime`/`driver`)
- `references/rust-patterns.md` + `rust-compact-output.md` — cargo-docs-md
- `references/llms-txt-patterns.md` + `tavily-vs-ours-comparison.md` — llms.txt / fetching
- `references/cleanup-patterns.md` + `section-extraction.md` — generic cleanup/splitting
- `references/cli-scrape-standards.md` — CLI globals extraction
- `references/skillsh-compose.md` — skill.sh compose wiring
- To-skill pipeline (load per phase): `module-detection.md`, `trigger-extraction.md`, `pattern-extraction.md`, `extraction-rules.md`, `skill-template.md`, `compilation-contract.md`, `quality-metrics.md`

## Docs-to-Skill Pipeline

Three phases: fetch → convert → evaluate. docs-scraper owns the pipeline. The `ai-engineering-expert` `skill-authoring` subskill supplies the standards every result must pass.

1. **Fetch** — `to-skill <doc-dir|url> [--name <skill>] [--supplementary <paths-or-urls>]` stages raw material into `references/<name>-raw/`, sanitizes it, writes `structure-report.json`, and emits `GENERATION-BRIEF.md`.
2. **Convert** — follow the brief: propose modules, extract triggers and patterns, generate per `skill-template.md`. Curated `references/<module>.md` answers 80% of queries. The raw layer keeps the skill self-contained.
3. **Evaluate** — run the gates the brief names (`compile.py validate-skill` / `validate-triggers`), score against `quality-metrics.md`, then user review closes.

Fold-in updates an existing skill. `to-skill <new-material> --fold-into <skill-dir>` stages new raw beside the old raw layer and emits `UPDATE-BRIEF.md` with merge rules. Curated files stay untouched until merge curation.

Default staging root: `.lsz/tmp/to-skill/<name>/`. Pass `--output-dir skills` to build in place.
