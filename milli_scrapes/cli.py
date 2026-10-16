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


@click.group()
def main():
    """Milli-Scrapes: Ultra-Fast Visual Web Scraper, Change Monitor, and Reflex Seat Booking Engine."""
    pass


@main.command("scrape")
@click.argument("url")
@click.option("--format", "output_format", type=click.Choice(["markdown", "json", "html"]), default="markdown", help="Output extraction format")
@click.option("--contacts/--no-contacts", default=True, help="Extract emails, phones, and contacts")
@click.option("--crawl", "crawl_pages", default=0, type=int, help="Crawl N pages following links on domain")
@click.option("--schema", default=None, help="JSON string of field:selector mappings, e.g. '{\"title\": \"h1\"}'")
@click.option("--headless/--no-headless", default=True, help="Run browser headless")
def scrape(url: str, output_format: str, contacts: bool, crawl_pages: int, schema: Optional[str], headless: bool):
    """Universal scraper: Extracts clean Markdown, structured JSON, contacts, or crawls any URL."""
    async def _run():
        schema_dict = json.loads(schema) if schema else None
        scraper = UniversalScraper(headless=headless)
        await scraper.browser.start()
        try:
            if crawl_pages > 0:
                results = await scraper.crawl(start_url=url, max_pages=crawl_pages, extract_schema=schema_dict)
                click.echo(json.dumps(results, indent=2))
            else:
                data = await scraper.scrape_url(url=url, extract_schema=schema_dict, extract_contacts=contacts)
                if output_format == "markdown":
                    click.echo(click.style(f"\n✓ Scraped {url} in {data['elapsed_ms']} ms", fg="green", bold=True))
                    if contacts and data.get("contacts", {}).get("emails"):
                        click.echo(click.style(f"  • Emails: {', '.join(data['contacts']['emails'])}", fg="cyan"))
                    click.echo("\n" + "="*70 + "\n" + data["markdown"] + "\n" + "="*70)
                elif output_format == "json":
                    click.echo(json.dumps(data, indent=2))
                else:
                    click.echo(data.get("markdown", ""))
        finally:
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
@click.option("--mode", type=click.Choice(["optical", "dom"]), default="optical", help="Sniping mode: visual canvas or in-loop DOM")
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

    asyncio.run(_run())


if __name__ == "__main__":
    main()
