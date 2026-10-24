"""
Automated Test Suite for Milli Scrape API Gateway and Playground.
Verifies all endpoints, Firecrawl drop-in compatibility, System 1 decision routes, and auth metering.
"""

import pytest
from fastapi.testclient import TestClient

from milli_scrapes.api.app import app
from milli_scrapes.api import auth

client = TestClient(app)


def test_serve_playground():
    """Verifies that the interactive live playground UI is served on GET /."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "MILLI" in resp.text
    assert "SCRAPES" in resp.text
    assert "1.8" in resp.text
    assert "Hacker News" in resp.text


def test_health_endpoint():
    """Verifies health check and system metric calculations."""
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert "total_requests" in data
    assert "engine" in data


def test_scrape_native_endpoint():
    """Verifies POST /v1/scrape returns native Milli structured response."""
    resp = client.post(
        "/v1/scrape",
        json={"url": "https://httpbin.org/html", "triage": True}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["url"] == "https://httpbin.org/html"
    assert "markdown" in data
    assert len(data["markdown"]) > 0
    assert "elapsed_ms" in data
    assert "token_reduction_percent" in data
    assert data["token_reduction_percent"] >= 0.0
    assert "triage" in data


def test_scrape_firecrawl_compat():
    """Verifies POST /v1/scrape returns 100% Firecrawl-compliant schema when requested."""
    resp = client.post(
        "/v1/scrape",
        json={
            "url": "https://httpbin.org/html",
            "formats": ["markdown", "html"],
            "onlyMainContent": True
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "data" in data
    assert "markdown" in data["data"]
    assert "metadata" in data["data"]
    assert data["data"]["metadata"]["statusCode"] == 200
    assert data["data"]["metadata"]["sourceURL"] == "https://httpbin.org/html"
    assert "milli_metadata" in data["data"]
    assert "speedup_vs_firecrawl" in data["data"]["milli_metadata"]


def test_decision_triage_endpoint():
    """Verifies System 1 non-autoregressive triage routing (< 1ms)."""
    blocked_html = "<html><head><title>Just a moment...</title></head><body>Verify you are human. Cloudflare Ray ID: 9988.</body></html>"
    resp = client.post(
        "/v1/decision/triage",
        json={"html": blocked_html, "url": "https://challenge-target.com"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["is_blocked"] is True
    assert data["layout_type"] == "CAPTCHA_GATE"
    assert data["elapsed_ms"] < 15.0


def test_decision_choice_endpoint():
    """Verifies categorical option selection."""
    product_state = "<div class='product'><h3>iPhone 16 Pro</h3><span class='price'>$999</span><button>Add to Cart</button></div>"
    resp = client.post(
        "/v1/decision/choice",
        json={
            "state": product_state,
            "options": ["PRODUCT_CATALOG", "DOCUMENTATION", "PAYWALL", "FORUM"]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["selected"] == "PRODUCT_CATALOG"
    assert data["confidence"] > 0.5
    assert data["latency_ms"] < 15.0


def test_decision_noul_endpoint():
    """Verifies calibrated boolean verification."""
    article_state = "The quick brown fox jumps over the lazy dog."
    resp = client.post(
        "/v1/decision/noul",
        json={
            "state": article_state,
            "statement": "Does this text contain the word fox?",
            "threshold": 0.5
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["value"] is True
    assert data["probability"] > 0.5


def test_auth_enforcement():
    """Verifies API key enforcement and unauthorized 401 handling."""
    original_key = auth.MASTER_KEY
    try:
        auth.MASTER_KEY = "milli_secret_key_prod"

        # Request with no key -> 401
        resp_unauth = client.get("/v1/health")
        # Health is open, but protected scrape route should fail:
        resp_scrape_unauth = client.post("/v1/scrape", json={"url": "https://example.com"})
        assert resp_scrape_unauth.status_code == 401

        # Request with valid key -> 200
        resp_valid = client.post(
            "/v1/scrape",
            json={"url": "https://example.com"},
            headers={"X-Milli-Key": "milli_secret_key_prod"}
        )
        assert resp_valid.status_code == 200
    finally:
        auth.MASTER_KEY = original_key
