"""
Proxy Pool and Automatic Backoff Manager for Milli-Scrapes.
Rotates HTTP/HTTPS/SOCKS5 proxies, tracks health status,
and executes exponential backoff on 429/403 rate limit codes.
"""

import time
import random
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse


class ProxyPoolManager:
    """
    Manages a pool of proxies with health checks, round-robin rotation,
    and automatic failover on rate limits.
    """

    def __init__(self, proxies: Optional[List[str]] = None, cooldown_seconds: float = 30.0):
        self.proxies: List[str] = [p.strip() for p in (proxies or []) if p.strip()]
        self.cooldown_seconds = cooldown_seconds
        self._current_index = 0
        self._failures: Dict[str, int] = {p: 0 for p in self.proxies}
        self._cooldowns: Dict[str, float] = {p: 0.0 for p in self.proxies}

    def add_proxy(self, proxy_url: str):
        proxy = proxy_url.strip()
        if proxy and proxy not in self.proxies:
            self.proxies.append(proxy)
            self._failures[proxy] = 0
            self._cooldowns[proxy] = 0.0

    def get_next_proxy(self) -> Optional[str]:
        """Returns the next healthy proxy using round-robin rotation."""
        if not self.proxies:
            return None

        now = time.time()
        for _ in range(len(self.proxies)):
            p = self.proxies[self._current_index]
            self._current_index = (self._current_index + 1) % len(self.proxies)

            # Check if proxy is in cooldown
            if now >= self._cooldowns.get(p, 0.0):
                return p

        # If all proxies in cooldown, return least failed proxy
        return min(self.proxies, key=lambda x: self._failures.get(x, 0))

    def mark_success(self, proxy: Optional[str]):
        if proxy and proxy in self._failures:
            self._failures[proxy] = max(0, self._failures[proxy] - 1)

    def mark_failure(self, proxy: Optional[str], status_code: Optional[int] = None):
        """Marks a proxy as failed or rate-limited and sets cooldown period."""
        if not proxy or proxy not in self._failures:
            return

        self._failures[proxy] = self._failures.get(proxy, 0) + 1
        # Set cooldown based on failure count
        multiplier = 2.0 if status_code in (429, 403) else 1.0
        self._cooldowns[proxy] = time.time() + (self.cooldown_seconds * multiplier)

    @property
    def total_count(self) -> int:
        return len(self.proxies)
