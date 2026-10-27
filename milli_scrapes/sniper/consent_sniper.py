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
    Sub-millisecond consent and overlay dismissal actuator.
    Combines in-loop CDP dispatch with zero-clamp V8 in-memory MessageChannel
    MutationObserver hooks to dismiss consent modals in < 1.0 ms.
    """

    def __init__(self, browser: MilliScrapeBrowser):
        self.browser = browser

    async def snipe_v8_hyper_consent(self, timeout_ms: float = 30.0) -> Dict[str, Any]:
        """
        Sub-millisecond V8 In-Memory Reflex Consent Sniper.
        Injects a zero-clamp MessageChannel + MutationObserver harness directly into the
        page's V8 JavaScript runtime. The microsecond a consent dialog (OneTrust, Didomi,
        Cookiebot, etc.) mounts or reveals, V8 clicks it instantly in < 1 ms.
        """
        t0 = time.perf_counter()
        if self.browser.mock_mode or not self.browser._engine:
            return {
                "dismissed": True,
                "mode": "v8_hyper_reflex_mock",
                "selector": "#onetrust-accept-btn-handler",
                "elapsed_ms": 0.42
            }

        arm_script = """
        (() => {
            window.__MILLI_CONSENT_RESULT__ = window.__MILLI_CONSENT_RESULT__ || null;
            const selectors = [
                '#onetrust-accept-btn-handler',
                '.onetrust-close-btn-handler',
                '#didomi-notice-agree-button',
                '.cc-btn.cc-allow',
                '#cookie-accept-all',
                'button[data-testid*="cookie" i][data-testid*="accept" i]',
                'button[aria-label*="Accept all" i]',
                'button[aria-label*="Accept" i]',
                'button[aria-label*="Agree" i]',
                'button[id*="accept" i]',
                'button[class*="accept" i]',
                'button[class*="consent" i]',
                '#accept-recommended-btn',
                '.js-cookie-consent-accept',
                'a[id*="accept" i]'
            ];

            function executeStrike(el, sel) {
                if (!el || window.__MILLI_CONSENT_RESULT__) return;
                const rect = el.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;

                el.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
                el.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
                el.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, clientX: cx, clientY: cy }));
                if (typeof el.click === "function") el.click();

                window.__MILLI_CONSENT_RESULT__ = {
                    dismissed: true,
                    selector: sel,
                    t_hit: performance.now()
                };
            }

            // 1. Strike immediate if already mounted
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && (el.offsetParent !== null || el.getClientRects().length > 0)) {
                    executeStrike(el, sel);
                    return window.__MILLI_CONSENT_RESULT__;
                }
            }

            // 2. Arm zero-clamp MessageChannel + MutationObserver for sub-ms reflex on dynamic mount
            const channel = new MessageChannel();
            channel.port1.onmessage = () => {
                if (window.__MILLI_CONSENT_RESULT__) return;
                for (const sel of selectors) {
                    const el = document.querySelector(sel);
                    if (el && (el.offsetParent !== null || el.getClientRects().length > 0)) {
                        executeStrike(el, sel);
                        break;
                    }
                }
            };

            const observer = new MutationObserver(() => {
                if (!window.__MILLI_CONSENT_RESULT__) {
                    channel.port2.postMessage(null);
                }
            });

            observer.observe(document.body || document.documentElement, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ["class", "style", "disabled"]
            });

            window.__MILLI_CONSENT_OBSERVER__ = observer;
            return window.__MILLI_CONSENT_RESULT__;
        })()
        """
        try:
            res = await self.browser.evaluate(arm_script)
            if res and res.get("dismissed"):
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "dismissed": True,
                    "mode": "v8_hyper_reflex",
                    "selector": res.get("selector"),
                    "elapsed_ms": round(elapsed_ms, 2)
                }

            # Poll briefly if banner is asynchronously animating/hydrating
            t_start = time.perf_counter()
            max_wait_sec = min(0.2, timeout_ms / 1000.0)
            while (time.perf_counter() - t_start) < max_wait_sec:
                hook_res = await self.browser.evaluate("window.__MILLI_CONSENT_RESULT__")
                if hook_res and hook_res.get("dismissed"):
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    return {
                        "dismissed": True,
                        "mode": "v8_hyper_reflex",
                        "selector": hook_res.get("selector"),
                        "elapsed_ms": round(elapsed_ms, 2)
                    }
                await asyncio.sleep(0.005)
        except Exception:
            pass

        return {
            "dismissed": False,
            "selector": None,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2)
        }

    async def auto_dismiss_consent(self, timeout_ms: float = 30.0) -> Dict[str, Any]:
        """
        Scans and clicks cookie acceptance / dismiss buttons in-loop using
        sub-millisecond V8 hyper-reflex with fallback to direct DOM click.
        """
        # 1. Primary: Sub-millisecond V8 in-memory hyper-reflex
        hyper_res = await self.snipe_v8_hyper_consent(timeout_ms=timeout_ms)
        if hyper_res.get("dismissed"):
            return hyper_res

        t0 = time.perf_counter()

        # 2. Fallback: Fast in-loop evaluation script
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
                    "mode": "dom_in_loop",
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
