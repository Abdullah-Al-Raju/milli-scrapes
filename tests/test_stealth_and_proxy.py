import unittest
from milli_scrapes.browser.stealth import StealthManager
from milli_scrapes.browser.proxy import ProxyPoolManager


class TestStealthAndProxy(unittest.TestCase):

    def test_stealth_script_integrity(self):
        script = StealthManager.get_stealth_script()
        self.assertIn("navigator, 'webdriver'", script)
        self.assertIn("Intel Inc.", script)
        self.assertIn("chrome.runtime", script)

    def test_proxy_pool_rotation_and_cooldown(self):
        pool = ProxyPoolManager(["http://proxy1:8080", "http://proxy2:8080"])
        self.assertEqual(pool.total_count, 2)

        p1 = pool.get_next_proxy()
        p2 = pool.get_next_proxy()
        self.assertNotEqual(p1, p2)

        # Mark p1 as failed with 429 rate limit
        pool.mark_failure(p1, status_code=429)
        # Next should avoid p1 and pick p2
        self.assertEqual(pool.get_next_proxy(), p2)


if __name__ == "__main__":
    unittest.main()
