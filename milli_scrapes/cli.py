"""
Milli-Scrapes Unified Command-Line Interface.
Commands:
  scrape  Extracts clean Markdown or structured JSON from any URL in milliseconds.
  watch   Continuously monitors a web page for changes and sends instant email alerts.
  snipe   Fires sub-15ms optical or DOM reflex booking actions for high-demand seats.
"""

import sys
import asyncio
import json
import click

from .browser.engine import MilliScrapeBrowser
from .extractor.markdown import HTMLToMarkdownExtractor
from .extractor.structured import StructuredDataExtractor
from .monitor.watcher import WebsiteWatcher
from .notifier.email import EmailNotifier
from .sniper.seat_sniper import ReflexSeatSniper


from .scraper.universal import UniversalScraper

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass


@click.group()
def main():
    """Milli-Scrapes: Ultra-Fast Visual Web Scraper, Change Monitor, and Reflex Seat Booking Engine."""
    pass


@main.command("scrape")
@click.argument("url")
@click.option("--format", "output_format", type=click.Choice(["markdown", "json", "html"]), default="markdown", help="Output extraction format")
@click.option("--contacts/--no-contacts", default=True, help="Extract emails, phones, and contacts")
@click.option("--chunk/--no-chunk", default=False, help="Produce RAG semantic chunks")
@click.option("--chunk-strategy", type=click.Choice(["heading", "sentence", "sliding"]), default="heading", help="RAG chunking strategy")
@click.option("--turnstile/--no-turnstile", default=True, help="Auto-solve Cloudflare Turnstile challenges")
@click.option("--auto-consent/--no-consent", default=True, help="Auto-dismiss cookie banners in sub-15ms")
@click.option("--proxy", default=None, help="Proxy URL (http://... or socks5://...)")
@click.option("--schema", default=None, help="JSON string of field:selector mappings, e.g. '{\"title\": \"h1\"}'")
@click.option("--headless/--no-headless", default=True, help="Run browser headless")
def scrape(url: str, output_format: str, contacts: bool, chunk: bool, chunk_strategy: str, turnstile: bool, auto_consent: bool, proxy: Optional[str], schema: Optional[str], headless: bool):
    """Universal scraper: Extracts clean Markdown, structured JSON, contacts, tables, and RAG chunks."""
    async def _run():
        schema_dict = json.loads(schema) if schema else None
        from .browser.proxy import ProxyPoolManager
        proxy_mgr = ProxyPoolManager([proxy]) if proxy else None
        browser = MilliScrapeBrowser(headless=headless, proxy_manager=proxy_mgr)
        scraper = UniversalScraper(browser=browser, auto_consent=auto_consent, auto_turnstile=turnstile)
        try:
            data = await scraper.scrape_url(
                url=url,
                extract_schema=schema_dict,
                extract_contacts=contacts,
                chunk=chunk,
                chunk_strategy=chunk_strategy
            )
            if output_format == "markdown":
                click.echo(click.style(f"\n✓ Scraped {url} in {data['elapsed_ms']} ms [{data.get('engine')}]", fg="green", bold=True))
                if contacts and (data.get("contacts") or {}).get("emails"):
                    click.echo(click.style(f"  • Emails: {', '.join(data['contacts']['emails'])}", fg="cyan"))
                if contacts and (data.get("contacts") or {}).get("social_media"):
                    for plat, link in data["contacts"]["social_media"].items():
                        click.echo(click.style(f"  • {plat.replace('_', ' ').title()}: {link}", fg="blue"))
                if (data.get("consent_status") or {}).get("dismissed"):
                    click.echo(click.style(f"  • Cookie Consent Auto-Dismissed: {data['consent_status']['selector']}", fg="yellow"))
                if (data.get("turnstile_status") or {}).get("solved"):
                    click.echo(click.style(f"  • Cloudflare Turnstile Solved: {data['turnstile_status']['type']}", fg="magenta"))
                click.echo("\n" + "="*70 + "\n" + data["markdown"] + "\n" + "="*70)
                if chunk and data.get("chunks"):
                    click.echo(click.style(f"\n📦 Generated {len(data['chunks'])} RAG semantic chunks", fg="blue", bold=True))
            elif output_format == "json":
                click.echo(json.dumps(data, indent=2))
            else:
                click.echo(data.get("markdown", ""))
        finally:
            await scraper.close()

    asyncio.run(_run())


@main.command("map")
@click.argument("base_url")
@click.option("--limit", default=500, type=int, help="Maximum number of URLs to discover")
def map_domain(base_url: str, limit: int):
    """Discovers all internal routes, sitemaps, and URL graphs of a target domain in seconds."""
    from .crawler.mapper import MilliMapper
    click.echo(click.style(f"\n🗺 Mapping domain topology for {base_url}...", fg="cyan", bold=True))
    res = MilliMapper.map_domain(base_url, max_urls=limit)
    click.echo(click.style(f"✓ Discovered {res['total_urls']} unique URLs in {res['elapsed_ms']} ms", fg="green", bold=True))
    if res.get("sitemaps"):
        click.echo(click.style(f"  • Sitemaps: {', '.join(res['sitemaps'])}", fg="yellow"))
    click.echo("\nRoute clusters:")
    for path_prefix, count in res.get("paths_summary", {}).items():
        click.echo(f"  {path_prefix:<25} {count} pages")
    click.echo(json.dumps(res, indent=2))


@main.command("crawl")
@click.argument("start_url")
@click.option("--limit", default=20, type=int, help="Maximum pages to crawl")
@click.option("--depth", default=2, type=int, help="Maximum crawl depth")
@click.option("--include", multiple=True, help="Path glob patterns to include (e.g. '/docs/*')")
@click.option("--exclude", multiple=True, help="Path glob patterns to exclude (e.g. '/admin/*')")
@click.option("--concurrency", default=5, type=int, help="Concurrent worker count")
def crawl_domain(start_url: str, limit: int, depth: int, include: tuple, exclude: tuple, concurrency: int):
    """High-concurrency deep crawler with path filtering, depth limits, and Markdown synthesis."""
    async def _run():
        scraper = UniversalScraper()
        click.echo(click.style(f"\n🕷 Crawling {start_url} (limit: {limit}, depth: {depth}, workers: {concurrency})...", fg="cyan", bold=True))
        results = await scraper.crawl(
            start_url=start_url,
            max_pages=limit,
            max_depth=depth,
            include_paths=list(include) if include else None,
            exclude_paths=list(exclude) if exclude else None,
            concurrency=concurrency,
            on_page_scraped=lambda p: click.echo(f"  ✓ [{p.get('status', 200)}] {p['url']} ({p.get('elapsed_ms', 0)}ms)")
        )
        click.echo(click.style(f"\n✓ Crawled {results['total_crawled']} pages in {results['elapsed_sec']}s ({results['pages_per_second']} p/s)", fg="green", bold=True))
        await scraper.close()

    asyncio.run(_run())



@main.command("watch")
@click.argument("url")
@click.option("--interval", default=2.0, help="Check interval in seconds")
@click.option("--email", default="analystx.raju@gmail.com", help="Destination recipient for alert emails")
@click.option("--optical/--no-optical", default=True, help="Enable transient RAM optical image differ")
@click.option("--cycles", default=None, type=int, help="Limit number of check cycles")
def watch(url: str, interval: float, email: str, optical: bool, cycles: int):
    """Monitors a website for visual or DOM changes and sends instant email alerts."""
    async def _run():
        browser = MilliScrapeBrowser(headless=True)
        notifier = EmailNotifier(recipient_email=email, dry_run=False)
        watcher = WebsiteWatcher(
            url=url,
            browser=browser,
            notifier=notifier,
            check_interval_seconds=interval
        )

        click.echo(click.style(f"\n👁 [Milli-Scrapes] Watching '{url}' (Interval: {interval}s, Optical: {optical})...", fg="cyan", bold=True))
        click.echo(f"  ↳ Alerts will be dispatched to: {email} (0 bytes written to disk)\n")

        await watcher.run_watch_loop(max_cycles=cycles, optical_mode=optical)

    asyncio.run(_run())


@main.command("snipe")
@click.argument("url")
@click.option("--mode", type=click.Choice(["optical", "dom", "hyper"]), default="optical", help="Sniping mode: visual optical canvas, in-loop DOM, or sub-ms V8 hyper reflex")
@click.option("--confirm", "confirm_selector", default="#confirm-booking", help="Checkout or confirmation selector")
@click.option("--seat", "seat_selector", default=".seat-available", help="DOM selector for candidate seat")
def snipe(url: str, mode: str, confirm_selector: str, seat_selector: str):
    """Executes sub-15ms reflex seat/slot booking."""
    async def _run():
        browser = MilliScrapeBrowser(headless=True)
        await browser.start()
        sniper = ReflexSeatSniper(browser=browser)

        try:
            click.echo(click.style(f"\n🎯 [Milli-Scrapes] Priming reflex sniper for '{url}' (Mode: {mode})...", fg="yellow", bold=True))
            await browser.navigate_and_settle(url)

            if mode == "optical":
                res = await sniper.snipe_optical_seat(confirm_selector=confirm_selector)
            elif mode == "hyper":
                res = await sniper.snipe_v8_hyper_seat(seat_selector=seat_selector, confirm_selector=confirm_selector)
            else:
                res = await sniper.snipe_dom_seat(seat_selector=seat_selector, confirm_selector=confirm_selector)

            if res.get("status") == "booked":
                click.echo(click.style(f"\n🏆 SEAT BOOKED IN {res['time_to_finish_ms']} ms!", fg="green", bold=True))
                click.echo(f"  • Reaction Latency: {res['reaction_latency_ms']} ms")
                click.echo(f"  • Target Mode:      {res['mode']}")
                if "target_coords" in res:
                    click.echo(f"  • Optical Centroid: {res['target_coords']}")
            else:
                click.echo(click.style(f"\n⚠️ {res.get('message', 'Booking failed')}", fg="red"))
        finally:
            await browser.aclose()

@main.command("serve")
@click.option("--host", default="0.0.0.0", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--reload/--no-reload", default=False, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool):
    """Launches the Milli Scrapes production API gateway and interactive playground."""
    from .api.app import run_server
    click.echo(click.style(f"\n⚡ [Milli Scrapes] Starting API Gateway on http://{host}:{port}", fg="green", bold=True))
    click.echo(f"  • Live Playground: http://localhost:{port}/")
    click.echo(f"  • OpenAPI Docs:   http://localhost:{port}/docs")
    click.echo(f"  • Firecrawl Mode: POST http://localhost:{port}/v1/scrape\n")
    run_server(host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
