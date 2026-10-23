"""
Milli-Scrapes Model Context Protocol (MCP) Server.
Exposes ultra-fast web scraping, structured extraction, site crawling,
and change monitoring directly to Cursor, Claude Desktop, and autonomous AI agents.
"""

import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from milli_scrapes.scraper.universal import UniversalScraper
from milli_scrapes.browser.engine import MilliScrapeBrowser


TOOLS_SCHEMA = [
    {
        "name": "milli_scrape_url",
        "description": "Scrapes any webpage in milliseconds using in-loop CDP execution. Automatically bypasses anti-bot defenses, auto-dismisses cookie banners in sub-15ms, solves Turnstile gates, and extracts clean token-efficient Markdown, tables, contacts (emails, phones), and optional RAG semantic chunks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Target web URL to scrape"
                },
                "format": {
                    "type": "string",
                    "enum": ["markdown", "json"],
                    "default": "markdown",
                    "description": "Preferred output extraction format"
                },
                "extract_contacts": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to extract emails and phone numbers"
                },
                "chunk": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to split markdown into RAG semantic chunks"
                },
                "schema": {
                    "type": "object",
                    "description": "Optional mapping of field names to CSS selectors, e.g. {'title': 'h1', 'price': '.price'}"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "milli_map_domain",
        "description": "Rapidly discovers all internal paths, sitemaps, and route clusters for a domain in seconds without downloading full pages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Target domain or base URL, e.g. https://docs.stripe.com"
                },
                "max_urls": {
                    "type": "integer",
                    "default": 500,
                    "description": "Maximum number of URLs to discover"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "milli_crawl_sitemap",
        "description": "Discovers and scrapes all URLs from a domain's XML sitemap or robots.txt at high asynchronous concurrency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Domain root URL or sitemap.xml link"
                },
                "max_urls": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum number of URLs to scrape from sitemap"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "milli_crawl_domain",
        "description": "Recursively crawls links on a domain starting from a root URL with path globbing and concurrency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_url": {
                    "type": "string",
                    "description": "Root URL to begin crawling"
                },
                "max_pages": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of internal pages to crawl"
                },
                "include_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Glob patterns to include, e.g. ['/docs/*']"
                },
                "exclude_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Glob patterns to exclude, e.g. ['/admin/*']"
                }
            },
            "required": ["start_url"]
        }
    }
]



class MilliScrapesMCPServer:
    """
    Standard JSON-RPC 2.0 stdio MCP Server.
    """

    def __init__(self):
        self.scraper: Optional[UniversalScraper] = None

    async def initialize(self):
        self.scraper = UniversalScraper(headless=True, auto_consent=True)
        await self.scraper.browser.start()

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "milli-scrapes-mcp",
                        "version": "0.1.0"
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_SCHEMA}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})

            try:
                if tool_name == "milli_scrape_url":
                    url = args.get("url")
                    fmt = args.get("format", "markdown")
                    contacts = args.get("extract_contacts", True)
                    chunk = args.get("chunk", False)
                    schema = args.get("schema")

                    res = await self.scraper.scrape_url(
                        url=url,
                        extract_schema=schema,
                        extract_contacts=contacts,
                        chunk=chunk
                    )
                    content_text = res["markdown"] if fmt == "markdown" else json.dumps(res, indent=2)
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": content_text}],
                            "isError": False
                        }
                    }

                elif tool_name == "milli_map_domain":
                    url = args.get("url")
                    max_urls = args.get("max_urls", 500)
                    res = await self.scraper.map(url, max_urls=max_urls)
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(res, indent=2)}],
                            "isError": False
                        }
                    }

                elif tool_name == "milli_crawl_sitemap":
                    url = args.get("url")
                    max_urls = args.get("max_urls", 20)
                    results = await self.scraper.crawl_sitemap(url, max_urls=max_urls)
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(results, indent=2)}],
                            "isError": False
                        }
                    }

                elif tool_name == "milli_crawl_domain":
                    start_url = args.get("start_url")
                    max_pages = args.get("max_pages", 10)
                    include_paths = args.get("include_paths")
                    exclude_paths = args.get("exclude_paths")
                    results = await self.scraper.crawl(
                        start_url,
                        max_pages=max_pages,
                        include_paths=include_paths,
                        exclude_paths=exclude_paths
                    )
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [{"type": "text", "text": json.dumps(results, indent=2)}],
                            "isError": False
                        }
                    }

                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}
                    }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error executing tool: {str(e)}"}],
                        "isError": True
                    }
                }

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"}
        }

    async def run_stdio(self):
        """Runs the JSON-RPC stdio event loop."""
        await self.initialize()
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line = await reader.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue
            try:
                req = json.loads(line_str)
                resp = await self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(e)}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


def main():
    server = MilliScrapesMCPServer()
    asyncio.run(server.run_stdio())


if __name__ == "__main__":
    main()
