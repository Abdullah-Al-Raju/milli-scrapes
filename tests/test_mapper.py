"""
Unit tests for MilliMapper.
"""

import unittest
from unittest.mock import patch, MagicMock
from milli_scrapes.crawler.mapper import MilliMapper


class TestMilliMapper(unittest.TestCase):

    @patch("milli_scrapes.crawler.sitemap.SitemapCrawler.discover_sitemaps_from_robots")
    @patch("milli_scrapes.crawler.sitemap.SitemapCrawler.fetch_and_parse")
    def test_domain_mapper_with_mock_sitemap(self, mock_fetch, mock_robots):
        mock_robots.return_value = ["https://example.com/sitemap.xml"]
        mock_fetch.return_value = [
            "https://example.com/docs/intro",
            "https://example.com/docs/api",
            "https://example.com/blog/v1",
            "https://example.com/pricing"
        ]

        res = MilliMapper.map_domain("https://example.com", max_urls=10)

        self.assertEqual(res["domain"], "example.com")
        self.assertEqual(res["total_urls"], 4)
        self.assertIn("https://example.com/docs/intro", res["urls"])
        self.assertEqual(res["paths_summary"].get("/docs"), 2)
        self.assertEqual(res["paths_summary"].get("/blog"), 1)
        self.assertEqual(res["paths_summary"].get("/pricing"), 1)
        self.assertGreaterEqual(res["elapsed_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
