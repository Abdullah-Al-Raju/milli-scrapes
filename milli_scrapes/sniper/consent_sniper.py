"""
Visual & DOM Consent / Cookie Banner Auto-Sniper for Milli-Scrapes.
Interceps and dismisses blocking cookie dialogs, OneTrust, Didomi,
and overlay modals in under 15 milliseconds prior to content extraction.
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup

from ..browser.engine import MilliScrapeBrowser


# Standard CSS selectors for major consent banners across the web
COMMON_CONSENT_SELECTORS = [
    "#onetrust-accept-btn-handler",
    ".onetrust-close-btn-handler",
    "#didomi-notice-agree-button",
    ".cc-btn.cc-allow",
    ".cookie-banner__accept",
    "#cookie-accept-all",
    "button[data-testid='cookie-policy-manage-dialog-accept-button']",
    "button[aria-label='Accept all']",
    "button[aria-label='Accept all cookies']",
    ".js-cookie-consent-accept",
    "#accept-recommended-btn",
    "button.accept-cookies-button"
]


class ConsentSniper:
    """
    Sub-15ms consent and overlay dismissal actuator.
    """

    def __init__(self, browser: MilliScrapeBrowser):
        self.browser = browser

    async def auto_dismiss_consent(self, timeout_ms: float = 30.0) -> Dict[str, Any]:
        """
        Scans and clicks cookie acceptance / dismiss buttons in-loop.
        Returns execution latency and status.
        """
        t0 = time.perf_counter()

        # Fast in-loop evaluation script to find and click the first matching consent button
        click_script = """
        (() => {
            const selectors = [
                '#onetrust-accept-btn-handler',
                '#didomi-notice-agree-button',
                '.cc-btn.cc-allow',
                '#cookie-accept-all',
                'button[aria-label*="Accept"]',
                'button[id*="accept"]',
                'button[class*="accept"]',
                'a[id*="accept"]'
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.offsetParent !== null) {
                    el.click();
                    return sel;
                }
            }
            return null;
        })();
        """

        try:
            clicked_selector = await self.browser.evaluate(click_script)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            if clicked_selector:
                return {
                    "dismissed": True,
                    "selector": clicked_selector,
                    "elapsed_ms": round(elapsed_ms, 2)
                }
        except Exception:
            pass

        return {
            "dismissed": False,
            "selector": None,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }
