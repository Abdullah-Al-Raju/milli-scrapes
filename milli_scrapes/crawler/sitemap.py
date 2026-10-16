"""
High-Speed XML Sitemap Parser and Asynchronous Domain Crawler.
Extracts all URLs from sitemap.xml, robots.txt, and sitemap indexes in milliseconds.
Feeds discovered URL queues directly into Milli-Scrapes' UniversalScraper.
"""

import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import List, Optional
from urllib.parse import urljoin, urlparse


class SitemapCrawler:
    """
    Parses XML sitemaps and discovers all crawlable URLs for a domain.
    """

    @classmethod
    def discover_sitemaps_from_robots(cls, base_url: str, timeout: float = 5.0) -> List[str]:
        """Reads robots.txt to discover declared Sitemap locations."""
        robots_url = urljoin(base_url, "/robots.txt")
        sitemaps = []
        try:
            req = urllib.request.Request(robots_url, headers={"User-Agent": "Milli-Scrapes/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                for line in content.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sm = line.split(":", 1)[1].strip()
                        if sm:
                            sitemaps.append(sm)
        except Exception:
            pass

        if not sitemaps:
            sitemaps.append(urljoin(base_url, "/sitemap.xml"))
        return sitemaps

    @classmethod
    def extract_urls_from_xml(cls, xml_text: str) -> List[str]:
        """Extracts all <loc> elements from an XML sitemap or sitemap index."""
        urls = []
        try:
            # Strip namespaces for simpler parsing
            clean_xml = re.sub(r'xmlns="[^"]+"', '', xml_text, count=1)
            root = ET.fromstring(clean_xml)

            # Match <loc> tags in <url> or <sitemap> blocks
            for loc in root.findall(".//loc"):
                if loc.text and loc.text.strip():
                    urls.append(loc.text.strip())
        except Exception:
            # Fallback regex extraction if XML is malformed
            urls = re.findall(r'<loc>\s*(https?://[^\s<]+)\s*<\/loc>', xml_text, re.IGNORECASE)

        return urls

    @classmethod
    def fetch_and_parse(cls, sitemap_url: str, timeout: float = 6.0) -> List[str]:
        """Fetches a remote XML sitemap and returns all URLs."""
        try:
            req = urllib.request.Request(sitemap_url, headers={"User-Agent": "Milli-Scrapes/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                return cls.extract_urls_from_xml(text)
        except Exception:
            return []
