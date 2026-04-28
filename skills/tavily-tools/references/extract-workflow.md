# Tavily Extract Workflow

Detailed guide for extracting markdown content from URLs.

## Output Convention

**Always save extracted content to file to avoid bloating context.**

Standard output path: `.lsz/extract/<short_topic>/`

```bash
# Create output directory
mkdir -p .lsz/extract/react-hooks

# Extract with file output
tvly extract "https://react.dev/reference/react/useEffect" \
  -o .lsz/extract/react-hooks/useEffect.md \
  --json
```

## Basic Usage

```bash
# Single URL - save to file
tvly extract "https://example.com/article" -o .lsz/extract/<topic>/article.md --json

# Batch - save combined output
tvly extract "url1" "url2" "url3" -o .lsz/extract/<topic>/batch.md --json
```

## Batch Extraction

Tavily supports up to 20 URLs in a single parallel request.

```bash
# Multiple URLs (parallel processing)
tvly extract \
  "https://docs.example.com/page1" \
  "https://docs.example.com/page2" \
  "https://docs.example.com/page3" \
  --json

# Extract with output file
tvly extract "url1" "url2" "url3" -o combined.md
```

### Performance

| URLs | Tavily (parallel) | Jina Reader (sequential) |
|------|-------------------|--------------------------|
| 1 | ~1s | ~1s |
| 3 | ~1.1s | ~19s |
| 10 | ~1.5s | ~60s+ |

## Query-Focused Extraction (Unique Feature)

Get only relevant chunks instead of full page content. This is Tavily's unique feature for reducing token usage.

```bash
# Extract only relevant chunks
tvly extract "https://docs.example.com/api" \
  --query "authentication JWT tokens" \
  --chunks-per-source 3 \
  --json
```

### When to Use Query Focus

- Documentation pages with lots of unrelated content
- Long articles where you need specific sections
- Changelogs where you want specific topics
- API docs where you need specific endpoints

### Example: Breaking Changes

```bash
# Get only breaking changes from a changelog
tvly extract "https://docs.framework.com/changelog" \
  --query "breaking changes migration v3" \
  --chunks-per-source 5 \
  --json
```

## JS-Heavy Pages

For SPAs and dynamically rendered content, use advanced depth:

```bash
# Basic (default) - try first
tvly extract "https://spa.example.com" --json

# Advanced - for JS-rendered content
tvly extract "https://spa.example.com" --extract-depth advanced --json
```

### Depth Comparison

| Depth | Use Case |
|-------|----------|
| `basic` | Static pages, server-rendered (default, faster) |
| `advanced` | SPAs, React/Vue apps, dynamic tables |

## Output Options

```bash
# JSON with structured output
tvly extract "https://example.com" --json | jq '.results[0].raw_content'

# Plain text instead of markdown
tvly extract "https://example.com" --format text --json

# Include images
tvly extract "https://example.com" --include-images --json

# Longer timeout for slow pages
tvly extract "https://slow.example.com" --timeout 60 --json
```

## JSON Output Structure

```json
{
  "results": [
    {
      "url": "https://example.com/page",
      "title": "Page Title",
      "raw_content": "# Markdown content...",
      "images": []
    }
  ],
  "failed_results": [],
  "response_time": 0.95
}
```

## Tavily vs Jina Reader

### Quick Comparison

| Aspect | Tavily Extract | Jina Reader |
|--------|----------------|-------------|
| Cost | API credits (metered) | Free |
| Batch | 20 URLs parallel | Sequential only |
| Query focus | `--query` (unique) | Not available |
| Auth | Required | None |
| JS rendering | `--extract-depth advanced` | Basic |

### Decision Matrix

| Scenario | Recommended Tool |
|----------|------------------|
| 1-2 URLs, quick lookup | Jina Reader (free, no setup) |
| 5+ URLs batch | Tavily (parallel, faster) |
| Need relevance filtering | Tavily `--query` |
| Budget constrained | Jina Reader |
| No auth available | Jina Reader |

### Jina Reader Usage

```bash
# Free alternative, no auth required
curl -sL "https://r.jina.ai/https://example.com/docs"
```

## Common Workflows

### Development Quick Lookup

```bash
# Fast, free lookup
curl -sL "https://r.jina.ai/https://docs.python.org/3/library/asyncio.html"
```

### Batch Documentation Fetch

```bash
# Parallel batch for multiple docs
tvly extract \
  "https://docs.example.com/intro" \
  "https://docs.example.com/installation" \
  "https://docs.example.com/quickstart" \
  --json > docs.json
```

### Research with Relevance Filter

```bash
# Get only relevant sections from long docs
tvly extract "https://docs.framework.com/guide" \
  --query "error handling exceptions" \
  --chunks-per-source 3 \
  --json
```

### Troubleshooting JS Pages

```bash
# Try basic first
tvly extract "https://react-app.example.com" --json

# If content is missing, try advanced
tvly extract "https://react-app.example.com" --extract-depth advanced --json
```
