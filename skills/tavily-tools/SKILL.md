---
name: tavily-tools
description: |
  Tavily CLI for web search, content extraction, and site mapping. Use for:
  (1) SEARCH - finding web pages, articles, news, documentation when you don't have URLs. Triggers on: search for, find me, look up, what's the latest on.
  (2) EXTRACT - pulling markdown from specific URLs, batch extraction, query-focused extraction. Triggers on: extract from URL, get content from, pull text from.
  (3) MAP - discover URLs on a site, list all pages, find site structure. Triggers on: map the site, find the URL for, what pages are on, list all pages, site structure.
  Returns LLM-optimized markdown with relevance scores.
argument-hint: "search <query> | extract <url> [--query <topic>] | map <site_url> [--instructions <filter>]"
allowed-tools: Bash(tvly *)
---

# Tavily Tools

Unified CLI for web search, content extraction, and site mapping.

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

**Always save output to file to avoid bloating context. Use `.lsz/extract/<short_topic>/` as output directory.**

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/extract/<short_topic>

# Single URL - save to file
tvly extract "https://example.com/docs" -o .lsz/extract/<short_topic>/output.md --json

# Batch (up to 20 URLs, parallel)
tvly extract "url1" "url2" "url3" -o .lsz/extract/<short_topic>/batch.md --json

# Query-focused extraction (unique feature)
tvly extract "https://docs.example.com/api" \
  --query "authentication JWT tokens" \
  --chunks-per-source 3 \
  -o .lsz/extract/<short_topic>/auth.md \
  --json
```

### Tavily vs Jina Reader

| Aspect | Tavily Extract | Jina Reader |
|--------|----------------|-------------|
| Cost | API credits (metered) | Free |
| Batch | 20 URLs parallel | Sequential only |
| Query focus | `--query` (unique) | Not available |
| Auth | Required (`tvly login`) | None |

**When to use which:**

| Scenario | Recommended |
|----------|-------------|
| 1-2 URLs, quick lookup | Jina: `curl https://r.jina.ai/<url>` |
| 5+ URLs batch | Tavily (parallel, faster) |
| Need relevance filtering | Tavily `--query` |
| Budget constrained | Jina Reader (free) |

**See [Extract Workflow](references/extract-workflow.md) for detailed usage and batch operations.**

---

## MAP

Discover URLs on a website without extracting content. Faster than crawling.

### Priority Order (CRITICAL)

**Before using `tvly map`, always check for faster alternatives:**

1. **llms.txt** — If site serves `https://<domain>/llms.txt`, fetch directly with curl (AI-optimized site index)
2. **sitemap.xml** — If site has `https://<domain>/sitemap.xml`, fetch and parse with curl
3. **Tavily map** — Use as fallback when neither above is available

```bash
# Step 1: Check llms.txt first (fastest, AI-optimized)
curl -s "https://example.com/llms.txt"

# Step 2: Check sitemap.xml (standard, comprehensive)
curl -s "https://example.com/sitemap.xml"

# Step 3: Fall back to Tavily map
tvly map "https://example.com" --json
```

### When to Use Map

- Need to find a specific subpage on a large site
- Want a list of all URLs before deciding what to extract
- llms.txt and sitemap.xml are not available
- Workflow: search → extract → **map** → crawl

### Quick Start

```bash
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
- **Use `--instructions`** for semantic filtering when path patterns aren't enough.
- **Check llms.txt first** — `curl -s` is free and instant; many docs sites now serve AI-optimized indexes.

---

## See Also

- [CLI Setup](references/cli-setup.md) — Installation and authentication
- [Extract Workflow](references/extract-workflow.md) — Detailed extract usage and batch operations
- [Map Workflow](references/map-workflow.md) — Site discovery with llms.txt/sitemap priority
