---
name: tavily-tools
description: "Tavily CLI for web search and content extraction. Use for: (1) SEARCH - finding web pages, articles, news, documentation when you don't have URLs. Triggers on: search for, find me, look up, what's the latest on. (2) EXTRACT - pulling markdown from specific URLs, batch extraction, query-focused extraction. Triggers on: extract from URL, get content from, pull text from. Returns LLM-optimized markdown with relevance scores."
argument-hint: "search <query> | extract <url> [--query <topic>] [--batch url1 url2 ...]"
allowed-tools: Bash(tvly *)
---

# Tavily Tools

Unified CLI for web search and content extraction.

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

## See Also

- [CLI Setup](references/cli-setup.md) — Installation and authentication
- [Extract Workflow](references/extract-workflow.md) — Detailed extract usage and batch operations
