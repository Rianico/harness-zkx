# Tavily Extract vs Our Scraper: Comprehensive Comparison

## Executive Summary

| Aspect | Tavily Extract | Our Scraper (Jina Reader) |
|--------|----------------|---------------------------|
| **Speed** | ~1s per URL, parallel batch | ~1s per URL, sequential |
| **Content Size** | More verbose (11K chars) | More focused (6-7K chars) |
| **Code Blocks** | Preserved | Preserved with cleaner markdown |
| **Batch Support** | Up to 20 URLs in parallel | Sequential only |
| **Query Focus** | Unique feature (--query) | Not available |
| **Cost** | API credits (metered) | Free (no auth needed) |
| **JS Rendering** | Advanced depth option | Works on most sites |
| **Rate Limits** | API limits | None (but may be blocked) |

---

## 1. Performance Comparison

### Single URL

| Test | Tavily | Jina Reader |
|------|--------|-------------|
| Anthropic models doc | 0.96s | 0.65s |
| FastAPI path params | 0.87s | 1.23s |
| React useEffect | 1.08s | 1.41s |

**Winner**: Tie - both are fast (~1s)

### Batch URLs (3 URLs)

| Test | Tavily | Jina Reader (sequential) |
|------|--------|--------------------------|
| 3 Anthropic docs | **1.13s** | 19.1s |

**Winner**: **Tavily** - 17x faster due to parallel processing

---

## 2. Content Quality

### Content Size

| URL | Tavily | Jina Reader |
|-----|--------|-------------|
| Anthropic models | 11,949 chars | 6,658 chars |
| React useEffect | 31,849 chars | 69,116 chars |
| FastAPI path params | Similar | Similar |

**Analysis**:
- Tavily includes more navigation/boilerplate on some pages
- Jina Reader more aggressive at content extraction
- Results vary by page structure

### Code Block Preservation

Both preserve code blocks well:

**Tavily output**:
```
from fastapi import FastAPI

app = FastAPI()

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

**Jina Reader output**:
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}
```

**Winner**: **Jina Reader** - cleaner markdown with language hints

### Navigation Cruft

Both include some navigation, but patterns differ:
- Tavily: Includes menu items as text
- Jina Reader: Includes more links but cleaner structure

---

## 3. Unique Features

### Tavily Unique Features

| Feature | Description | Use Case |
|---------|-------------|----------|
| `--query` + `--chunks-per-source` | Rerank content by relevance | Get only relevant sections |
| `--extract-depth advanced` | Better JS rendering | SPAs, dynamic content |
| Batch (20 URLs) | Parallel processing | Crawl multiple pages |
| `--timeout` up to 60s | Handle slow pages | Large documents |
| Structured output | JSON with metadata | Programmatic use |

**Query-focused extraction example**:
```bash
# Get only relevant chunks instead of full page
tvly extract "https://docs.example.com/api" \
  --query "authentication JWT tokens" \
  --chunks-per-source 3
```

### Our Scraper Unique Features

| Feature | Description | Use Case |
|---------|-------------|----------|
| `llms.txt` support | Check for curated index | LLM-optimized sites |
| Accept header | Server-side markdown | Cloudflare sites |
| .md extension | Direct markdown URL | nbdev projects |
| Local caching | Avoid re-fetching | Development iteration |
| Rate limiting | Built-in delays | Polite scraping |
| Robots.txt compliance | Respect site rules | Ethical scraping |
| User-Agent rotation | Avoid blocking | Aggressive sites |

---

## 4. Use Case Analysis

### A. Temporary Query for Development

**Scenario**: You encounter a new library/framework and need quick reference.

```bash
# Option 1: Tavily (fast, structured)
tvly extract "https://fastapi.tiangolo.com/tutorial/path-params/" --json

# Option 2: Our scraper via Jina Reader (free, no auth)
curl -sL "https://r.jina.ai/https://fastapi.tiangolo.com/tutorial/path-params/"
```

**Recommendation**:
- **Quick lookup**: Jina Reader (free, no setup)
- **Structured integration**: Tavily (JSON output, metadata)

### B. Handoff Dumping for Context

**Scenario**: You need to dump multiple pages as context for an LLM.

```bash
# Option 1: Tavily batch (fast parallel)
tvly extract \
  "https://docs.example.com/page1" \
  "https://docs.example.com/page2" \
  "https://docs.example.com/page3" \
  --json > context.json

# Option 2: Our scraper (sequential but free)
for url in url1 url2 url3; do
  curl -sL "https://r.jina.ai/$url"
done > context.md
```

**Recommendation**:
- **Many pages (>5)**: Tavily (parallel, faster)
- **Few pages (<5)**: Jina Reader (free)
- **Budget constrained**: Jina Reader (always free)

### C. Complex Issues Not in Training Data

**Scenario**: New API, breaking changes, or niche library.

```bash
# Tavily with query focus (get only relevant parts)
tvly extract "https://docs.new-lib.com/changelog" \
  --query "breaking changes migration" \
  --chunks-per-source 5

# Our scraper (full content)
curl -sL "https://r.jina.ai/https://docs.new-lib.com/changelog"
```

**Recommendation**:
- **Targeted info**: Tavily (--query feature)
- **Full context**: Jina Reader (complete content)

---

## 5. Cost Analysis

### Tavily

| Plan | Extract Calls | Cost |
|------|---------------|------|
| Free tier | 1,000/month | $0 |
| Pro | Pay per use | Metered |
| Enterprise | Custom | Contact |

### Our Scraper (Jina Reader)

| Aspect | Cost |
|--------|------|
| API calls | Free |
| Authentication | Not required |
| Rate limits | None documented |
| Risk | May be blocked by aggressive sites |

---

## 6. Integration Examples

### Using Both Together

```python
class HybridScraper:
    """Use Tavily for batch, Jina for single."""
    
    def fetch_single(self, url: str) -> str:
        """Fast single URL fetch via Jina Reader."""
        return requests.get(f"https://r.jina.ai/{url}").text
    
    def fetch_batch(self, urls: list[str]) -> list[str]:
        """Parallel batch fetch via Tavily."""
        result = subprocess.run([
            "tvly", "extract", *urls, "--json"
        ], capture_output=True)
        data = json.loads(result.stdout)
        return [r["raw_content"] for r in data["results"]]
```

### Decision Matrix

| Condition | Use |
|-----------|-----|
| 1-2 URLs, quick lookup | Jina Reader |
| 5+ URLs batch | Tavily |
| Need relevance filtering | Tavily (--query) |
| No API key available | Jina Reader |
| Budget constrained | Jina Reader |
| Production reliability | Tavily |
| Development/iteration | Jina Reader |

---

## 7. Summary

### Tavily Extract Advantages

1. **Parallel batch processing** (up to 20 URLs)
2. **Query-focused extraction** (unique feature)
3. **Advanced JS rendering** option
4. **Structured JSON output** with metadata
5. **Reliable API** with SLA

### Our Scraper Advantages

1. **Free** (no API key or credits)
2. **Multiple fallback methods** (llms.txt, Accept header, .md extension)
3. **Local caching** for development iteration
4. **Rate limiting and robots.txt compliance**
5. **No authentication required**

### Recommendation

**For development workflow**: Use **Jina Reader** for quick lookups (free, no setup). Use **Tavily** for batch operations or when you need query-focused extraction.

**For production scraping**: Consider using both - Tavily for reliability and structured output, our scraper with caching for cost efficiency on repeated fetches.
