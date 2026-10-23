# Milli-Scrapes: Ultra-Fast Visual Web Scraper, Crawler, and Anti-Bot Stealth Engine for AI Agents

[![License](https://img.shields.io/badge/License-Personal_&_Academic_Free-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://python.org)
[![MCP Ready](https://img.shields.io/badge/MCP-Compatible-purple.svg)](SKILL.md)
[![Tests](https://img.shields.io/badge/Tests-20%2F20_Passed-success.svg)](tests/)
[![Memory Footprint](https://img.shields.io/badge/RAM_Footprint-~65_MB-orange.svg)](#2-competitive-matrix)

Milli-Scrapes is an ultra-fast autonomous web scraper, streaming XML crawler, and anti-bot stealth engine engineered specifically for LLMs, autonomous AI agents, and real-time RAG pipelines.

By executing directly over native Chrome DevTools Protocol (CDP) WebSockets with in-memory transient RAM frame processing, Milli-Scrapes settles dynamic JavaScript and React single-page applications (SPAs) in milliseconds with **zero arbitrary sleeps** and a lightweight **~65 MB RAM footprint** (vs. 1.5 GB in conventional Playwright/Puppeteer setups).

---

## 1. Executive Summary and Architectural Advantages

### The Bottleneck in Current Web Scrapers
Conventional scrapers (Crawl4AI, Firecrawl, Scrapy, Playwright) suffer from severe architectural limitations:
- **High Memory Overhead**: 850 MB to 1.5 GB RAM per browser worker, preventing scalable concurrent agent scraping.
- **Arbitrary Sleep Latency**: Forcing 2,000 ms to 5,000 ms per page using `wait_for_timeout()` sleeps to wait for dynamic elements.
- **Cookie & Consent Walls**: Stalled by OneTrust, Didomi, and Cookiebot modals that block scraping.
- **Heavy Disk Degradation**: Constant disk writes of screenshots and cached artifacts.

### The Milli-Scrapes Engine
- **In-Loop WebSocket CDP**: Direct JSON-RPC connection inside the browser run-loop (< 0.05 ms dispatch latency).
- **Mutation-Driven Reactive Settling**: Injects DOM `MutationObserver` hooks (`wait_until_idle`). Returns the microsecond the page finishes rendering—0 ms arbitrary sleep.
- **Anti-Bot Stealth Engine**: Pre-navigation CDP script injection masking `navigator.webdriver`, WebGL vendor/renderer, plugins, and runtime flags.
- **Sub-15ms Consent Auto-Dismiss**: Detects and dismisses cookie consent dialogs and overlay banners in under 15 milliseconds.
- **Zero-Shot Pydantic Validation**: Extracts and validates strongly-typed data directly into native Python Pydantic `BaseModel` classes.
- **Streaming XML Sitemap & Deep Crawler**: High-speed sitemap parser (`/sitemap.xml`, `robots.txt`) streaming batch crawls across domains.
- **Model Context Protocol (MCP) Native**: Out-of-the-box MCP server connecting with Cursor, Claude Desktop, and autonomous AI agents.
- **Transient RAM Visual Differ**: Monitors visual layout changes at 60 FPS in memory (0 bytes saved to secondary storage).

---

## 2. Competitive Matrix

| Feature / Metric | Scrapy | Crawl4AI | Firecrawl | Milli-Scrapes |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Engine** | Twisted / HTTP requests | Playwright wrapper | Node.js / Playwright API | Direct In-Loop WebSocket CDP |
| **JavaScript / SPA Support** | Poor (Requires Splash) | Yes (via Playwright) | Yes (via Cloud API) | Yes (In-Loop DOM & Canvas) |
| **RAM Footprint** | ~45 MB | ~850 MB | ~1,500 MB | **~65 MB (Ultra-Lightweight)** |
| **Settling Mechanism** | N/A (Static HTML) | `wait_for_timeout` sleeps | Network idle heuristics | **DOM Mutation Reactive Settling (0ms sleep)** |
| **Anti-Bot Stealth** | Needs proxy plugins | Basic stealth plugin | Cloud proxy pool | **In-Loop CDP Pre-Navigation Spoofing** |
| **Cookie Consent Dismissal** | None | Slow DOM clicks | Partial API bypass | **Sub-15ms In-Loop Auto-Dismiss** |
| **Pydantic Structured Output**| Custom pipelines | `JsonCssExtraction` | Cloud schema extract | **Native Zero-Shot Pydantic BaseModel** |
| **Sitemap Discovery** | `SitemapSpider` | Manual URL list | `/map` endpoint | **Streaming XML & Robots.txt Crawler** |
| **MCP AI Agent Support** | Custom | Third-party adapter | Third-party adapter | **Native Built-In MCP Server** |

---

## 3. Head-to-Head Benchmark: Milli Visual Scraper vs. Firecrawl CrawlBench

We evaluated Milli Visual Scraper directly against Firecrawl's published benchmark standard, **CrawlBench-Easy** (Y Combinator Startup Directory Extraction at `https://www.ycombinator.com/companies`):

| Performance Dimension | Firecrawl API (Published Baseline) | Milli Visual Scraper (Measured Live) | Milli Advantage |
| :--- | :---: | :---: | :--- |
| **Execution Architecture** | Cloud Container (Playwright + Redis) | **Local In-Memory Retina** (Native CDP + RAM) | **Zero Cloud Network Latency** |
| **Incremental Scroll Perception** | **$2,100\text{ ms}$** *(Must re-scrape entire page)* | **$57.2\text{ ms}$** *(In-loop continuum advection)* | **$36.8\times$ FASTER** |
| **Per-Event Token Emission** | $\sim 1,711$ tokens (Full page Markdown dump) | **$274\text{ tokens}$** (Saccadic foveal crop bounding box) | **$84.0\%$ FEWER tokens** |
| **Token Reduction vs. Raw HTML** | $93.5\%$ | **$97.4\%$** | **$3.9\%$ Greater Compression** |
| **DOM Obfuscation / Canvas** | **Fails** (relies on raw HTML text) | **Immune** (directly observes framebuffer pixels) | **Resilient to obfuscation** |
| **Cost Per 1,000 Scrapes** | **$\$15.00\text{ USD}$** (API credits) | **$\$0.00\text{ USD}$** (Local compute) | **100% Free & Unlimited** |

> See full details, extracted JSON schema, and reproduction instructions in [`benchmarks/CRAWLBENCH_MILLI_VS_FIRECRAWL.md`](benchmarks/CRAWLBENCH_MILLI_VS_FIRECRAWL.md) and [`benchmarks/crawlbench_milli_vs_firecrawl.json`](benchmarks/crawlbench_milli_vs_firecrawl.json).

---

## 3. Installation

### Prerequisites
- Python 3.10 or higher
- Chromium, Google Chrome, or Brave Browser located in system PATH
- Supported Platforms: Linux and Windows 10/11

```bash
git clone https://github.com/Abdullah-Al-Raju/milli-scrapes.git
cd milli-scrapes
pip install -e .
```

---

## 4. Quickstart and Command-Line Interface

### 1. Ultra-Fast Clean Markdown Extraction
Extract clean, token-efficient Markdown stripped of navigation chrome and ads:
```bash
milli-scrape scrape https://example.com --format markdown
```

### 2. Structured JSON Extraction with Automatic Contacts
Automatically extract verified emails, phone numbers, tables, and key-values:
```bash
milli-scrape scrape https://example.com --format json --contacts
```

### 3. Declarative Schema Extraction
Extract specific fields using CSS selectors without writing code:
```bash
milli-scrape scrape https://example.com --schema '{"title": "h1", "price": ".price"}' --format json
```

### 4. XML Sitemap Crawling
Crawl an entire domain automatically via its XML sitemap:
```bash
milli-scrape scrape https://example.com --sitemap --crawl 50 --format json
```

### 5. Website Change Monitoring and Email Alerts
Monitor any page for visual or text modifications and receive instant email notifications:
```bash
milli-scrape watch https://example.com/status --interval 2.0 --email user@example.com
```

---

## 5. Python API Usage

### Direct In-Loop Scraping with Anti-Bot Stealth
```python
import asyncio
from milli_scrapes import UniversalScraper

async def run():
    scraper = UniversalScraper(headless=True, auto_consent=True)
    await scraper.browser.start()
    
    # Settles reactively in milliseconds without arbitrary sleeps
    result = await scraper.scrape_url("https://example.com", extract_contacts=True)
    
    print("Clean Markdown:", result["markdown"])
    print("Extracted Emails:", result["contacts"]["emails"])
    
    await scraper.close()

asyncio.run(run())
```

### Zero-Shot Pydantic Structured Extraction
```python
from pydantic import BaseModel
from typing import Optional
from milli_scrapes import UniversalScraper

class Product(BaseModel):
    name: str
    price: str
    in_stock: bool = True

async def extract_product():
    scraper = UniversalScraper()
    result = await scraper.scrape_url(
        "https://store.example.com/item",
        pydantic_model=Product,
        extract_schema={"name": "h1.prod-title", "price": ".price-tag"}
    )
    print(result["pydantic"])
```

---

## 6. Autonomous AI Agent Integration

Milli-Scrapes is designed as a first-class tool for autonomous AI agents, multi-agent frameworks, and coding assistants:

- **Model Context Protocol (MCP)**: Run `python3 -m milli_scrapes.mcp_server` to connect with Cursor, Claude Desktop, and LangChain.
- **Agent Skill Directives**: See [`SKILL.md`](SKILL.md) for tool call schemas and integration instructions.
- **Machine-Readable API Contract**: See [`llms.txt`](llms.txt) for token-efficient prompt context and architecture metrics.
- **Autonomous Subagent Protocols**: See [`AGENTS.md`](AGENTS.md) for autonomous execution criteria.

---

## 7. Licensing and Terms of Use

- **Personal, Academic, and Evaluation Use:** Milli-Scrapes is free to use, modify, and inspect for individual developers, students, researchers, and personal projects.
- **Commercial, Industrial, and Enterprise Use:** Deployment of Milli-Scrapes within commercial platforms, SaaS products, or enterprise systems requires written licensing permission.

---

## 8. Research Inquiries and Contact

Milli-Scrapes was architected and developed by **Abdullah-Al-Raju**.

I am actively seeking **Graduate Research Positions, Academic Fellowships, and AI Lab Collaborations** in foundation computer-use, autonomous agent architectures, and web intelligence.

- **Email:** `analystx.raju@gmail.com`
- **GitHub:** [https://github.com/Abdullah-Al-Raju](https://github.com/Abdullah-Al-Raju)
