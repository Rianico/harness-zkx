# Tavily Map Workflow

Detailed guide for site URL discovery with priority fallback to llms.txt and sitemap.xml.

## Priority Order (CRITICAL)

**Always check faster alternatives before using Tavily map:**

```
1. llms.txt     → AI-optimized index, fastest
2. sitemap.xml  → Standard site index
3. Tavily map   → Fallback discovery
```

## Step 1: Check llms.txt

Many documentation sites now serve `llms.txt` — a markdown file optimized for LLMs containing the site structure and key URLs. Fetch directly with curl (free, instant).

```bash
# Fetch llms.txt directly
curl -s "https://docs.example.com/llms.txt"
```

### What llms.txt Provides

- Site structure in markdown format
- Key documentation URLs
- Often includes brief descriptions
- Designed for AI consumption (no HTML parsing needed)

### Sites Known to Support llms.txt

- Documentation frameworks (Mintlify, etc.)
- Python package docs (growing adoption)
- AI-focused product documentation

## Step 2: Check sitemap.xml

Standard XML sitemaps contain all indexed URLs. Fetch directly with curl.

```bash
# Fetch sitemap.xml directly
curl -s "https://example.com/sitemap.xml"

# Extract just the URLs
curl -s "https://example.com/sitemap.xml" | grep -oP '(?<=<loc>)[^<]+'
```

### Sitemap Variants

```bash
# Common sitemap locations
curl -s "https://example.com/sitemap.xml"        # Standard
curl -s "https://example.com/sitemap_index.xml"   # Index (WordPress)
curl -s "https://example.com/sitemap.txt"         # Plain text
```

### Parse Sitemap Index

Some sites use sitemap indexes (multiple sitemaps):

```bash
# Get all sitemap URLs from index
curl -s "https://example.com/sitemap_index.xml" | grep -oP '(?<=<loc>)[^<]+'

# Then fetch each sitemap
curl -s "https://example.com/sitemap-1.xml" | grep -oP '(?<=<loc>)[^<]+'
```

## Step 3: Tavily Map (Fallback)

When llms.txt and sitemap are unavailable:

```bash
# Basic map
tvly map "https://example.com" --json

# With semantic filtering
tvly map "https://example.com" --instructions "API documentation" --json

# Deep discovery
tvly map "https://example.com" --max-depth 3 --limit 200 --json
```

## Decision Tree

```
User wants site URLs
        │
        ▼
Check llms.txt ──200 OK──► Extract and return URLs
        │
       404
        │
        ▼
Check sitemap.xml ──200 OK──► Parse and return URLs
        │
       404
        │
        ▼
Run tvly map ──► Return discovered URLs
```

## Complete Example

```bash
# Site URL discovery workflow
SITE="https://docs.anthropic.com"

# 1. Try llms.txt first (fastest, AI-optimized)
echo "Checking llms.txt..."
LLMS=$(curl -sf "$SITE/llms.txt")
if [ -n "$LLMS" ]; then
  echo "Found llms.txt:"
  echo "$LLMS"
  exit 0
fi

# 2. Try sitemap.xml
echo "Checking sitemap.xml..."
SITEMAP=$(curl -sf "$SITE/sitemap.xml")
if [ -n "$SITEMAP" ]; then
  echo "Found sitemap.xml — parsing URLs..."
  echo "$SITEMAP" | grep -oP '(?<=<loc>)[^<]+'
  exit 0
fi

# 3. Fall back to Tavily map
echo "Falling back to Tavily map..."
tvly map "$SITE" --json
```

## When Each Method Wins

| Method | Best For |
|--------|----------|
| llms.txt | AI-optimized docs, modern frameworks, quick site overview |
| sitemap.xml | Comprehensive URL lists, WordPress sites, SEO-focused sites |
| Tavily map | Sites without structured indexes, discovery with filtering |

## Performance Comparison

| Method | Speed | Cost | AI-Friendly |
|--------|-------|------|-------------|
| llms.txt | Instant | Free | Yes (markdown) |
| sitemap.xml | Instant | Free | Needs parsing |
| Tavily map | Seconds | API credits | Yes (JSON) |
