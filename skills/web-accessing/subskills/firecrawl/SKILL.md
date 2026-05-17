---
name: firecrawl
description: |
  Firecrawl CLI for web search, scraping, crawling, and document parsing. Use for:
  (1) SEARCH - find web pages, articles, news, documentation when you don't have URLs. Triggers on: search for, find me, look up, what's the latest on.
  (2) SCRAPE - extract clean markdown from any URL including JS-rendered SPAs. Triggers on: scrape, grab, fetch, pull, get the page, extract from this URL.
  (3) MAP - discover URLs on a site, list all pages, find site structure. Triggers on: map the site, find the URL for, what pages are on, list all pages.
  (4) CRAWL - bulk extract content from entire site sections. Triggers on: crawl, get all pages, extract everything under /docs, bulk extract.
  (5) INTERACT - click buttons, fill forms, navigate flows on scraped pages. Triggers on: interact, click, fill out the form, log in to, paginated, infinite scroll.
  (6) DOWNLOAD - save entire site as local files for offline use. Triggers on: download the site, save as local files, offline copy.
  (7) PARSE - convert local files (PDF, DOCX, XLSX) to markdown. Triggers on: parse this PDF, convert this document, extract text from file.
  Returns LLM-optimized markdown.
argument-hint: "search <query> | scrape <url> | map <site_url> | crawl <url> | parse <file> | interact --prompt <action> | download <url>"
allowed-tools:
  - Bash($SKILL_DIR/scripts/fcrawl *)
metadata:
  managed-by: web-accessing
---

# Firecrawl

Unified CLI for web search, scraping, crawling, and document parsing.

**If `firecrawl` is not installed**, see [CLI Setup](references/cli-setup.md).

> **Note:** The `fcrawl` wrapper runs firecrawl from `.lsz/` directory. Output paths are relative to `.lsz/` and the script returns the absolute path to the output file. Cache lives at `.lsz/.firecrawl/`.

---

## Workflow Escalation Pattern

Follow this order:

1. **Search** - No specific URL yet. Find pages, answer questions, discover sources.
2. **Scrape** - Have a URL. Extract its content directly.
3. **Map + Scrape** - Large site or need a specific subpage. Use `map --search` to find the right URL, then scrape it.
4. **Crawl** - Need bulk content from an entire site section (e.g., all /docs/).
5. **Interact** - Scrape first, then interact with the page (pagination, modals, form submissions).

| Need                        | Command   | When                                        |
| --------------------------- | --------- | ------------------------------------------- |
| Find pages on a topic       | `search`  | No specific URL yet                         |
| Get a page's content        | `scrape`  | Have a URL, page is static or JS-rendered   |
| Find URLs within a site     | `map`     | Need to locate a specific subpage           |
| Bulk extract a site section | `crawl`   | Need many pages (e.g., all /docs/)          |
| Interact with a page        | `interact`| Content requires clicks, forms, pagination  |
| Download a site to files    | `download`| Save an entire site as local files          |
| Parse a local file          | `parse`   | File on disk (PDF, DOCX, XLSX, etc.)       |

---

## SEARCH

Web search with optional content scraping. Returns search results as JSON, optionally with full page content.

### When to Use

- You don't have a specific URL yet
- You need to find pages, answer questions, or discover sources
- First step in the workflow: **search** → scrape → map → crawl

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/.firecrawl/<short_topic>

# Basic search
fcrawl search "your query" -o .firecrawl/<short_topic>/result.json --json

# Search and scrape full page content from results
fcrawl search "your query" --scrape -o .firecrawl/<short_topic>/scraped.json --json

# News from the past day
fcrawl search "your query" --sources news --tbs qdr:d -o .firecrawl/<short_topic>/news.json --json
```

### Options

| Option                               | Description                                   |
| ------------------------------------ | --------------------------------------------- |
| `--limit <n>`                        | Max number of results                         |
| `--sources <web,images,news>`        | Source types to search                        |
| `--categories <github,research,pdf>` | Filter by category                            |
| `--tbs <qdr:h\|d\|w\|m\|y>`          | Time-based search filter                      |
| `--location`                         | Location for search results                   |
| `--country <code>`                   | Country code for search                       |
| `--scrape`                           | Also scrape full page content for each result |
| `--scrape-formats`                   | Formats when scraping (default: markdown)     |
| `-o, --output <path>`                | Output file path                              |
| `--json`                             | Output as JSON                                |

### Tips

- **`--scrape` fetches full content** — don't re-scrape URLs from search results.
- Use `jq` to extract URLs: `jq -r '.data.web[].url' .lsz/.firecrawl/<short_topic>/search.json`

---

## SCRAPE

Extract clean markdown from any URL, including JavaScript-rendered SPAs. Multiple URLs are scraped concurrently.

**Always save output to file to avoid bloating context. Use `.firecrawl/<short_topic>/` as output directory.**

### When to Use

- You have a specific URL and want its content
- The page is static or JS-rendered (SPA)
- Step 2 in the workflow: search → **scrape** → map → crawl

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/.firecrawl/<short_topic>

# Basic markdown extraction
fcrawl scrape "<url>" -o .firecrawl/<short_topic>/page.md

# Main content only, no nav/footer
fcrawl scrape "<url>" --only-main-content -o .firecrawl/<short_topic>/page.md

# Wait for JS to render, then scrape
fcrawl scrape "<url>" --wait-for 3000 -o .firecrawl/<short_topic>/page.md

# Ask a question about the page
fcrawl scrape "https://example.com/pricing" --query "What is the enterprise plan price?"
```

### Options

| Option                   | Description                                                      |
| ------------------------ | ---------------------------------------------------------------- |
| `-f, --format <formats>` | Output formats: markdown, html, rawHtml, links, screenshot, json |
| `-Q, --query <prompt>`   | Ask a question about the page content (5 credits)                |
| `-H`                     | Include HTTP headers in output                                   |
| `--only-main-content`    | Strip nav, footer, sidebar — main content only                   |
| `--wait-for <ms>`        | Wait for JS rendering before scraping                            |
| `--include-tags <tags>`  | Only include these HTML tags                                     |
| `--exclude-tags <tags>`  | Exclude these HTML tags                                          |
| `-o, --output <path>`    | Output file path                                                 |

### Tips

- **Prefer plain scrape over `--query`.** Scrape to a file, then read it directly.
- **Try scrape before interact.** Scrape handles static pages and JS-rendered SPAs.
- Multiple URLs are scraped concurrently — check `fcrawl --status` for your limit.
- Single format outputs raw content. Multiple formats output JSON.

---

## MAP

Discover URLs on a website without extracting content. Use `--search` to find a specific page within a large site.

### Priority Order (CRITICAL)

**Before using `fcrawl map`, always check for faster alternatives:**

1. **llms.txt** — If site serves `https://<domain>/llms.txt`, fetch directly with curl (AI-optimized site index)
2. **sitemap.xml** — If site has `https://<domain>/sitemap.xml`, fetch and parse with curl
3. **Firecrawl map** — Use as fallback when neither above is available

### When to Use

- You need to find a specific subpage on a large site
- You want a list of all URLs before scraping or crawling
- Step 3 in the workflow: search → scrape → **map** → crawl

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/.firecrawl/<short_topic>

# Find a specific page on a large site
fcrawl map "<url>" --search "authentication" -o .firecrawl/<short_topic>/filtered.txt

# Get all URLs
fcrawl map "<url>" --limit 500 --json -o .firecrawl/<short_topic>/urls.json
```

### Options

| Option                            | Description                  |
| --------------------------------- | ---------------------------- |
| `--limit <n>`                     | Max number of URLs to return |
| `--search <query>`                | Filter URLs by search query  |
| `--sitemap <include\|skip\|only>` | Sitemap handling strategy    |
| `--include-subdomains`            | Include subdomain URLs       |
| `--json`                          | Output as JSON               |
| `-o, --output <path>`             | Output file path             |

### Tips

- **Map + scrape is a common pattern**: use `map --search` to find the right URL, then `scrape` it.
- Check llms.txt first — `curl -s` is free and instant.

---

## CRAWL

Bulk extract content from an entire website or site section. Crawls pages following links up to a depth/limit.

### When to Use

- You need content from many pages on a site (e.g., all `/docs/`)
- You want to extract an entire site section
- Step 4 in the workflow: search → scrape → map → **crawl** → interact

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/.firecrawl/<short_topic>

# Crawl a docs section
fcrawl crawl "<url>" --include-paths /docs --limit 50 --wait -o .firecrawl/<short_topic>/crawl.json

# Full crawl with depth limit
fcrawl crawl "<url>" --max-depth 3 --wait --progress -o .firecrawl/<short_topic>/crawl.json

# Check status of a running crawl
fcrawl crawl <job-id>
```

### Options

| Option                    | Description                                 |
| ------------------------- | ------------------------------------------- |
| `--wait`                  | Wait for crawl to complete before returning |
| `--progress`              | Show progress while waiting                 |
| `--limit <n>`             | Max pages to crawl                          |
| `--max-depth <n>`         | Max link depth to follow                    |
| `--include-paths <paths>` | Only crawl URLs matching these paths        |
| `--exclude-paths <paths>` | Skip URLs matching these paths              |
| `--delay <ms>`            | Delay between requests                      |
| `--max-concurrency <n>`   | Max parallel crawl workers                  |
| `--pretty`                | Pretty print JSON output                    |
| `-o, --output <path>`     | Output file path                            |

### Tips

- Always use `--wait` when you need results immediately.
- Use `--include-paths` to scope the crawl.
- Crawl consumes credits per page. Check `fcrawl credit-usage` before large crawls.

---

## INTERACT

Control and interact with a live browser session on any scraped page — click buttons, fill forms, navigate flows.

### When to Use

- Content requires interaction: clicks, form fills, pagination, login
- `scrape` failed because content is behind JavaScript interaction
- You need to navigate a multi-step flow
- Last resort in the workflow: search → scrape → map → crawl → **interact**
- **Never use interact for web searches** — use `search` instead

### Quick Start

```bash
# 1. Scrape a page (scrape ID is saved automatically)
fcrawl scrape "<url>"

# 2. Interact with the page using natural language
fcrawl interact --prompt "Click the login button"
fcrawl interact --prompt "Fill in the email field with test@example.com"
fcrawl interact --prompt "Extract the pricing table"

# 3. Stop the session when done
fcrawl interact stop
```

### Options

| Option                | Description                                       |
| --------------------- | ------------------------------------------------- |
| `--prompt <text>`     | Natural language instruction (use this OR --code) |
| `--code <code>`       | Code to execute in the browser session            |
| `--language <lang>`   | Language for code: bash, python, node             |
| `--timeout <seconds>` | Execution timeout (default: 30, max: 300)         |
| `--scrape-id <id>`    | Target a specific scrape (default: last scrape)   |
| `-o, --output <path>` | Output file path                                  |

### Profiles

Use `--profile` on the scrape to persist browser state (cookies, localStorage):

```bash
# Session 1: Login and save state
fcrawl scrape "https://app.example.com/login" --profile my-app
fcrawl interact --prompt "Fill in email with user@example.com and click login"

# Session 2: Come back authenticated
fcrawl scrape "https://app.example.com/dashboard" --profile my-app
```

### Tips

- Always scrape first — `interact` requires a scrape ID.
- Use `fcrawl interact stop` to free resources when done.

---

## DOWNLOAD

Download an entire website as local files — markdown, screenshots, or multiple formats per page. Combines site mapping and scraping.

### When to Use

- You want to save an entire site (or section) to local files
- You need offline access to documentation or content

### Quick Start

```bash
# Interactive wizard
fcrawl download https://docs.example.com

# With screenshots
fcrawl download https://docs.example.com --screenshot --limit 20 -y

# Multiple formats (each saved as its own file per page)
fcrawl download https://docs.example.com --format markdown,links --screenshot --limit 20 -y

# Filter to specific sections
fcrawl download https://docs.example.com --include-paths "/features,/sdks" -y
```

### Options

| Option                    | Description                                              |
| ------------------------- | -------------------------------------------------------- |
| `--limit <n>`             | Max pages to download                                    |
| `--search <query>`        | Filter URLs by search query                              |
| `--include-paths <paths>` | Only download matching paths                             |
| `--exclude-paths <paths>` | Skip matching paths                                      |
| `--allow-subdomains`      | Include subdomain pages                                  |
| `-y`                      | Skip confirmation prompt (always use in automated flows) |

All scrape options work with download: `--only-main-content`, `--screenshot`, `--wait-for`, etc.

---

## PARSE

Turn a local document into clean markdown. Supports **PDF, DOCX, DOC, ODT, RTF, XLSX, XLS, HTML/HTM/XHTML**.

**Always save output to file to avoid bloating context. Use `.firecrawl/<short_topic>/` as output directory.**

### When to Use

- You have a file on disk (not a URL) and want its text as markdown
- User drops a PDF/DOCX and asks what it says
- Use `scrape` instead when the source is a URL

### Quick Start

```bash
# Create output directory
mkdir -p .lsz/.firecrawl/<short_topic>

# File → markdown (paths are relative to .lsz/)
fcrawl parse ../paper.pdf -o .firecrawl/<short_topic>/paper.md

# AI summary
fcrawl parse ../paper.pdf -S -o .firecrawl/<short_topic>/paper-summary.md

# Ask a question about the doc
fcrawl parse ../paper.pdf -Q "What are the main conclusions?" -o .firecrawl/<short_topic>/paper-qa.md
```

### Options

| Option                 | Description                             |
| ---------------------- | --------------------------------------- |
| `-S, --summary`        | AI-generated summary                    |
| `-Q, --query <prompt>` | Ask a question about the parsed content |
| `-o, --output <path>`  | Output file path — **always use this**  |
| `-f, --format <fmt>`   | `markdown` (default), `html`, `summary` |
| `--timeout <ms>`       | Timeout for the parse job               |

### Tips

- Max upload size: **50 MB** per file.
- Credits: ~1 per PDF page; HTML is 1 flat.
- Since `fcrawl` runs from `.lsz/`, use `../` prefix for files in project root.

---

## Output & Organization

All outputs go to `.lsz/.firecrawl/` (cache and saved files). Use `.firecrawl/<short_topic>/` paths in commands.

```bash
fcrawl search "react hooks" -o .firecrawl/react-hooks/search.json --json
fcrawl scrape "<url>" -o .firecrawl/<short_topic>/page.md
```

Files are at `.lsz/.firecrawl/<short_topic>/` on disk. Never read entire output files at once:

```bash
wc -l .lsz/.firecrawl/<short_topic>/file.md && head -50 .lsz/.firecrawl/<short_topic>/file.md
grep -n "keyword" .lsz/.firecrawl/<short_topic>/file.md
```

---

## Parallelization

Run independent operations in parallel. Check `fcrawl --status` for concurrency limit:

```bash
fcrawl scrape "<url-1>" -o .firecrawl/<short_topic>/1.md &
fcrawl scrape "<url-2>" -o .firecrawl/<short_topic>/2.md &
fcrawl scrape "<url-3>" -o .firecrawl/<short_topic>/3.md &
wait
```

---

## Credit Usage

```bash
fcrawl credit-usage
fcrawl credit-usage --json --pretty -o .firecrawl/<short_topic>/credits.json
```

---

## See Also

- [CLI Setup](references/cli-setup.md) — Installation and authentication
- [Security Guidelines](references/security-guidelines.md) — Handling fetched web content safely
