"""
High-Frequency Website Change Watcher.
Performs continuous monitoring with sub-second checks.
Detects DOM structural mutations, keyword arrivals, or optical visual diffs in RAM.
Dispatches real-time email alerts with in-memory image attachments.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
import numpy as np

from ..browser.engine import MilliScrapeBrowser
from ..extractor.markdown import HTMLToMarkdownExtractor
from ..optical.differ import OpticalDiffer
from ..notifier.email import EmailNotifier


class WebsiteWatcher:
    """
    Watches a target web page for optical or textual changes.
    """

    def __init__(
        self,
        url: str,
        browser: Optional[MilliScrapeBrowser] = None,
        notifier: Optional[EmailNotifier] = None,
        optical_differ: Optional[OpticalDiffer] = None,
        check_interval_seconds: float = 2.0
    ):
        self.url = url
        self.browser = browser or MilliScrapeBrowser()
        self.notifier = notifier or EmailNotifier()
        self.differ = optical_differ or OpticalDiffer()
        self.extractor = HTMLToMarkdownExtractor()
        self.check_interval_seconds = check_interval_seconds
        self.running = False

        self._last_markdown: Optional[str] = None
        self._last_frame: Optional[np.ndarray] = None
        self._change_count = 0

    async def check_once(self, optical_mode: bool = True) -> Dict[str, Any]:
        """
        Executes a single check cycle against the target URL.
        """
        res = await self.browser.navigate_and_settle(self.url)
        html = res.get("html", "")
        current_md = self.extractor.extract(html)
        current_frame = await self.browser.capture_frame_ram() if optical_mode else None

        detected_change = False
        change_info = {"url": self.url, "timestamp": time.time()}

        if self._last_markdown is None:
            # Baseline cycle
            self._last_markdown = current_md
            self._last_frame = current_frame
            return {"status": "baseline_established", "has_changed": False}

        # Check textual diff
        if current_md != self._last_markdown:
            detected_change = True
            change_info["type"] = "dom_text_change"
            change_info["prev_length"] = len(self._last_markdown)
            change_info["curr_length"] = len(current_md)

        # Check optical visual diff if enabled
        if optical_mode and current_frame is not None and self._last_frame is not None:
            diff_res = self.differ.compute_diff(self._last_frame, current_frame)
            if diff_res["has_changed"]:
                detected_change = True
                change_info["type"] = "optical_visual_change"
                change_info["change_percent"] = diff_res["change_percent"]
                change_info["bounding_box"] = diff_res["bounding_box"]
                change_info["diff_mask"] = diff_res["diff_mask"]

        if detected_change:
            self._change_count += 1
            self._last_markdown = current_md
            self._last_frame = current_frame

            # Render visual proof snapshot from RAM
            proof_bytes = None
            if current_frame is not None:
                mask = change_info.get("diff_mask")
                proof_bytes = self.differ.render_visual_proof_jpeg(current_frame, diff_mask=mask)

            # Fire email alert
            subject = f"Milli-Scrapes Alert: Detected Change on {self.url}"
            body_text = (
                f"Change detected on monitored site: {self.url}\n\n"
                f"Type: {change_info.get('type')}\n"
                f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Change Details: {change_info}\n"
            )
            email_res = self.notifier.send_alert(
                subject=subject,
                body_text=body_text,
                snapshot_jpeg=proof_bytes
            )
            change_info["email_status"] = email_res.get("status")

        change_info["has_changed"] = detected_change
        return change_info

    async def run_watch_loop(self, max_cycles: Optional[int] = None, optical_mode: bool = True):
        """
        Runs continuous monitoring loop.
        """
        self.running = True
        cycles = 0
        await self.browser.start()

        try:
            while self.running:
                res = await self.check_once(optical_mode=optical_mode)
                if res.get("has_changed"):
                    print(f"[WebsiteWatcher] Detected change! Alert dispatched.")
                cycles += 1
                if max_cycles and cycles >= max_cycles:
                    break
                await asyncio.sleep(self.check_interval_seconds)
        finally:
            await self.browser.aclose()
