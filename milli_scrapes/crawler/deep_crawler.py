"""
High-Concurrency Deep Crawler and Site Hierarchy Engine.
Provides full /crawl capabilities: path inclusion/exclusion, depth limits, concurrent workers,
and automatic streaming callbacks.
"""

import fnmatch
import time
import asyncio
import re
from typing import List, Dict, Any, Optional, Set, Callable
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from ..scraper.hybrid_router import HybridScrapeRouter
from ..extractor.markdown import HTMLToMarkdownExtractor
from ..sniper.consent_sniper import ConsentSniper
from ..sniper.turnstile_sniper import TurnstileSniper


class CrawlResult(dict):
    """
    Dual representation for crawl results:
    Acts as a dictionary (metadata, metrics) AND as an iterable/indexable list of page dictionaries.
    """
    def __iter__(self):
        return iter(self.get("pages", []))

    def __len__(self):
        return len(self.get("pages", []))

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.get("pages", [])[item]
        return super().__getitem__(item)


class MilliCrawler:
    """
    High-concurrency recursive crawler matching and surpassing Firecrawl & Spider.cloud:
    - Scoped path inclusion and exclusion globbing (e.g. /docs/*, !/auth/*)
    - Depth-controlled URL graph traversal
    - Concurrency worker pools with asynchronous queues
    - Turnstile and Cookie auto-dismissal on every resolved node
    """

    def __init__(
        self,
        router: Optional[HybridScrapeRouter] = None,
        concurrency: int = 5,
        prefer_fast_path: bool = True
    ):
        self.router = router or HybridScrapeRouter(prefer_fast_path=prefer_fast_path)
        self.concurrency = concurrency
        self.md_extractor = HTMLToMarkdownExtractor()

    async def crawl(
        self,
        start_url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        allow_subdomains: bool = False,
        on_page_scraped: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> CrawlResult:
        """
        Crawls a domain starting at start_url adhering to depth, glob filters, and concurrency.
        """
        t0 = time.perf_counter()
        parsed_root = urlparse(start_url)
        root_domain = parsed_root.netloc

        visited: Set[str] = set()
        queue: asyncio.Queue = asyncio.Queue()

        # Item tuple: (url, depth)
        await queue.put((start_url, 0))
        visited.add(start_url)

        results: List[Dict[str, Any]] = []
        semaphore = asyncio.Semaphore(self.concurrency)

        async def worker():
            while not queue.empty() and len(results) < max_pages:
                try:
                    current_url, depth = await asyncio.wait_for(queue.get(), timeout=1.0)
                except (asyncio.TimeoutError, asyncio.QueueEmpty):
                    break

                async with semaphore:
                    try:
                        res = await self.router.fetch_page(current_url)
                        html = res.get("html", "")
                        status = res.get("status", 200)

                        # Extract Markdown and metadata
                        markdown, metadata = self.md_extractor.extract_with_metadata(html)

                        page_record = {
                            "url": current_url,
                            "depth": depth,
                            "status": status,
                            "title": res.get("title") or metadata.get("title", ""),
                            "engine": res.get("engine", "fast_http"),
                            "markdown": markdown,
                            "metadata": metadata,
                            "elapsed_ms": res.get("elapsed_ms", 0.0)
                        }

                        results.append(page_record)
                        if on_page_scraped:
                            try:
                                on_page_scraped(page_record)
                            except Exception:
                                pass

                        # Discover outgoing links if depth < max_depth
                        if depth < max_depth and len(results) < max_pages:
                            links = self._extract_links(html, current_url)
                            for link in links:
                                if link not in visited and len(visited) < max_pages * 3:
                                    if self._is_allowed(link, root_domain, allow_subdomains, include_paths, exclude_paths):
                                        visited.add(link)
                                        await queue.put((link, depth + 1))

                    except Exception as e:
                        results.append({
                            "url": current_url,
                            "depth": depth,
                            "status": 500,
                            "error": str(e)
                        })
                    finally:
                        queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(self.concurrency)]
        await asyncio.gather(*workers)

        total_elapsed_sec = time.perf_counter() - t0
        pages_per_sec = len(results) / max(0.001, total_elapsed_sec)

        return CrawlResult({
            "root_url": start_url,
            "total_crawled": len(results),
            "pages": results,
            "elapsed_sec": round(total_elapsed_sec, 2),
            "pages_per_second": round(pages_per_sec, 2)
        })

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extracts and normalizes all valid HTTP/HTTPS anchor links from HTML."""
        links: List[str] = []
        raw_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        for href in raw_hrefs:
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full_url = urljoin(base_url, href)
            p = urlparse(full_url)
            if p.scheme in ("http", "https"):
                # Normalize link
                clean_url = f"{p.scheme}://{p.netloc}{p.path}"
                if p.query:
                    clean_url += f"?{p.query}"
                if not any(clean_url.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".pdf", ".zip"]):
                    links.append(clean_url)
        return list(dict.fromkeys(links))

    def _is_allowed(
        self,
        url: str,
        root_domain: str,
        allow_subdomains: bool,
        include_paths: Optional[List[str]],
        exclude_paths: Optional[List[str]]
    ) -> bool:
        """Evaluates whether a candidate URL should be crawled based on domain and glob patterns."""
        p = urlparse(url)

        # Domain check
        if allow_subdomains:
            if not p.netloc.endswith(root_domain):
                return False
        else:
            if p.netloc != root_domain:
                return False

        path = p.path or "/"

        # Exclusion paths check
        if exclude_paths:
            for pat in exclude_paths:
                if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat):
                    return False

        # Inclusion paths check
        if include_paths:
            matched = False
            for pat in include_paths:
                if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(url, pat):
                    matched = True
                    break
            if not matched:
                return False

        return True
