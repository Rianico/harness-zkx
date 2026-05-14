---
name: tavily-tools
description: |
  Tavily CLI for web search, content extraction, site mapping, crawling, and AI-powered research. Use for:
  (1) SEARCH - finding web pages, articles, news, documentation when you don't have URLs. Triggers on: search for, find me, look up, what's the latest on.
  (2) EXTRACT - pulling markdown from specific URLs, batch extraction, query-focused extraction. Triggers on: extract from URL, get content from, pull text from.
  (3) MAP - discover URLs on a site, list all pages, find site structure. Triggers on: map the site, find the URL for, what pages are on, list all pages, site structure.
  (4) CRAWL - bulk extract content from entire site sections, download docs. Triggers on: crawl, get all pages, download the docs, bulk extract, extract everything under /docs.
  (5) RESEARCH - AI-powered deep research with citations. Triggers on: research, investigate, analyze in depth, compare X vs Y, market analysis, literature review.
  Returns LLM-optimized markdown with relevance scores.
argument-hint: "search <query> | extract <url> | map <site_url> | crawl <url> | research <topic> [--model mini|pro]"
allowed-tools: Bash(tvly *)
---

# Tavily Tools

Unified CLI for web search, content extraction, site mapping, crawling, and AI-powered research.

**If `tvly` is not installed**, see [CLI Setup](references/cli-setup.md).

---

## Workflow Escalation Pattern

Follow this order:

1. **Search** — No specific URL. Find pages, answer questions, discover sources.
2. **Extract** — Have a URL. Pull its content directly.
3. **Map** — Large site, need to find the right page. Discover URLs first.
4. **Crawl** — Need bulk content from an entire site section.
5. **Research** — Need comprehensive, multi-source analysis with citations.

| Need | Command | When |
|------|---------|------|
| Find pages on a topic | `search` | No specific URL yet |
| Get a page's content | `extract` | Have a URL |
| Find URLs within a site | `map` | Need to locate a specific subpage |
| Bulk extract a site section | `crawl` | Need many pages (e.g., all /docs/) |
| Deep research with citations | `research` | Need multi-source synthesis |

---

## SEARCH

Web search returning LLM-optimized results with content snippets and relevance scores.

### When to Use

- Finding information when you don't have a URL
- First step in workflow: **search** → extract → map → crawl

### Quick Start

```bash
# Basic search
tvly search "your query" --json

# Advanced search
tvly search "quantum computing" --depth advanced --max-results 10 --json

# Recent news
tvly search "AI news" --time-range week --topic news --json

# Domain-filtered
tvly search "SEC filings" --include-domains sec.gov,reuters.com --json

# Include full page content (saves separate extract call)
tvly search "react hooks tutorial" --include-raw-content --max-results 3 --json
```

### Options

| Option | Values | Description |
|--------|--------|-------------|
| `--depth` | `ultra-fast`, `fast`, `basic` (default), `advanced` | Speed vs relevance tradeoff |
| `--max-results` | 0-20 (default: 5) | Number of results |
| `--topic` | `general`, `news`, `finance` | Content type |
| `--time-range` | `day`, `week`, `month`, `year` | Recency filter |
| `--include-domains` | `domain1,domain2` | Whitelist domains |
| `--exclude-domains` | `domain1,domain2` | Blacklist domains |
| `--include-raw-content` | `markdown`, `text` | Full page content |
| `--include-answer` | `basic`, `advanced` | AI-generated answer |

### Search Depth Guide

| Depth | Speed | Relevance | Best For |
|-------|-------|-----------|----------|
| `ultra-fast` | Fastest | Lower | Real-time chat, autocomplete |
| `fast` | Fast | Good | Need chunks, latency matters |
| `basic` | Medium | High | General-purpose (default) |
| `advanced` | Slower | Highest | Precision, specific facts |

### Tips

- **Keep queries under 400 characters** — think search query, not prompt.
- **Break complex queries into sub-queries** for better results.
- **Use `--include-raw-content`** when you need full page text (saves extract call).
- **Use `--include-domains`** to focus on trusted sources.
- **Use `--time-range`** for recent information.

---

## EXTRACT

Extract clean markdown from URLs with optional query-focused filtering.

**Always save output to file to avoid bloating context. Use `.lsz/tavily/<short_topic>/` as output directory.**

### When to Use

- You have a specific URL and want its content
- You need text from JavaScript-rendered pages
- Step 2 in the workflow: search → **extract** → map → crawl

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/tavily/<short_topic>

# Single URL - save to file
tvly extract "https://example.com/docs" -o .lsz/tavily/<short_topic>/output.md --json

# Batch (up to 20 URLs, parallel)
tvly extract "url1" "url2" "url3" -o .lsz/tavily/<short_topic>/batch.md --json

# Query-focused extraction (unique feature)
tvly extract "https://docs.example.com/api" \
  --query "authentication JWT tokens" \
  --chunks-per-source 3 \
  -o .lsz/tavily/<short_topic>/auth.md \
  --json

# JS-heavy pages
tvly extract "https://app.example.com" --extract-depth advanced --json
```

### Options

| Option | Description |
|--------|-------------|
| `--query` | Rerank chunks by relevance to this query |
| `--chunks-per-source` | Chunks per URL (1-5, requires `--query`) |
| `--extract-depth` | `basic` (default) or `advanced` (for JS pages) |
| `--format` | `markdown` (default) or `text` |
| `--include-images` | Include image URLs |
| `--timeout` | Max wait time (1-60 seconds) |
| `-o, --output` | Save output to file |
| `--json` | Structured JSON output |

### Extract Depth

| Depth | When to use |
|-------|-------------|
| `basic` | Simple pages, fast — try this first |
| `advanced` | JS-rendered SPAs, dynamic content, tables |

### Tips

- **Max 20 URLs per request** — batch larger lists into multiple calls.
- **Use `--query` + `--chunks-per-source`** to get only relevant content instead of full pages.
- **Try `basic` first**, fall back to `advanced` if content is missing.

---

## MAP

Discover URLs on a website without extracting content. Faster than crawling.

### Priority Order (CRITICAL)

**Before using `tvly map`, always check for faster alternatives:**

1. **llms.txt** — If site serves `https://<domain>/llms.txt`, fetch directly with curl (AI-optimized site index)
2. **sitemap.xml** — If site has `https://<domain>/sitemap.xml`, fetch and parse with curl
3. **Tavily map** — Use as fallback when neither above is available

### When to Use

- Need to find a specific subpage on a large site
- Want a list of all URLs before deciding what to extract
- Workflow: search → extract → **map** → crawl

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/tavily/<short_topic>

# Discover all URLs
tvly map "https://docs.example.com" --json

# With natural language filtering
tvly map "https://docs.example.com" --instructions "Find API docs and guides" --json

# Filter by path
tvly map "https://example.com" --select-paths "/blog/.*" --limit 500 --json

# Deep map
tvly map "https://example.com" --max-depth 3 --limit 200 --json
```

### Options

| Option | Description |
|--------|-------------|
| `--max-depth` | Levels deep (1-5, default: 1) |
| `--max-breadth` | Links per page (default: 20) |
| `--limit` | Max URLs to discover (default: 50) |
| `--instructions` | Natural language guidance for URL filtering |
| `--select-paths` | Comma-separated regex patterns to include |
| `--exclude-paths` | Comma-separated regex patterns to exclude |
| `--select-domains` | Comma-separated regex for domains to include |
| `--exclude-domains` | Comma-separated regex for domains to exclude |
| `--allow-external / --no-external` | Include external links |
| `--timeout` | Max wait (10-150 seconds) |
| `-o, --output` | Save output to file |
| `--json` | Structured JSON output |

### Map + Extract Pattern

Use `map` to find the right page, then `extract` it:

```bash
# Step 1: Find the authentication docs
tvly map "https://docs.example.com" --instructions "authentication" --json

# Step 2: Extract the specific page you found
tvly extract "https://docs.example.com/api/authentication" --json
```

### Tips

- **Map is URL discovery only** — no content extraction. Use `extract` or `crawl` for content.
- **Map + extract beats crawl** when you only need a few specific pages from a large site.
- **Check llms.txt first** — `curl -s` is free and instant.

---

## CRAWL

Crawl a website and extract content from multiple pages. Supports saving each page as a local markdown file.

### When to Use

- You need content from many pages on a site (e.g., all `/docs/`)
- You want to download documentation for offline use
- Step 4 in the workflow: search → extract → map → **crawl** → research

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/tavily/<short_topic>

# Basic crawl (JSON output)
tvly crawl "https://docs.example.com" -o .lsz/tavily/<short_topic>/crawl.json --json

# Save each page as a markdown file
tvly crawl "https://docs.example.com" --output-dir .lsz/tavily/<short_topic>/docs/

# Deeper crawl with limits
tvly crawl "https://docs.example.com" --max-depth 2 --limit 50 --json

# Filter to specific paths
tvly crawl "https://example.com" --select-paths "/api/.*,/guides/.*" --exclude-paths "/blog/.*" --json

# Semantic focus (returns relevant chunks, not full pages)
tvly crawl "https://docs.example.com" --instructions "Find authentication docs" --chunks-per-source 3 --json
```

### Options

| Option | Description |
|--------|-------------|
| `--max-depth` | Levels deep (1-5, default: 1) |
| `--max-breadth` | Links per page (default: 20) |
| `--limit` | Total pages cap (default: 50) |
| `--instructions` | Natural language guidance for semantic focus |
| `--chunks-per-source` | Chunks per page (1-5, requires `--instructions`) |
| `--extract-depth` | `basic` (default) or `advanced` |
| `--format` | `markdown` (default) or `text` |
| `--select-paths` | Comma-separated regex patterns to include |
| `--exclude-paths` | Comma-separated regex patterns to exclude |
| `--allow-external / --no-external` | Include external links (default: allow) |
| `--timeout` | Max wait (10-150 seconds) |
| `-o, --output` | Save JSON output to file |
| `--output-dir` | Save each page as a .md file in directory |
| `--json` | Structured JSON output |

### Crawl for Context vs. Data Collection

**For agentic use** (feeding results to an LLM):

Always use `--instructions` + `--chunks-per-source`. Returns only relevant chunks instead of full pages — prevents context explosion.

```bash
tvly crawl "https://docs.example.com" --instructions "API authentication" --chunks-per-source 3 --json
```

**For data collection** (saving to files):

Use `--output-dir` without `--chunks-per-source` to get full pages as markdown files.

```bash
tvly crawl "https://docs.example.com" --max-depth 2 --output-dir .lsz/tavily/<short_topic>/docs/
```

### Tips

- **Start conservative** — `--max-depth 1`, `--limit 20` — and scale up.
- **Use `--select-paths`** to focus on the section you need.
- **Use map first** to understand site structure before a full crawl.
- **Always set `--limit`** to prevent runaway crawls.

---

## RESEARCH

AI-powered deep research that gathers sources, analyzes them, and produces a cited report. Takes 30-120 seconds.

### When to Use

- You need comprehensive, multi-source analysis
- The user wants a comparison, market report, or literature review
- Quick searches aren't enough — you need synthesis with citations
- Step 5 in the workflow: search → extract → map → crawl → **research**

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/tavily/<short_topic>

# Basic research (waits for completion)
tvly research "competitive landscape of AI code assistants"

# Pro model for comprehensive analysis
tvly research "electric vehicle market analysis" --model pro

# Stream results in real-time
tvly research "AI agent frameworks comparison" --stream

# Save report to file
tvly research "fintech trends 2025" --model pro -o .lsz/tavily/<short_topic>/fintech-report.md

# JSON output for agents
tvly research "quantum computing breakthroughs" --json
```

### Options

| Option | Description |
|--------|-------------|
| `--model` | `mini`, `pro`, or `auto` (default) |
| `--stream` | Stream results in real-time |
| `--no-wait` | Return request_id immediately (async) |
| `--output-schema` | Path to JSON schema for structured output |
| `--citation-format` | `numbered`, `mla`, `apa`, `chicago` |
| `--poll-interval` | Seconds between checks (default: 10) |
| `--timeout` | Max wait seconds (default: 600) |
| `-o, --output` | Save output to file |
| `--json` | Structured JSON output |

### Model Selection

| Model | Use for | Speed |
|-------|---------|-------|
| `mini` | Single-topic, targeted research | ~30s |
| `pro` | Comprehensive multi-angle analysis | ~60-120s |
| `auto` | API chooses based on complexity | Varies |

**Rule of thumb:** "What does X do?" → mini. "X vs Y vs Z" or "best way to..." → pro.

### Async Workflow

For long-running research, you can start and poll separately:

```bash
# Start without waiting
tvly research "topic" --no-wait --json    # returns request_id

# Check status
tvly research status <request_id> --json

# Wait for completion
tvly research poll <request_id> --json -o result.json
```

### Tips

- **Research takes 30-120 seconds** — use `--stream` to see progress in real-time.
- **Use `--model pro`** for complex comparisons or multi-faceted topics.
- **For quick facts**, use `tvly search` instead — research is for deep synthesis.

---

## Output & Organization

Always save results to `.lsz/tavily/<short_topic>/` with `-o` to avoid context bloat.

```bash
tvly search "react hooks" -o .lsz/tavily/react-hooks/search.json --json
tvly extract "https://example.com" -o .lsz/tavily/<short_topic>/page.md
```

Never read entire output files at once. Use `grep`, `head`, or incremental reads:

```bash
wc -l .lsz/tavily/<short_topic>/file.md && head -50 .lsz/tavily/<short_topic>/file.md
grep -n "keyword" .lsz/tavily/<short_topic>/file.md
```

---

## See Also

- [CLI Setup](references/cli-setup.md) — Installation and authentication
- [Extract Workflow](references/extract-workflow.md) — Detailed extract usage and batch operations
- [Map Workflow](references/map-workflow.md) — Site discovery with llms.txt/sitemap priority
- [SDK Reference](references/sdk.md) — Building apps with Tavily API (Python/JavaScript)
