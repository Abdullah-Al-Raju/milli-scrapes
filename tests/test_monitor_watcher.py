"""
Unit tests for WebsiteWatcher.
"""

import unittest
from milli_scrapes.browser.engine import MilliScrapeBrowser
from milli_scrapes.monitor.watcher import WebsiteWatcher
from milli_scrapes.notifier.email import EmailNotifier


class TestWebsiteWatcher(unittest.IsolatedAsyncioTestCase):

    async def test_watcher_check_cycle(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        notifier = EmailNotifier(dry_run=True)
        watcher = WebsiteWatcher(
            url="https://example.com/status",
            browser=browser,
            notifier=notifier,
            check_interval_seconds=0.1
        )

        # First cycle establishes baseline
        res1 = await watcher.check_once(optical_mode=False)
        self.assertEqual(res1["status"], "baseline_established")
        self.assertFalse(res1["has_changed"])

        # Change mock page
        browser._mock_html = "<html><body><h1>Updated Status: Seats Available!</h1></body></html>"

        # Second cycle detects change
        res2 = await watcher.check_once(optical_mode=False)
        self.assertTrue(res2["has_changed"])
        self.assertEqual(res2["type"], "dom_text_change")
        self.assertEqual(res2["email_status"], "simulated")


if __name__ == "__main__":
    unittest.main()
