import unittest
from milli_scrapes.sniper.consent_sniper import ConsentSniper
from milli_scrapes.browser.engine import MilliScrapeBrowser


class TestConsentSniper(unittest.IsolatedAsyncioTestCase):

    async def test_consent_auto_dismiss(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        sniper = ConsentSniper(browser)
        res = await sniper.auto_dismiss_consent()
        self.assertIn("dismissed", res)
        self.assertIn("elapsed_ms", res)
        self.assertLess(res["elapsed_ms"], 50.0)


if __name__ == "__main__":
    unittest.main()
