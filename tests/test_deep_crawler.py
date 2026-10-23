"""
Unit tests for MilliCrawler.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock
from milli_scrapes.crawler.deep_crawler import MilliCrawler


class TestMilliCrawler(unittest.TestCase):

    async def async_test_crawl_flow(self):
        mock_router = MagicMock()
        mock_router.fetch_page = AsyncMock(side_effect=[
            {
                "status": 200,
                "url": "https://example.com",
                "html": """
                <html>
                    <head><title>Home</title></head>
                    <body>
                        <h1>Home Page</h1>
                        <a href="/docs/intro">Docs</a>
                        <a href="/blog/news">News</a>
                        <a href="/admin/login">Admin</a>
                    </body>
                </html>
                """,
                "engine": "fast_http",
                "elapsed_ms": 15.0
            },
            {
                "status": 200,
                "url": "https://example.com/docs/intro",
                "html": "<html><title>Docs Intro</title><body><h1>Introduction</h1></body></html>",
                "engine": "fast_http",
                "elapsed_ms": 12.0
            }
        ])

        crawler = MilliCrawler(router=mock_router, concurrency=2)
        res = await crawler.crawl(
            start_url="https://example.com",
            max_pages=2,
            max_depth=2,
            include_paths=["/docs/*"],
            exclude_paths=["/admin/*"]
        )

        self.assertEqual(res["total_crawled"], 2)
        self.assertEqual(res["root_url"], "https://example.com")
        urls = [p["url"] for p in res["pages"]]
        self.assertIn("https://example.com", urls)
        self.assertIn("https://example.com/docs/intro", urls)
        self.assertNotIn("https://example.com/admin/login", urls)

    def test_crawl(self):
        import asyncio
        asyncio.run(self.async_test_crawl_flow())


if __name__ == "__main__":
    unittest.main()
