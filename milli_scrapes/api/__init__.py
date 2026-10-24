"""
Milli Scrape API Gateway Package.
High-speed, production-grade web scraping, crawling, and System 1 decision server.
Includes 100% Firecrawl drop-in compatibility and interactive web playground.
"""

from .app import create_app, app

__all__ = ["create_app", "app"]
