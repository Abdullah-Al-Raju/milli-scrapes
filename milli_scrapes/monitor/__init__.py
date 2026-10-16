"""
Milli-Scrapes Website Monitoring Subsystem.
Tracks visual and DOM changes in high-frequency observation loops.
"""

from .watcher import WebsiteWatcher

__all__ = ["WebsiteWatcher"]
