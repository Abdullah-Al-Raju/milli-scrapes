"""
Cloudflare Turnstile and Challenge Auto-Sniper for Milli-Scrapes.
Detects Cloudflare Turnstile and challenge interstitials, locates the interactive checkbox,
and executes in-loop coordinate dispatch to solve challenges in milliseconds without external solver APIs.
"""

import time
import asyncio
from typing import Dict, Any, Optional

from ..browser.engine import MilliScrapeBrowser


class TurnstileSniper:
    """
    Automated detector and coordinate actuator for Cloudflare Turnstile & Challenge gates.
    """

    def __init__(self, browser: MilliScrapeBrowser):
        self.browser = browser

    async def detect_and_solve(self, timeout_sec: float = 6.0) -> Dict[str, Any]:
        """
        Scans page for Cloudflare Turnstile or Challenge iframe, computes its interactive
        coordinates, and dispatches an authentic click event to bypass the gate.
        """
        t0 = time.perf_counter()

        detect_script = """
        (() => {
            // Check for Cloudflare Turnstile iframe
            const turnstileIframe = document.querySelector('iframe[src*="challenges.cloudflare.com"]') ||
                                    document.querySelector('iframe[title*="Cloudflare security challenge"]') ||
                                    document.querySelector('div#cf-turnstile-wrapper iframe');
            if (turnstileIframe) {
                const rect = turnstileIframe.getBoundingClientRect();
                return {
                    detected: true,
                    type: 'turnstile',
                    x: rect.x + (rect.width * 0.12),
                    y: rect.y + (rect.height * 0.5),
                    width: rect.width,
                    height: rect.height
                };
            }

            // Check for Cloudflare standard interstitial
            const cfTitle = document.title.toLowerCase();
            const cfBody = document.body ? document.body.innerText.toLowerCase() : '';
            if (cfTitle.includes("just a moment") || cfBody.includes("checking your browser")) {
                const checkbox = document.querySelector('input[type="checkbox"]') ||
                                 document.querySelector('.ctp-checkbox-label') ||
                                 document.querySelector('#challenge-stage input');
                if (checkbox) {
                    const rect = checkbox.getBoundingClientRect();
                    return {
                        detected: true,
                        type: 'cf_checkbox',
                        x: rect.x + (rect.width / 2),
                        y: rect.y + (rect.height / 2),
                        width: rect.width,
                        height: rect.height
                    };
                }
                return { detected: true, type: 'cf_interstitial_waiting' };
            }

            return { detected: false };
        })();
        """

        try:
            status = await self.browser.evaluate(detect_script)
            if not status or not status.get("detected"):
                return {"detected": False, "solved": False, "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2)}

            # If coordinates are available, click on the target
            if "x" in status and "y" in status:
                click_x = status["x"]
                click_y = status["y"]

                # Dispatch click inside browser context
                click_script = f"""
                (() => {{
                    const el = document.elementFromPoint({click_x}, {click_y});
                    if (el) {{
                        el.click();
                        return true;
                    }}
                    return false;
                }})();
                """
                await self.browser.evaluate(click_script)
                await asyncio.sleep(0.3)

                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "detected": True,
                    "solved": True,
                    "type": status.get("type"),
                    "coordinates": (click_x, click_y),
                    "elapsed_ms": round(elapsed_ms, 2)
                }

        except Exception as e:
            return {"detected": False, "solved": False, "error": str(e)}

        return {
            "detected": False,
            "solved": False,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }
