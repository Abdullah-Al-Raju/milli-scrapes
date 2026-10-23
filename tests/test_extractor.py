"""
Unit tests for HTMLToMarkdownExtractor and StructuredDataExtractor.
"""

import unittest
from milli_scrapes.extractor.markdown import HTMLToMarkdownExtractor
from milli_scrapes.extractor.structured import StructuredDataExtractor


class TestExtractors(unittest.TestCase):

    def test_markdown_extractor(self):
        html = """
        <html>
            <head><title>Test Page</title><style>.bad{color:red;}</style></head>
            <body>
                <nav><a href="/home">Home</a></nav>
                <h1>Flight Booking Portal</h1>
                <p>Welcome to <strong>Milli-Scrapes</strong>. Fastest scraper on the planet.</p>
                <ul>
                    <li>London to Tokyo - <a href="/book/1">Book Now</a></li>
                    <li>New York to Paris - <a href="/book/2">Book Now</a></li>
                </ul>
                <script>console.log("tracker");</script>
                <footer>Copyright 2026</footer>
            </body>
        </html>
        """
        extractor = HTMLToMarkdownExtractor(strip_nav_footer=True)
        md = extractor.extract(html)

        self.assertIn("# Flight Booking Portal", md)
        self.assertIn("**Milli-Scrapes**", md)
        self.assertIn("[Book Now](/book/1)", md)
        self.assertNotIn("console.log", md)
        self.assertNotIn("Copyright 2026", md)

    def test_structured_table_extractor(self):
        html = """
        <table>
            <tr><th>Flight</th><th>Price</th><th>Seats</th></tr>
            <tr><td>BA001</td><td>$450</td><td>2 left</td></tr>
            <tr><td>JL002</td><td>$620</td><td>Available</td></tr>
        </table>
        """
        extractor = StructuredDataExtractor()
        tables = extractor.extract_tables(html)

        self.assertEqual(len(tables), 1)
        rows = tables[0]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Flight"], "BA001")
        self.assertEqual(rows[0]["Price"], "$450")
        self.assertEqual(rows[1]["Seats"], "Available")

    def test_key_values_extractor(self):
        html = "<div>Flight Status: Confirmed</div><div>Gate: B12</div>"
        extractor = StructuredDataExtractor()
        kvs = extractor.extract_key_values(html)
        self.assertEqual(kvs.get("Flight Status"), "Confirmed")
        self.assertEqual(kvs.get("Gate"), "B12")

    def test_markdown_table_conversion(self):
        html = """
        <html>
            <body>
                <h1>Pricing Matrix</h1>
                <table>
                    <tr><th>Plan</th><th>Price</th><th>Limit</th></tr>
                    <tr><td>Basic</td><td>$10/mo</td><td>10k req</td></tr>
                    <tr><td>Pro</td><td>$50/mo</td><td>100k req</td></tr>
                </table>
            </body>
        </html>
        """
        extractor = HTMLToMarkdownExtractor()
        md = extractor.extract(html)
        self.assertIn("| Plan | Price | Limit |", md)
        self.assertIn("| --- | --- | --- |", md)
        self.assertIn("| Basic | $10/mo | 10k req |", md)
        self.assertIn("| Pro | $50/mo | 100k req |", md)

    def test_metadata_and_clutter_stripping(self):
        html = """
        <html>
            <head>
                <title>Awesome Docs</title>
                <meta name="description" content="Official documentation for developers.">
                <meta property="og:image" content="https://example.com/cover.png">
                <link rel="canonical" href="https://example.com/docs">
            </head>
            <body>
                <div class="cookie-banner-modal">Please accept all cookies!</div>
                <div class="advertisement-slot">Buy our product!</div>
                <p>Welcome to our developer docs.</p>
            </body>
        </html>
        """
        extractor = HTMLToMarkdownExtractor()
        md, meta = extractor.extract_with_metadata(html)
        self.assertEqual(meta.get("title"), "Awesome Docs")
        self.assertEqual(meta.get("description"), "Official documentation for developers.")
        self.assertEqual(meta.get("image"), "https://example.com/cover.png")
        self.assertEqual(meta.get("canonical"), "https://example.com/docs")
        self.assertNotIn("Please accept all cookies", md)
        self.assertNotIn("Buy our product", md)
        self.assertIn("Welcome to our developer docs.", md)


if __name__ == "__main__":
    unittest.main()

