"""
FastAPI Application Factory for Milli Scrapes API Gateway.
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .playground import PLAYGROUND_HTML
from .auth import get_system_metrics
from .routes.scrape import router as scrape_router, get_scraper
from .routes.crawl import router as crawl_router
from .routes.decision import router as decision_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager ensuring clean resource allocation and graceful browser cleanup."""
    # Pre-warm fast-path resources
    yield
    # Cleanup browser process if instantiated
    try:
        scraper = get_scraper()
        await scraper.close()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Factory creating configured FastAPI gateway."""
    application = FastAPI(
        title="Milli Scrapes API Gateway",
        description="The High-Frequency Web Scraper, Crawler, and System 1 Decision Engine for AI Agents.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Enable full Cross-Origin Resource Sharing for browser clients
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Wall-clock processing time middleware
    @application.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - t0) * 1000.0
        response.headers["X-Process-Time-Ms"] = f"{process_time_ms:.2f}"
        response.headers["X-Powered-By"] = "Milli-Scrapes-Universal-Engine"
        return response

    # Mount interactive playground on root
    @application.get("/", response_class=HTMLResponse, tags=["Playground"])
    async def serve_playground():
        return HTMLResponse(content=PLAYGROUND_HTML)

    # System health and operational metrics endpoint
    @application.get("/v1/health", tags=["Health"])
    async def health_check():
        return get_system_metrics()

    # Register API route clusters
    application.include_router(scrape_router)
    application.include_router(crawl_router)
    application.include_router(decision_router)

    return application


# Global ASGI application instance
app = create_app()


def run_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Launches the gateway server using Uvicorn."""
    import uvicorn
    uvicorn.run("milli_scrapes.api.app:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server()
