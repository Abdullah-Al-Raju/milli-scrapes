"""
Optical Infinite Scroll Settling Engine for Milli-Scrapes.
Uses in-memory pixel delta comparison to detect when dynamic infinite feeds
have rendered and settled, eliminating guess-based arbitrary sleeps.
"""

import time
import asyncio
from typing import Dict, Any, Optional
import numpy as np

from ..browser.engine import MilliScrapeBrowser
from .differ import OpticalDiffer


class OpticalScrollSettler:
    """
    Drives infinite scroll while monitoring visual stability in RAM.
    """

    def __init__(self, browser: MilliScrapeBrowser, differ: Optional[OpticalDiffer] = None):
        self.browser = browser
        self.differ = differ or OpticalDiffer(pixel_delta_threshold=15, change_percent_trigger=0.1)

    async def scroll_and_settle(
        self,
        scroll_px: int = 800,
        max_wait_ms: float = 300.0,
        poll_interval_ms: float = 20.0
    ) -> Dict[str, Any]:
        """
        Scrolls down by `scroll_px` and loops until pixel changes settle below delta threshold.
        """
        t0 = time.perf_counter()

        # Capture pre-scroll frame
        prev_frame = await self.browser.capture_frame_ram()

        # Execute scroll
        scroll_script = f"window.scrollBy({{ top: {scroll_px}, behavior: 'instant' }});"
        await self.browser.evaluate(scroll_script)

        # Poll frame in RAM until changes settle
        settled = False
        cycles = 0
        poll_sec = poll_interval_ms / 1000.0
        max_sec = max_wait_ms / 1000.0

        while (time.perf_counter() - t0) < max_sec:
            await asyncio.sleep(poll_sec)
            cycles += 1
            curr_frame = await self.browser.capture_frame_ram()
            diff_res = self.differ.compute_diff(prev_frame, curr_frame)

            # If changed, update baseline; if delta drops below threshold, page has settled
            if diff_res["change_percent"] < self.differ.change_percent_trigger and cycles > 1:
                settled = True
                break
            prev_frame = curr_frame

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "settled": settled,
            "cycles": cycles,
            "elapsed_ms": round(elapsed_ms, 2)
        }
