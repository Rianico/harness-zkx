# LLM-Friendly Web Patterns

Modern web scraping patterns optimized for AI/LLM consumption.

## 1. llms.txt Standard

**Source**: [llmstxt.org](https://llmstxt.org/) by Jeremy Howard / Answer.AI

### What It Is

A standardized markdown file at `/llms.txt` that provides LLM-friendly navigation to a website's content.

### Structure

```markdown
# Project Name

> Short summary of the project (blockquote)

Optional additional details and guidance.

## Section Name

- [Link Title](https://example.com/page.md): Optional description
- [Another Link](https://example.com/other.md)

## Optional

- [Secondary Content](https://example.com/optional.md): Can be skipped for shorter context
```

### Key Points

- **Location**: Root path `/llms.txt` (or subpath)
- **Required**: H1 with project/site name
- **Optional**: Blockquote summary, detail sections, H2 file lists
- **Special**: `## Optional` section marks content that can be skipped
- **Links**: Point to `.md` versions of pages

### Detection Pattern

```python
def check_llms_txt(base_url: str) -> str | None:
    """Check if site has llms.txt file."""
    llms_url = urljoin(base_url, "/llms.txt")
    try:
        response = requests.head(llms_url, timeout=10)
        if response.status_code == 200:
            return llms_url
    except requests.RequestException:
        pass
    return None
```

### Sites Using llms.txt

- [Anthropic](https://docs.anthropic.com/llms.txt)
- [Cloudflare](https://developers.cloudflare.com/llms.txt)
- [FastHTML](https://fastht.ml/docs/llms.txt)
- Any nbdev project

---

## 2. Accept: text/markdown Header

**Source**: [Cloudflare Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/) (Feb 2026)

### What It Is

Content negotiation header that requests markdown instead of HTML. Supported by Cloudflare-enabled sites.

### How It Works

```bash
# Request markdown version
curl https://developers.cloudflare.com/fundamentals/reference/markdown-for-agents/ \
  -H "Accept: text/markdown"
```

### Response Headers

```
HTTP/2 200
content-type: text/markdown; charset=utf-8
x-markdown-tokens: 725
content-signal: ai-train=yes, search=yes, ai-input=yes
```

### Token Savings

Cloudflare reports **80% token reduction**:
- HTML: 16,180 tokens
- Markdown: 3,150 tokens

### Detection Pattern

```python
def fetch_markdown(url: str) -> tuple[str | None, str]:
    """Try to fetch markdown version via content negotiation."""
    headers = {"Accept": "text/markdown, text/html"}
    response = requests.get(url, headers=headers)
    
    content_type = response.headers.get("content-type", "")
    if "text/markdown" in content_type:
        # Server returned markdown directly
        return response.text, "markdown"
    
    # Fallback to HTML
    return response.text, "html"
```

### Supported Platforms

- Cloudflare (automatic for enabled zones)
- Static Web Server (configurable)
- Netlify (requires edge function)
- Sites with custom markdown endpoints

---

## 3. .md URL Extension

### What It Is

Some sites serve markdown at the same URL with `.md` appended.

### Pattern

```
HTML:  https://example.com/docs/page.html
Markdown: https://example.com/docs/page.html.md

HTML:  https://example.com/docs/page
Markdown: https://example.com/docs/page.md
```

### Detection Pattern

```python
def try_md_extension(url: str) -> str | None:
    """Try fetching .md version of a URL."""
    md_url = url.rstrip("/") + ".md"
    if url.endswith("/"):
        md_url = url + "index.md"
    
    try:
        response = requests.head(md_url, timeout=10)
        if response.status_code == 200:
            return md_url
    except requests.RequestException:
        pass
    return None
```

---

## 4. Implementation Strategy

### Priority Order

When scraping a URL, try in order:

1. **Check for llms.txt** — Get structured navigation
2. **Try Accept: text/markdown** — Get markdown directly
3. **Try .md extension** — Get pre-converted markdown
4. **Fall back to HTML** — Convert locally

### Scraper Integration

```python
class LLMOptimizedScraper(BaseScraper):
    def fetch_page(self, url: str) -> tuple[str, str]:
        """Fetch page content with LLM-friendly optimizations."""
        
        # Try markdown via content negotiation
        headers = {"Accept": "text/markdown, text/html"}
        response = self._fetch_with_retry(url, headers=headers)
        
        content_type = response.headers.get("content-type", "")
        if "text/markdown" in content_type:
            return response.text, "markdown"
        
        # Try .md extension
        md_url = self._try_md_extension(url)
        if md_url:
            response = self._fetch_with_retry(md_url)
            return response.text, "markdown"
        
        # Fall back to HTML conversion
        return response.text, "html"
    
    def scrape_site(self, base_url: str) -> dict:
        """Scrape site using llms.txt if available."""
        result = {"pages": [], "format": "html"}
        
        # Check for llms.txt
        llms_url = self.check_llms_txt(base_url)
        if llms_url:
            llms_content = self._fetch_with_retry(llms_url).text
            pages = self._parse_llms_txt(llms_content)
            result["llms_txt"] = llms_content
            result["format"] = "markdown"
            
            for page in pages:
                content, fmt = self.fetch_page(page["url"])
                result["pages"].append({
                    "title": page["title"],
                    "url": page["url"],
                    "content": content,
                    "format": fmt,
                })
            
            return result
        
        # Fall back to standard scraping
        # ...
```

---

## 5. Benefits

| Pattern | Token Savings | Implementation | Coverage |
|---------|---------------|----------------|----------|
| llms.txt | High (curated) | Easy | Growing |
| Accept header | 80%+ | Easy | Cloudflare sites |
| .md extension | High | Easy | nbdev, some static sites |
| HTML conversion | Baseline | Complex | Universal |

---

## 6. URL Prefix Proxies

### Jina Reader (Free, Most Popular)

**URL Pattern**: `https://r.jina.ai/<original_url>`

```bash
# Get markdown for any page
curl "https://r.jina.ai/https://example.com/docs"

# Returns structured markdown with metadata:
# Title: ...
# URL Source: ...
# Published Time: ...
# Markdown Content:
# ...
```

**Features**:
- No API key required (free tier)
- Clean markdown extraction
- Removes navigation, ads, scripts
- Includes metadata (title, URL, publish time)

**Python Integration**:

```python
def fetch_via_jina_reader(url: str) -> str | None:
    """Fetch markdown via Jina Reader proxy."""
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url, timeout=30)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass
    return None
```

### Textise

**URL Pattern**: `https://www.textise.net/show?url=<original_url>`

Returns text-only version of pages. Good for accessibility-focused extraction.

---

## 7. API Services

### Firecrawl

**Full-featured web scraping API with markdown output.**

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_KEY")

# Scrape single page to markdown
result = app.scrape_url("https://example.com/docs")
markdown = result["markdown"]

# Crawl entire site
result = app.crawl_url("https://example.com", limit=100)
```

**Features**:
- JavaScript rendering (SPA support)
- Search + scrape combined
- Site mapping
- Structured extraction with AI prompts

### Apify Website-to-Markdown

```python
from apify_client import ApifyClient

client = ApifyClient("YOUR_API_TOKEN")
run = client.actor("pink_comic/website-content-to-markdown").call(
    run_input={"url": "https://example.com"}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["markdown"])
```

---

## 8. Local Processing Libraries

### html2text (Python) — Already in scraper

```python
import html2text

h = html2text.HTML2Text()
h.body_width = 0  # No line wrapping
markdown = h.handle(html_content)
```

### kreuzberg html-to-markdown (Rust, multi-language)

High-performance HTML to markdown conversion:
- Rust, Python, Node.js, Ruby, PHP, Go, Java, C#
- Faster than html2text
- Better table/list handling

```python
from html_to_markdown import convert_to_markdown

markdown = convert_to_markdown(html_content)
```

### Reader-LM (Small Language Model)

Jina AI's Reader-LM models (0.5B and 1.5B parameters) trained specifically for HTML→markdown conversion:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("jinaai/ReaderLM-v2")
tokenizer = AutoTokenizer.from_pretrained("jinaai/ReaderLM-v2")

# Convert HTML to markdown using LLM
inputs = tokenizer(html_content, return_tensors="pt")
outputs = model.generate(**inputs)
markdown = tokenizer.decode(outputs[0])
```

**Best for**: Complex pages with tables, equations, nested lists.

---

## 9. Comparison Table

| Method | Cost | JS Rendering | Speed | Best For |
|--------|------|--------------|-------|----------|
| Accept header | Free | No | Fastest | Cloudflare sites |
| Jina Reader | Free | No | Fast | Quick testing, any site |
| Firecrawl | Paid | Yes | Medium | SPAs, crawl jobs |
| html2text | Free | No | Fast | Simple pages |
| Reader-LM | Free | No | Slow | Complex content |

---

## 10. Implementation Priority

When fetching a URL, try in order:

1. **llms.txt** — Check for curated navigation
2. **Accept: text/markdown** — Server-side conversion (Cloudflare)
3. **Jina Reader** — Free proxy (`r.jina.ai/`)
4. **.md extension** — Static sites, nbdev
5. **Firecrawl API** — Complex SPAs (paid)
6. **html2text** — Local fallback (always works)

---

## 11. Sources

- [llms.txt Specification](https://llmstxt.org/)
- [Cloudflare Markdown for Agents](https://blog.cloudflare.com/markdown-for-agents/)
- [Static Web Server Markdown Negotiation](https://static-web-server.net/features/markdown-content-negotiation/)
- [DeployHQ: AI-Friendly Documentation](https://www.deployhq.com/blog/making-your-documentation-ai-friendly-serving-markdown-to-ai-coding-assistants)
