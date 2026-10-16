"""
Milli-Scrapes In-Loop Browser Subsystem.
Powered by WebSocket Chrome DevTools Protocol (CDP) with mutation-driven reactive settling.
"""

from .engine import MilliScrapeBrowser

__all__ = ["MilliScrapeBrowser"]
