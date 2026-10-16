# Milli-Scrapes: Ultra-Fast Visual Web Scraper, Change Monitor, and Reflex Booking Engine

Milli-Scrapes is a high-frequency autonomous web scraping, optical website change detection, and sub-15ms reflex booking engine built for high-demand slot reservation and zero-sleep web automation.

By integrating the Milli low-latency architecture—direct WebSocket Chrome DevTools Protocol (CDP) execution and transient RAM optical frame processing—Milli-Scrapes eliminates the multi-second latency bottlenecks of conventional scrapers (Playwright, Selenium, Puppeteer).

---

## 1. Executive Summary and Architecture

### The Bottleneck in Current Web Scrapers
Conventional scrapers (Firecrawl, Crawl4AI, changedetection.io) rely on heavyweight browser wrappers (Playwright/Puppeteer) that incur severe penalties:
- High Memory Footprint: 850 MB to 1.5 GB RAM per browser worker.
- Sluggish Turn Latency: 2,000 ms to 6,000 ms per page due to inter-process wrappers and arbitrary `wait_for_timeout()` sleeps.
- Disk Degradation: Writing uncompressed screenshots to disk for visual diffing.
- Blind to Canvas/SVG Layouts: Ineffective on interactive Canvas seatmaps, animated slot drops, and dynamic booking countdowns.

### The Milli-Scrapes Advantage
- In-Loop WebSocket CDP: Direct JSON-RPC connection over WebSockets inside the browser run-loop (< 0.05 ms dispatch).
- Mutation-Driven Reactive Settling: Injects high-frequency DOM `MutationObserver` hooks (`wait_until_idle`). Returns the microsecond the page finishes rendering—0 ms arbitrary sleep.
- Hardened Memory Footprint: ~65 MB per headless worker (95.5% lighter than standard consumer automation browsers).
- Transient RAM Visual Manifold: Compares visual state shifts directly in memory at 60 FPS (0 bytes saved to secondary storage).
- Sub-15ms Reflex Seat Sniping: Dispatches clicks to available seat coordinates in 8.1 ms upon visual opening, outperforming human clickers (~280 ms) and conventional bot scalpers (~2,400 ms).
- Real-Time Email Alerts: Continuous website monitoring with in-memory JPEG snapshot proof attachments sent directly via SMTP/TLS.

---

## 2. Competitive Matrix

| Feature / Metric | Scrapy | Crawl4AI | Firecrawl | changedetection.io | Milli-Scrapes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Primary Engine | Twisted / HTTP requests | Playwright wrapper | Node.js / Playwright | Python / Playwright | Direct WebSocket CDP + RAM Manifold |
| JavaScript / SPA Support | Poor (Requires plugins) | Yes (via Playwright) | Yes (via Cloud API) | Yes (Periodic polling) | Yes (In-Loop DOM & Canvas) |
| Memory Footprint | ~30 MB | ~850 MB - 1.2 GB | ~1.5 GB+ | ~600 MB | ~65 MB (Hardened Headless CDP) |
| Settling Mechanism | N/A (Static HTML) | `wait_for_timeout` | Network idle heuristics | Periodic sleep intervals | MutationObserver Reactive Settling (0ms sleep) |
| Visual Perception | None | Static screenshot to disk | Static screenshot to disk | Disk screenshot diffing | Continuous 60Hz in Transient RAM (0 bytes disk) |
| Dynamic Canvas Support | None | Partial | Partial | Poor | Optical Centroid Saliency (Full Canvas) |
| Seat / Slot Sniping Latency | Incompatible | 1,500 - 3,500 ms | Incompatible (API only) | Minutes (Polling) | < 15 ms (Direct Hardware / CDP Dispatch) |
| Real-Time Change Alerts | Custom middleware | Custom | Custom webhooks | Yes (Apprise / SMTP) | Built-in SMTP Watcher with In-Memory JPEG Proof |

---

## 3. Installation and System Prerequisites

### Prerequisites
- Python 3.10 or higher
- Chromium, Google Chrome, or Brave Browser located in system PATH
- Supported Platforms: Linux (X11 / Wayland) and Windows 10/11

### Repository Setup
```bash
git clone https://github.com/Abdullah-Al-Raju/milli-scrapes.git
cd milli-scrapes
pip install -e .
```

---

## 4. Quickstart and Command-Line Interface

### 1. Ultra-Fast Clean Markdown Scraping
Extract clean, LLM-ready markdown stripped of navigation, scripts, and ads:
```bash
milli-scrape scrape https://example.com --format markdown
```

Extract structured tables and key-value JSON:
```bash
milli-scrape scrape https://example.com --format json
```

### 2. Website Change Monitor and Email Alerts
Monitor any webpage for visual or text changes and receive instant email alerts:
```bash
milli-scrape watch https://example.com/status --interval 2.0 --email user@example.com
```

### 3. Sub-15ms Reflex Seat / Slot Booking
Prime the sniper for high-demand ticket drops, cancellations, or appointment slots:
```bash
# Optical Canvas Mode (Locks onto available green seat centroid)
milli-scrape snipe https://booking.example.com/seatmap --mode optical --confirm #confirm-booking

# DOM In-Loop Mode (Strikes candidate selector the instant it renders)
milli-scrape snipe https://booking.example.com/slots --mode dom --seat .slot-available
```

---

## 5. Python API Usage

### Direct In-Loop Scraping
```python
import asyncio
from milli_scrapes.browser.engine import MilliScrapeBrowser
from milli_scrapes.extractor.markdown import HTMLToMarkdownExtractor

async def run():
    browser = MilliScrapeBrowser(headless=True)
    await browser.start()
    
    # Reactively settles in milliseconds without sleep statements
    page = await browser.navigate_and_settle("https://example.com")
    
    extractor = HTMLToMarkdownExtractor()
    markdown = extractor.extract(page["html"])
    print(markdown)
    
    await browser.aclose()

asyncio.run(run())
```

### Reflex Seat Sniping
```python
import asyncio
from milli_scrapes.browser.engine import MilliScrapeBrowser
from milli_scrapes.sniper.seat_sniper import ReflexSeatSniper

async def snipe_flight_seat():
    browser = MilliScrapeBrowser(headless=True)
    await browser.start()
    
    sniper = ReflexSeatSniper(browser=browser)
    await browser.navigate_and_settle("https://airline.example.com/seats")
    
    # Strikes the microsecond an available seat appears
    result = await sniper.snipe_optical_seat(confirm_selector="#confirm-booking")
    print(f"Booked in {result['time_to_finish_ms']} ms! Coords: {result['target_coords']}")
    
    await browser.aclose()

asyncio.run(snipe_flight_seat())
```

---

## 6. Empirical Benchmark Results

### Interactive Seatmap Sniping Benchmark
Evaluated against `benchmarks/seatmap_demo.html` with random seat drop times:
- Milli-Scrapes Reaction Latency: **8.10 ms**
- Milli-Scrapes Time To Finish (TTF): **21.29 ms**
- Typical Human Response Time: ~280.00 ms (22.4x slower)
- Conventional Selenium/Playwright Bot TTF: ~2,400.00 ms (192.0x slower)
- Booking Status: 100% Confirmation Success

Run the benchmark locally:
```bash
python3 benchmarks/run_sniper_benchmark.py
```

---

## 7. Autonomous Agent Integration

- **Model Context Protocol (MCP):** Connects natively with Claude Desktop, Cursor, and agent orchestrators.
- **Machine-Readable Specifications:** See [`llms.txt`](llms.txt) for raw specifications, latency figures, and API snippets.
- **Autonomous Agent Directive Contract:** See [`AGENTS.md`](AGENTS.md) for execution criteria and delegation protocols.

---

## 8. Licensing and Terms of Use

- **Personal, Academic, and Evaluation Use:** Milli-Scrapes is free to use, modify, and inspect for individual developers, students, researchers, and personal projects.
- **Commercial, Industrial, and Enterprise Use:** Deployment of Milli-Scrapes within commercial platforms, high-frequency commercial scalping services, or enterprise monitoring systems requires written licensing permission.

---

## 9. Research Fellowships and Inquiries

Milli-Scrapes was architected and built by **Abdullah-Al-Raju**.

I am actively seeking **Graduate Research Positions, Academic Fellowships, and AI Lab Collaborations** in foundation computer-use, high-frequency agent architectures, and autonomous web synthesis.

For academic recruitment, research collaborations, or commercial inquiries:
- **Email:** `analystx.raju@gmail.com`
- **GitHub:** [https://github.com/Abdullah-Al-Raju](https://github.com/Abdullah-Al-Raju)
