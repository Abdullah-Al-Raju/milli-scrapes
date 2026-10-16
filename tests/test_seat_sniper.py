"""
Unit tests for ReflexSeatSniper.
"""

import unittest
import asyncio
import numpy as np
from milli_scrapes.browser.engine import MilliScrapeBrowser
from milli_scrapes.sniper.seat_sniper import ReflexSeatSniper


class TestSeatSniper(unittest.IsolatedAsyncioTestCase):

    async def test_dom_seat_sniping(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        sniper = ReflexSeatSniper(browser=browser, dry_run=True)

        res = await sniper.snipe_dom_seat(
            seat_selector="#seat-a1",
            confirm_selector="#confirm-btn"
        )

        self.assertEqual(res["status"], "booked")
        self.assertEqual(res["mode"], "dom_in_loop")
        self.assertGreater(res["time_to_finish_ms"], 0.0)

    async def test_optical_seat_sniping(self):
        browser = MilliScrapeBrowser(mock_mode=True)
        sniper = ReflexSeatSniper(browser=browser, dry_run=True)

        # Inject synthetic frame with 1 green seat into browser
        green_frame = np.ones((768, 1366, 3), dtype=np.uint8) * 40
        green_frame[200:230, 400:430, 0] = 46
        green_frame[200:230, 400:430, 1] = 204
        green_frame[200:230, 400:430, 2] = 113

        async def _mock_frame():
            return green_frame

        browser.capture_frame_ram = _mock_frame

        res = await sniper.snipe_optical_seat(confirm_selector="#book-btn", max_scan_seconds=1.0)
        self.assertEqual(res["status"], "booked")
        self.assertEqual(res["mode"], "optical_canvas")
        self.assertIsNotNone(res["target_coords"])
        self.assertTrue(390 <= res["target_coords"][0] <= 440)
        self.assertTrue(190 <= res["target_coords"][1] <= 240)


if __name__ == "__main__":
    unittest.main()
