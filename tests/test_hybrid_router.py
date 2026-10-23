"""
Unit tests for HybridScrapeRouter.
"""

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from milli_scrapes.scraper.hybrid_router import HybridScrapeRouter


class TestHybridScrapeRouter(unittest.TestCase):

    @patch("milli_scrapes.scraper.hybrid_router.HybridScrapeRouter._try_fast_http")
    def test_fast_path_routing(self, mock_fast_http):
        mock_fast_http.return_value = {
            "success": True,
            "engine": "fast_http",
            "status": 200,
            "url": "https://example.com/docs",
            "html": "<html><title>Docs</title><body><p>Static Content</p></body></html>",
            "title": "Docs"
        }

        router = HybridScrapeRouter(prefer_fast_path=True)
        import asyncio
        res = asyncio.run(router.fetch_page("https://example.com/docs"))

        self.assertEqual(res["engine"], "fast_http")
        self.assertEqual(res["status"], 200)
        self.assertEqual(res["title"], "Docs")

    @patch("milli_scrapes.scraper.hybrid_router.HybridScrapeRouter._try_fast_http")
    def test_spa_fallback_to_browser(self, mock_fast_http):
        mock_fast_http.return_value = {"success": False, "reason": "dynamic_spa_detected"}

        mock_browser = MagicMock()
        mock_browser.navigate_and_settle = AsyncMock(return_value={
            "status": 200,
            "url": "https://example.com/app",
            "html": "<html><body>Rendered SPA</body></html>",
            "title": "SPA App"
        })

        router = HybridScrapeRouter(browser=mock_browser, prefer_fast_path=True)
        import asyncio
        res = asyncio.run(router.fetch_page("https://example.com/app"))

        self.assertEqual(res["engine"], "milli_optical_browser")
        self.assertIn("Rendered SPA", res["html"])


if __name__ == "__main__":
    unittest.main()
