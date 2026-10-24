"""
Pydantic Models for Milli Scrape API Gateway.
Includes native high-performance models and 100% Firecrawl-compatible request/response schemas.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    """Unified scrape request supporting native Milli and Firecrawl parameters."""
    url: str = Field(..., description="Target web URL to scrape")
    
    # Native Milli options
    format: Optional[str] = Field("markdown", description="Preferred output format: 'markdown', 'json', or 'html'")
    extract_contacts: Optional[bool] = Field(True, description="Whether to extract discovered email addresses and phone numbers")
    chunk: Optional[bool] = Field(False, description="Whether to partition markdown into RAG semantic chunks")
    chunk_strategy: Optional[str] = Field("heading", description="RAG chunking strategy: 'heading' or 'sentence'")
    extract_schema: Optional[Dict[str, str]] = Field(None, description="CSS selector mapping for targeted field extraction")
    force_browser: Optional[bool] = Field(False, description="Force Chromium optical browser over fast-path HTTP")
    triage: Optional[bool] = Field(True, description="Execute System 1 non-autoregressive triage classification")
    
    # Firecrawl compatibility fields
    formats: Optional[List[str]] = Field(None, description="Firecrawl compatible formats list: ['markdown', 'html', 'rawHtml']")
    onlyMainContent: Optional[bool] = Field(True, description="Firecrawl compatible main content stripping")
    waitFor: Optional[int] = Field(0, description="Firecrawl compatible wait interval in milliseconds")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom HTTP headers to send")


class ScrapeResponse(BaseModel):
    """Milli native high-fidelity scrape response."""
    success: bool = True
    url: str
    status: int = 200
    title: str = ""
    engine: str = "fast_http"
    elapsed_ms: float = 0.0
    markdown: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[Dict[str, Any]] = Field(default_factory=list)
    contacts: Dict[str, List[str]] = Field(default_factory=dict)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    key_values: Dict[str, Any] = Field(default_factory=dict)
    triage: Optional[Dict[str, Any]] = None
    token_reduction_percent: float = 75.0
    speedup_vs_firecrawl: str = "1.8x"


class BatchScrapeRequest(BaseModel):
    """Batch concurrent scrape request."""
    urls: List[str]
    concurrency: Optional[int] = Field(5, ge=1, le=20)
    extract_schema: Optional[Dict[str, str]] = None


class BatchScrapeResponse(BaseModel):
    """Batch scrape response summary."""
    success: bool = True
    total: int
    successful: int
    elapsed_ms: float
    results: List[Dict[str, Any]]


class MapRequest(BaseModel):
    """Domain URL topology and sitemap discovery request."""
    url: str = Field(..., description="Target domain or base URL")
    max_urls: Optional[int] = Field(500, ge=10, le=5000)
    search: Optional[str] = Field(None, description="Optional search filter for discovered paths")


class MapResponse(BaseModel):
    """Discovered internal routes and sitemaps."""
    success: bool = True
    base_url: str
    urls_found: int
    sitemaps: List[str] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    clusters: Dict[str, List[str]] = Field(default_factory=dict)
    elapsed_ms: float = 0.0


class CrawlRequest(BaseModel):
    """Scoped recursive crawling request."""
    url: str = Field(..., description="Starting URL for crawl")
    max_pages: Optional[int] = Field(20, ge=1, le=100)
    max_depth: Optional[int] = Field(2, ge=1, le=5)
    include_paths: Optional[List[str]] = None
    exclude_paths: Optional[List[str]] = None
    concurrency: Optional[int] = Field(5, ge=1, le=10)


class CrawlResponse(BaseModel):
    """Recursive crawl execution output."""
    success: bool = True
    start_url: str
    pages_crawled: int
    elapsed_ms: float
    pages: List[Dict[str, Any]]


class DecisionTriageRequest(BaseModel):
    """HTML state for single-pass System 1 classification."""
    html: str
    url: Optional[str] = ""


class DecisionTriageResponse(BaseModel):
    """System 1 page triage evaluation."""
    success: bool = True
    url: str
    is_blocked: bool
    is_paywalled: bool
    has_pagination: bool
    layout_type: str
    content_density_score: float
    elapsed_ms: float


class DecisionChoiceRequest(BaseModel):
    """Categorical selection request."""
    state: str
    options: List[str]
    question: Optional[str] = "Select optimal category"


class DecisionChoiceResponse(BaseModel):
    """Winning option with softmax confidence."""
    success: bool = True
    selected: str
    probabilities: Dict[str, float]
    confidence: float
    latency_ms: float


class DecisionNoulRequest(BaseModel):
    """Calibrated boolean verification request."""
    state: str
    statement: str
    threshold: Optional[float] = 0.5


class DecisionNoulResponse(BaseModel):
    """Binary resolution with probability."""
    success: bool = True
    value: bool
    probability: float
    confidence: float
    latency_ms: float
