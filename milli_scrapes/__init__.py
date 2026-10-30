"""
Milli-Scrapes: Ultra-Fast Visual Web Scraper, Change Monitor, and Reflex Seat Booking Engine.
Engineered for sub-15ms visual/DOM response loops, zero-sleep reactive settling,
and in-memory optical change detection without disk writes.
"""

__version__ = "0.1.0"
__author__ = "Abdullah-Al-Raju"

from .scraper.universal import UniversalScraper
from .extractor.pydantic_extractor import PydanticExtractor
from .sniper.consent_sniper import ConsentSniper
from .crawler.sitemap import SitemapCrawler
from .browser.proxy import ProxyPoolManager
from .browser.stealth import StealthManager
from .optical.scroll_differ import OpticalScrollSettler
from .decision import MilliDecisionEngine, Noul, Choice, Score
from .extractor.visual import MilliVisualVerifier, VisualCategory

__all__ = [
    "UniversalScraper",
    "PydanticExtractor",
    "ConsentSniper",
    "SitemapCrawler",
    "ProxyPoolManager",
    "StealthManager",
    "OpticalScrollSettler",
    "MilliDecisionEngine",
    "MilliVisualVerifier",
    "VisualCategory",
    "Noul",
    "Choice",
    "Score",
    "__version__",
    "__author__"
]
