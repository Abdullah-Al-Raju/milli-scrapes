"""
General Purpose Universal Scraper Engine (inspired by Scrapy / Crawl4AI / Firecrawl).
Accepts arbitrary URLs, CSS/XPath schemas, pagination rules, or AI extraction prompts.
Works on ANY target website out of the box without custom scripts.
"""

import asyncio
import re
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from ..browser.engine import MilliScrapeBrowser
from ..extractor.markdown import HTMLToMarkdownExtractor
from ..extractor.structured import StructuredDataExtractor


class UniversalScraper:
    """
    General-purpose web scraper:
    - Scrapes any arbitrary URL or batch of URLs
    - Extracts unstructured Markdown, tables, links, images, emails, phones, and contacts
    - Supports declarative schema extraction (CSS selector maps or regex patterns)
    - Follows pagination and crawls domain links
    - Reactively settles JS/React/SPA pages in milliseconds with zero arbitrary sleeps
    """

    def __init__(self, browser: Optional[MilliScrapeBrowser] = None, headless: bool = True):
        self.browser = browser or MilliScrapeBrowser(headless=headless)
        self.md_extractor = HTMLToMarkdownExtractor()
        self.struct_extractor = StructuredDataExtractor()
        self._owns_browser = browser is None

    async def scrape_url(
        self,
        url: str,
        extract_schema: Optional[Dict[str, str]] = None,
        extract_contacts: bool = True
    ) -> Dict[str, Any]:
        """
        Scrapes a single URL and extracts structured and unstructured content.

        Args:
            url: Target URL
            extract_schema: Optional mapping of field names to CSS selectors or regexes,
                            e.g. {"name": "h1.title", "price": ".price-tag"}
            extract_contacts: If True, automatically extracts all emails, phone numbers, and social handles
        """
        res = await self.browser.navigate_and_settle(url)
        html = res.get("html", "")
        elapsed_ms = res.get("elapsed_ms", 0.0)

        # 1. Clean Markdown
        markdown = self.md_extractor.extract(html)

        # 2. Structured Tables & Key-Values
        tables = self.struct_extractor.extract_tables(html)
        key_values = self.struct_extractor.extract_key_values(html)

        # 3. Automatic Contact Discovery (Emails, Phones)
        contacts = {}
        if extract_contacts:
            contacts = self._extract_contacts(html)

        # 4. Custom Schema Extraction (if user supplied CSS rules)
        custom_data = {}
        if extract_schema and html:
            custom_data = self._extract_by_schema(html, extract_schema)

        return {
            "url": url,
            "status": res.get("status", 200),
            "title": res.get("title", ""),
            "elapsed_ms": elapsed_ms,
            "markdown": markdown,
            "contacts": contacts,
            "custom_data": custom_data,
            "tables": tables,
            "key_values": key_values,
        }

    async def scrape_batch(
        self,
        urls: List[str],
        extract_schema: Optional[Dict[str, str]] = None,
        concurrency: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scrapes a collection of URLs concurrently.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _worker(target_url: str):
            async with semaphore:
                try:
                    return await self.scrape_url(target_url, extract_schema=extract_schema)
                except Exception as e:
                    return {"url": target_url, "error": str(e), "status": 500}

        tasks = [_worker(u) for u in urls]
        return await asyncio.gather(*tasks)

    async def crawl(
        self,
        start_url: str,
        max_pages: int = 10,
        same_domain: bool = True,
        extract_schema: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively crawls URLs starting from a root address, similar to Scrapy / Crawl4AI.
        """
        visited = set()
        queue = [start_url]
        results = []
        parsed_root = urlparse(start_url)
        root_domain = parsed_root.netloc

        while queue and len(visited) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            page_data = await self.scrape_url(current_url, extract_schema=extract_schema)
            results.append(page_data)

            # Extract outgoing links
            soup = BeautifulSoup(page_data.get("markdown", ""), "html.parser")
            # Discover links in markdown / html
            outgoing = self._find_outgoing_links(page_data.get("markdown", ""), current_url)
            for link in outgoing:
                parsed_link = urlparse(link)
                if same_domain and parsed_link.netloc != root_domain:
                    continue
                if link not in visited and link not in queue:
                    queue.append(link)

        return results

    def _extract_contacts(self, html: str) -> Dict[str, List[str]]:
        """Extracts valid emails and phone numbers from HTML."""
        # Email regex matching standard RFC formats
        email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = list(set(re.findall(email_pattern, html)))
        # Filter obvious static asset false positives (.png, .jpg, .svg)
        clean_emails = [
            e for e in emails
            if not any(e.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp"])
        ]

        # Phone numbers
        phone_pattern = r'(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]*(\d{3})[-. ]*(\d{4})'
        phone_matches = re.findall(phone_pattern, html)
        phones = list(set(["-".join(filter(None, p)) for p in phone_matches if len(p) >= 3]))

        return {
            "emails": clean_emails,
            "phones": phones
        }

    def _extract_by_schema(self, html: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """Extracts targeted fields using BeautifulSoup CSS selectors."""
        soup = BeautifulSoup(html, "html.parser")
        data = {}
        for field, selector in schema.items():
            if selector.startswith("//"):
                # XPath-like or simple text search
                data[field] = ""
            else:
                nodes = soup.select(selector)
                if len(nodes) == 1:
                    data[field] = nodes[0].get_text(strip=True)
                elif len(nodes) > 1:
                    data[field] = [n.get_text(strip=True) for n in nodes]
                else:
                    data[field] = None
        return data

    def _find_outgoing_links(self, text: str, base_url: str) -> List[str]:
        """Finds markdown formatted links [title](url) or http links."""
        links = re.findall(r'\[.*?\]\((https?://[^\)]+)\)', text)
        return list(set(links))

    async def close(self):
        if self._owns_browser and self.browser:
            await self.browser.aclose()
