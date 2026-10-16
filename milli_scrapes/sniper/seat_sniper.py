"""
Reflex Seat Sniper for High-Demand Bookings.
Interception engine that strikes available seats and slots in under 15 milliseconds.
Supports both Canvas/SVG optical color detection and in-loop CDP DOM events.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
import numpy as np

from ..browser.engine import MilliScrapeBrowser
from ..optical.saliency import SeatSaliencyDetector

try:
    from milli_agent.platform import get_platform_driver
    from milli_agent.controller.input import OSInputController
except ImportError:
    get_platform_driver = None
    OSInputController = None


class ReflexSeatSniper:
    """
    Sub-15ms reflex seat and slot booking actuator.
    """

    def __init__(
        self,
        browser: Optional[MilliScrapeBrowser] = None,
        target_rgb: Tuple[int, int, int] = (46, 204, 113),
        dry_run: bool = False
    ):
        self.browser = browser or MilliScrapeBrowser()
        self.detector = SeatSaliencyDetector(target_rgb=target_rgb)
        self.dry_run = dry_run

        self.platform = get_platform_driver() if get_platform_driver else None
        self.controller = OSInputController(dry_run=dry_run, driver=self.platform) if (OSInputController and self.platform) else None

    async def snipe_optical_seat(
        self,
        confirm_selector: Optional[str] = "#book-now-btn",
        max_scan_seconds: float = 10.0
    ) -> Dict[str, Any]:
        """
        Continuously scans live framebuffer in RAM for available green seat centroids.
        The microsecond a seat turns green, warps and clicks at (cx, cy) and triggers confirmation.
        """
        t0 = time.perf_counter()
        seat_clicked = False
        target_coords = None

        while (time.perf_counter() - t0) < max_scan_seconds:
            t_frame0 = time.perf_counter()
            frame = await self.browser.capture_frame_ram()
            seats = self.detector.find_available_seats(frame)

            if seats:
                # Target first available seat
                seat = seats[0]
                target_coords = (seat["screen_x"], seat["screen_y"])
                react_latency_ms = (time.perf_counter() - t_frame0) * 1000.0

                # Microsecond native hardware click or CDP click
                if self.controller and not self.dry_run:
                    self.controller.click(target_coords[0], target_coords[1])
                seat_clicked = True

                # Immediate confirmation trigger
                if confirm_selector:
                    await self.browser.cy_click(confirm_selector)

                total_ttf_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "status": "booked",
                    "mode": "optical_canvas",
                    "target_coords": target_coords,
                    "reaction_latency_ms": round(react_latency_ms, 3),
                    "time_to_finish_ms": round(total_ttf_ms, 2),
                    "confidence": seat.get("confidence", 0.99)
                }

            await asyncio.sleep(0.016)  # ~60 Hz scan

        return {
            "status": "timeout",
            "mode": "optical_canvas",
            "message": f"No available seat opened within {max_scan_seconds}s"
        }

    async def snipe_dom_seat(
        self,
        seat_selector: str = ".seat-available",
        confirm_selector: str = "#confirm-booking"
    ) -> Dict[str, Any]:
        """
        In-loop DOM seat reservation.
        Dispatches click the instant candidate node appears without arbitrary sleep.
        """
        t0 = time.perf_counter()
        t_click0 = time.perf_counter()

        await self.browser.cy_click(seat_selector)
        react_latency_ms = (time.perf_counter() - t_click0) * 1000.0

        if confirm_selector:
            await self.browser.cy_click(confirm_selector)

        total_ttf_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "booked",
            "mode": "dom_in_loop",
            "seat_selector": seat_selector,
            "reaction_latency_ms": round(react_latency_ms, 3),
            "time_to_finish_ms": round(total_ttf_ms, 2)
        }
