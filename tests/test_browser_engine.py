"""
Unit tests for MilliScrapeBrowser.
"""

import unittest
import asyncio
from milli_scrapes.browser.engine import MilliScrapeBrowser


class TestBrowserEngine(unittest.IsolatedAsyncioTestCase):

    async def test_mock_browser_lifecycle_and_scraping(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        await browser.start()

        try:
            res = await browser.navigate_and_settle("https://example.com")
            self.assertEqual(res["status"], 200)
            self.assertIn("Milli-Scrapes", res["html"])
            self.assertGreaterEqual(res["elapsed_ms"], 0.0)

            # Frame capture in RAM
            frame = await browser.capture_frame_ram()
            self.assertEqual(frame.shape, (768, 1366, 3))

            # State query
            state = await browser.get_interactive_state()
            self.assertIn("elements", state)

            # In-loop event dispatch
            clicked = await browser.cy_click("#seat-a1")
            self.assertTrue(clicked)

            typed = await browser.cy_type("Query")
            self.assertTrue(typed)

        finally:
            await browser.aclose()


if __name__ == "__main__":
    unittest.main()
