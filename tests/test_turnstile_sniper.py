"""
Unit tests for TurnstileSniper.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock
from milli_scrapes.sniper.turnstile_sniper import TurnstileSniper


class TestTurnstileSniper(unittest.TestCase):

    async def async_test_turnstile_detection_and_solve(self):
        mock_browser = MagicMock()
        mock_browser.evaluate = AsyncMock(side_effect=[
            {"detected": True, "type": "turnstile", "x": 120.0, "y": 240.0, "width": 300, "height": 65},
            True
        ])

        sniper = TurnstileSniper(mock_browser)
        res = await sniper.detect_and_solve()

        self.assertTrue(res["detected"])
        self.assertTrue(res["solved"])
        self.assertEqual(res["type"], "turnstile")
        self.assertEqual(res["coordinates"], (120.0, 240.0))

    def test_turnstile_detection(self):
        import asyncio
        asyncio.run(self.async_test_turnstile_detection_and_solve())


if __name__ == "__main__":
    unittest.main()
