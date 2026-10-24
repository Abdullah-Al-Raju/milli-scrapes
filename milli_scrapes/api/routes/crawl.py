"""
Domain topology mapping and recursive crawling route handlers.
"""

import time
from fastapi import APIRouter, Depends

from milli_scrapes.scraper.universal import UniversalScraper
from ..models import MapRequest, MapResponse, CrawlRequest, CrawlResponse
from ..auth import verify_api_key, USAGE_METRICS
from .scrape import get_scraper

router = APIRouter(prefix="/v1", tags=["Crawling & Mapping"])


@router.post("/map", response_model=MapResponse)
async def map_domain_topology(
    req: MapRequest,
    client_id: str = Depends(verify_api_key)
) -> MapResponse:
    """
    Sub-second internal URL and sitemap topology discovery.
    """
    scraper = get_scraper()
    t0 = time.perf_counter()

    res = await scraper.map(base_url=req.url, max_urls=req.max_urls or 500)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    USAGE_METRICS["crawls_completed"] += 1

    links = res.get("links", [])
    if req.search:
        search_lower = req.search.lower()
        links = [u for u in links if search_lower in u.lower()]

    return MapResponse(
        success=True,
        base_url=req.url,
        urls_found=len(links),
        sitemaps=res.get("sitemaps", []),
        links=links,
        clusters=res.get("clusters", {}),
        elapsed_ms=round(elapsed_ms, 2)
    )


@router.post("/crawl", response_model=CrawlResponse)
async def crawl_domain_deep(
    req: CrawlRequest,
    client_id: str = Depends(verify_api_key)
) -> CrawlResponse:
    """
    Scoped recursive domain crawl with path filtering and depth limits.
    """
    scraper = get_scraper()
    t0 = time.perf_counter()

    res = await scraper.crawl(
        start_url=req.url,
        max_pages=req.max_pages or 20,
        max_depth=req.max_depth or 2,
        include_paths=req.include_paths,
        exclude_paths=req.exclude_paths,
        concurrency=req.concurrency or 5
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    USAGE_METRICS["crawls_completed"] += 1

    pages = res.get("pages", [])

    return CrawlResponse(
        success=True,
        start_url=req.url,
        pages_crawled=len(pages),
        elapsed_ms=round(elapsed_ms, 2),
        pages=pages
    )
