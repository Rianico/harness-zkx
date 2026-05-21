---
name: web-accessing
description: >-
  |
  Web access layer for AI agents. Routes to tavily for search, extraction, crawling, and AI-powered research, or firecrawl for search, scraping, crawling, and document parsing.
  TRIGGER on: web search, scrape, crawl, extract from URL, map the site, research, download docs, parse PDF/DOCX, interact with pages, get web content.
arguments: tool command
argument-hint: |
  tavily search|extract|map|crawl|research -- Tavily for search, extract, research
  firecrawl search|scrape|map|crawl|parse|interact|download -- Firecrawl for scrape, interact, parse
metadata:
  manage: [tavily, firecrawl]
---

# Web Accessing

Web access layer for AI agents. Single entry point for web search, scraping, crawling, extraction, and research.

## Sub-Skill Registry

```yaml
subskills:
  tavily: $SKILL_DIR/subskills/tavily/SKILL.md
  firecrawl: $SKILL_DIR/subskills/firecrawl/SKILL.md
```

## Tool Selection Guide

| Need | Tool | Why |
|------|------|-----|
| Search the web | `tavily search` or `firecrawl search` | Both support search |
| Extract from URL | `tavily extract` or `firecrawl scrape` | Tavily for batch, Firecrawl for JS-heavy pages |
| Research with citations | `tavily research` | AI-powered deep research |
| Interact with pages | `firecrawl interact` | Click, fill forms, navigate flows |
| Parse local files | `firecrawl parse` | PDF, DOCX, XLSX to markdown |
| Download site | `firecrawl download` | Save entire site locally |
| Map site URLs | `tavily map` or `firecrawl map` | Both support URL discovery |

### When to Choose Tavily

- AI-powered research with citations
- Batch URL extraction (up to 20 URLs)
- Query-focused extraction (get relevant chunks, not full pages)
- Need relevance scores

### When to Choose Firecrawl

- JavaScript-rendered SPAs
- Page interaction (clicks, forms, pagination)
- Parse local files (PDF, DOCX, XLSX)
- Download entire sites
- Screenshots and multiple output formats

## Dispatch

Parse `$ARGUMENTS` to determine tool:

| First Arg | Action |
|-----------|--------|
| `tavily` | Read `$SKILL_DIR/subskills/tavily/SKILL.md` and follow its instructions |
| `firecrawl` | Read `$SKILL_DIR/subskills/firecrawl/SKILL.md` and follow its instructions |

### `/web-accessing tavily [search|extract|map|crawl|research] ...`

Read `$SKILL_DIR/subskills/tavily/SKILL.md` and follow its instructions for the specified command.

### `/web-accessing firecrawl [search|scrape|map|crawl|parse|interact|download] ...`

Read `$SKILL_DIR/subskills/firecrawl/SKILL.md` and follow its instructions for the specified command.

### No argument provided

If `$ARGUMENTS` is empty, ask the user which tool they need:

1. **tavily** — "I need web search, URL extraction, or AI-powered research with citations"
2. **firecrawl** — "I need to scrape JS-heavy pages, interact with pages, parse files, or download sites"
