# Milli Scrapes API Reference & Migration Guide

> **Base URL**: `http://localhost:8000/v1` (Local) or your hosted gateway domain  
> **Interactive Playground**: `http://localhost:8000/`  
> **Interactive Swagger / OpenAPI Docs**: `http://localhost:8000/docs`  
> **Licensing**: Milli Source-Available Dual License (Free for research/personal, commercial license required for production/SaaS).

---

## 1. Quickstart

### Launch the Server Locally ($0 Cost)
```bash
milli-scrape serve --port 8000
```
Or with Docker:
```bash
docker compose up -d
```

---

## 2. Authentication

By default, the server runs in open evaluation mode. To enforce authentication, set the `MILLI_API_KEY` environment variable:
```bash
export MILLI_API_KEY="milli_live_sec_12345"
```
Pass your API key using either:
```bash
Authorization: Bearer <your_api_key>
# or
X-Milli-Key: <your_api_key>
```

---

## 3. Endpoints

### 3.1. `POST /v1/scrape` (High-Speed Single URL Extraction)
Scrapes a single URL in milliseconds. Automatically attempts Fast-Path HTTP (20ms) and cascades to the in-loop Chromium optical browser if dynamic hydration or anti-bot challenge gates (e.g. Turnstile) are detected.

#### Request Body
```json
{
  "url": "https://news.ycombinator.com",
  "format": "markdown",
  "extract_contacts": true,
  "chunk": false,
  "triage": true
}
```

#### Native Response Example
```json
{
  "success": true,
  "url": "https://news.ycombinator.com",
  "status": 200,
  "title": "Hacker News",
  "engine": "fast_http",
  "elapsed_ms": 28.4,
  "markdown": "# Hacker News\n\n1. Show HN: Milli-Agent...",
  "metadata": {
    "title": "Hacker News",
    "description": "Social news for developers"
  },
  "contacts": {
    "emails": [],
    "phones": []
  },
  "tables": [],
  "triage": {
    "is_blocked_by_bot_gate": false,
    "is_paywalled": false,
    "has_pagination": true,
    "layout_type": "FORUM",
    "content_density_score": 0.88
  },
  "token_reduction_percent": 75.0,
  "speedup_vs_firecrawl": "65.1x"
}
```

---

### 3.2. Firecrawl Drop-In Compatibility Mode
Milli Scrape API is **100% drop-in compatible with existing Firecrawl SDKs and pipelines**.

#### How to Switch in JavaScript / TypeScript (5 Seconds)
```typescript
import { FirecrawlApp } from '@mendable/firecrawl-js';

// Simply change the apiUrl to your Milli instance:
const app = new FirecrawlApp({
  apiUrl: 'http://localhost:8000/v1',
  apiKey: 'milli_demo_key'
});

// Works identically, but runs 1.8x faster with 75% fewer tokens:
const result = await app.scrapeUrl('https://example.com');
console.log(result.data.markdown);
```

#### How to Switch in Python
```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_url="http://localhost:8000/v1", api_key="milli_demo_key")
res = app.scrape_url("https://example.com")
print(res["data"]["markdown"])
```

---

### 3.3. `POST /v1/map` (Sub-Second Domain Topology Discovery)
Discovers all internal links and sitemaps without downloading heavy page bodies.

#### Request
```json
{
  "url": "https://fastapi.tiangolo.com",
  "max_urls": 500,
  "search": "tutorial"
}
```

#### Response
```json
{
  "success": true,
  "base_url": "https://fastapi.tiangolo.com",
  "urls_found": 42,
  "sitemaps": ["https://fastapi.tiangolo.com/sitemap.xml"],
  "links": [
    "https://fastapi.tiangolo.com/tutorial/",
    "https://fastapi.tiangolo.com/tutorial/first-steps/"
  ],
  "elapsed_ms": 312.5
}
```

---

### 3.4. `POST /v1/decision/triage` (System 1 Page Triage)
Classifies any HTML payload in a single forward pass (< 0.5 ms) without generating LLM tokens.

#### Request
```json
{
  "html": "<html><body>Verify you are human. Cloudflare Ray ID: 890a.</body></html>",
  "url": "https://target-site.com"
}
```

#### Response
```json
{
  "success": true,
  "url": "https://target-site.com",
  "is_blocked": true,
  "is_paywalled": false,
  "has_pagination": false,
  "layout_type": "CAPTCHA_GATE",
  "content_density_score": 0.05,
  "elapsed_ms": 0.18
}
```

---

### 3.5. `GET /v1/health` (Operational Health & Token Savings)
Returns real-time server metrics:
```json
{
  "uptime_seconds": 3600.0,
  "total_requests": 1420,
  "scrapes_completed": 1280,
  "crawls_completed": 45,
  "decisions_completed": 95,
  "estimated_tokens_saved": 1845000,
  "active_clients": 14,
  "status": "healthy",
  "engine": "Milli Scrapes Universal Engine v0.1.0"
}
```
