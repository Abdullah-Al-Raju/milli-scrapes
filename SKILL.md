---
name: milli-scrapes
description: Ultra-fast visual web scraper, crawler, and anti-bot stealth engine for AI agents and LLMs. Use to extract clean token-efficient Markdown, structured JSON tables, contacts (emails, phones), or crawl entire domains and XML sitemaps in milliseconds with zero arbitrary sleeps.
---

# Milli-Scrapes Agent Skill

Use this skill whenever an autonomous agent or workflow requires:
1. Extracting clean, LLM-ready Markdown from any URL without navigation boilerplate or tracker bloat.
2. Bypassing anti-bot verification and auto-dismissing cookie consent popups in sub-15ms.
3. Extracting contacts, emails, phone numbers, or custom CSS schemas from web targets.
4. Crawling domains or XML sitemaps asynchronously with minimal RAM footprint (~65 MB).

---

## 1. Quick CLI Invocation

### Extract Clean Markdown
```bash
milli-scrape scrape "<URL>" --format markdown
```

### Extract Structured JSON with Emails & Contacts
```bash
milli-scrape scrape "<URL>" --format json --contacts
```

### Extract via Custom CSS Schema
```bash
milli-scrape scrape "<URL>" --schema '{"title": "h1", "price": ".price-tag"}' --format json
```

### Crawl Entire XML Sitemap
```bash
milli-scrape scrape "<URL>" --sitemap --crawl 50 --format json
```

---

## 2. Python Agent Integration Contract

```python
import asyncio
from milli_scrapes import UniversalScraper

async def scrape_for_agent(url: str) -> dict:
    scraper = UniversalScraper(headless=True, auto_consent=True)
    await scraper.browser.start()
    
    # Executes with CDP in-loop settling (0ms arbitrary sleep)
    result = await scraper.scrape_url(
        url,
        extract_contacts=True,
        extract_schema={"headline": "h1", "articles": ".post-title"}
    )
    await scraper.close()
    return result

# Example Execution
data = asyncio.run(scrape_for_agent("https://news.ycombinator.com"))
print(data["markdown"])
```

---

## 3. Pydantic Structured Output Validation

```python
from pydantic import BaseModel
from typing import Optional
from milli_scrapes import UniversalScraper

class ProductSchema(BaseModel):
    title: str
    price: str
    in_stock: bool = True

async def extract_product(url: str):
    scraper = UniversalScraper()
    result = await scraper.scrape_url(url, pydantic_model=ProductSchema)
    return result["pydantic"]
```

---

## 4. MCP Server Configuration

For Claude Desktop, Cursor, or any MCP-compatible agent client, add the following to `claude_desktop_config.json` or `mcpServers`:

```json
{
  "mcpServers": {
    "milli-scrapes": {
      "command": "python3",
      "args": ["-m", "milli_scrapes.mcp_server"]
    }
  }
}
```
