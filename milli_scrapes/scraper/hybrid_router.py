"""
Dual-Engine Hybrid Router for Milli-Scrapes.
Intelligently routes scraping targets between:
1. Fast-Path HTTP (~15-35 ms) for static documentation, blogs, and public articles.
2. Optical CDP Browser (~57 ms) for dynamic SPAs, infinite scrolls, and Cloudflare/Turnstile gates.
Combines Spider.cloud's microsecond HTTP speed with Milli's unbeatable visual perception.
"""

import time
import asyncio
import urllib.request
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from ..extractor.markdown import HTMLToMarkdownExtractor
from ..browser.engine import MilliScrapeBrowser


class HybridScrapeRouter:
    """
    Intelligent router delivering peak speed across both static and dynamic web environments.
    """

    def __init__(
        self,
        browser: Optional[MilliScrapeBrowser] = None,
        prefer_fast_path: bool = True
    ):
        self.browser = browser or MilliScrapeBrowser(headless=True)
        self.prefer_fast_path = prefer_fast_path
        self.md_extractor = HTMLToMarkdownExtractor()

    async def fetch_page(self, url: str, force_browser: bool = False) -> Dict[str, Any]:
        """
        Fetches and settles a page using the optimal engine.
        """
        t0 = time.perf_counter()

        if self.prefer_fast_path and not force_browser and not getattr(self.browser, "mock_mode", False):
            # Attempt Fast-Path HTTP
            fast_result = await self._try_fast_http(url)
            if fast_result.get("success"):
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                fast_result["elapsed_ms"] = round(elapsed_ms, 2)
                return fast_result


        # Fallback to in-loop browser engine
        if not self.browser._engine and not getattr(self.browser, "mock_mode", False):
            await self.browser.start()
        browser_res = await self.browser.navigate_and_settle(url)
        browser_res["engine"] = "milli_optical_browser"
        return browser_res

    async def _try_fast_http(self, url: str, timeout: float = 3.5) -> Dict[str, Any]:
        """Fast HTTP fetcher with anti-bot headers and SPA detection."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        loop = asyncio.get_running_loop()

        def _sync_fetch():
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                html = resp.read().decode("utf-8", errors="ignore")
                return status, html

        try:
            status, html = await loop.run_in_executor(None, _sync_fetch)

            # Check if this is an empty SPA shell requiring JS rendering
            if self._is_dynamic_spa(html):
                return {"success": False, "reason": "dynamic_spa_detected"}

            # Check for Cloudflare / anti-bot interstitial
            if "just a moment" in html.lower() or "cf-turnstile" in html.lower() or status in (403, 503):
                return {"success": False, "reason": "challenge_detected"}

            return {
                "success": True,
                "engine": "fast_http",
                "status": status,
                "url": url,
                "html": html,
                "title": self._extract_title(html)
            }
        except Exception as e:
            return {"success": False, "reason": str(e)}

    def _is_dynamic_spa(self, html: str) -> bool:
        """Detects if an HTML page is a blank hydration shell (React/Next/Vue/Angular)."""
        lower = html.lower()
        # If body is tiny or contains standard empty root containers
        if len(html) < 800 and ('<div id="root"></div>' in lower or '<div id="app"></div>' in lower or '<app-root></app-root>' in lower):
            return True
        return False

    def _extract_title(self, html: str) -> str:
        """Extracts <title> text."""
        import re
        m = re.search(r"<title\b[^>]*>(.*?)<\/title>", html, flags=re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ""
