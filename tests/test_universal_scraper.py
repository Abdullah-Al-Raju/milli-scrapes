import unittest
import asyncio
from milli_scrapes.scraper.universal import UniversalScraper
from milli_scrapes.browser.engine import MilliScrapeBrowser


class TestUniversalScraper(unittest.IsolatedAsyncioTestCase):

    async def test_universal_scraper_arbitrary_url(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        browser._mock_html = """
        <html>
          <head><title>Sample Universal Page</title></head>
          <body>
            <h1>Welcome to Universal Scraper</h1>
            <p>Contact the team at hello@example.com or support@milli.org or call 555-019-2831.</p>
            <div class="product">
              <span class="title">Turbo Widget</span>
              <span class="price">$49.99</span>
            </div>
            <a href="https://example.com/about">About Us</a>
          </body>
        </html>
        """
        scraper = UniversalScraper(browser=browser)
        res = await scraper.scrape_url("https://example.com", extract_schema={"widget": ".title", "cost": ".price"})

        self.assertEqual(res["status"], 200)
        self.assertIn("Welcome to Universal Scraper", res["markdown"])
        self.assertIn("hello@example.com", res["contacts"]["emails"])
        self.assertIn("support@milli.org", res["contacts"]["emails"])
        self.assertEqual(res["custom_data"]["widget"], "Turbo Widget")
        self.assertEqual(res["custom_data"]["cost"], "$49.99")

    async def test_universal_scraper_crawl(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        browser._mock_html = """
        <html>
          <body>
            <h1>Directory Root</h1>
            <a href="https://directory.org/page1">Page 1</a>
            <a href="https://directory.org/page2">Page 2</a>
            <p>Inquiries: info@directory.org</p>
          </body>
        </html>
        """
        scraper = UniversalScraper(browser=browser)
        crawl_results = await scraper.crawl("https://directory.org", max_pages=2)
        self.assertGreaterEqual(len(crawl_results), 1)
        self.assertEqual(crawl_results[0]["status"], 200)


    async def test_universal_scraper_chunking(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        browser._mock_html = """
        <html>
          <head><title>Docs Page</title></head>
          <body>
            <h1>Section One</h1>
            <p>This is the first section of the documentation.</p>
            <h2>Section Two</h2>
            <p>This is the second section detailing API endpoints.</p>
          </body>
        </html>
        """
        scraper = UniversalScraper(browser=browser)
        res = await scraper.scrape_url("https://example.com/docs", chunk=True)

        self.assertEqual(res["status"], 200)
        self.assertTrue(len(res["chunks"]) >= 2)
        self.assertEqual(res["chunks"][0]["breadcrumbs"], ["Section One"])

    async def test_universal_scraper_map(self):
        from unittest.mock import patch
        scraper = UniversalScraper()
        with patch("milli_scrapes.crawler.mapper.MilliMapper.map_domain") as mock_map:
            mock_map.return_value = {
                "domain": "example.com",
                "total_urls": 5,
                "urls": ["https://example.com/a", "https://example.com/b"]
            }
            res = await scraper.map("https://example.com")
            self.assertEqual(res["total_urls"], 5)
            self.assertEqual(res["domain"], "example.com")


if __name__ == "__main__":
    unittest.main()

