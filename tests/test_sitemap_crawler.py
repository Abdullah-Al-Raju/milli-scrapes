import unittest
from milli_scrapes.crawler.sitemap import SitemapCrawler


class TestSitemapCrawler(unittest.TestCase):

    def test_extract_urls_from_xml(self):
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
          <url>
            <loc>https://example.com/page1</loc>
            <lastmod>2026-01-01</lastmod>
          </url>
          <url>
            <loc>https://example.com/page2</loc>
          </url>
        </urlset>
        """
        urls = SitemapCrawler.extract_urls_from_xml(sample_xml)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://example.com/page1", urls)
        self.assertIn("https://example.com/page2", urls)

    def test_extract_urls_fallback(self):
        malformed_xml = "<loc>https://test.org/itemA</loc> Some other text <loc>https://test.org/itemB</loc>"
        urls = SitemapCrawler.extract_urls_from_xml(malformed_xml)
        self.assertEqual(len(urls), 2)
        self.assertIn("https://test.org/itemA", urls)


if __name__ == "__main__":
    unittest.main()
