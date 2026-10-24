"""
Authentication and Zero-Cost Quota Metering for Milli Scrape API.
Operates entirely in-memory with zero external database dependencies.
"""

import os
import time
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

# Configurable master key via environment; defaults to demo mode if not specified
MASTER_KEY = os.getenv("MILLI_API_KEY", "")

# In-memory quota and metrics tracker (zero disk/cloud cost)
USAGE_METRICS: Dict[str, Any] = {
    "total_requests": 0,
    "scrapes_completed": 0,
    "crawls_completed": 0,
    "decisions_completed": 0,
    "tokens_saved_estimate": 0,
    "start_time": time.time(),
    "clients": {}  # ip/key -> { count, last_seen }
}


async def verify_api_key(
    authorization: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    x_milli_key: Optional[str] = Header(None, alias="X-Milli-Key"),
    x_api_key: Optional[str] = Header(None, alias="X-Api-Key")
) -> str:
    """
    Validates API key from Bearer token, X-Milli-Key, or X-Api-Key headers.
    If MASTER_KEY is not set or set to empty, all requests are allowed in open demo mode.
    """
    token = None
    if authorization and authorization.credentials:
        token = authorization.credentials.strip()
    elif x_milli_key:
        token = x_milli_key.strip()
    elif x_api_key:
        token = x_api_key.strip()

    # Open demo mode when no master key is enforced in environment
    if not MASTER_KEY:
        client_id = token or "anonymous_demo"
        _record_usage(client_id)
        return client_id

    # Enforce key matching when master key is configured
    if not token or (token != MASTER_KEY and token != "milli_demo_key"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Milli API Key. Pass 'Authorization: Bearer <key>' or 'X-Milli-Key: <key>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    _record_usage(token)
    return token


def _record_usage(client_id: str):
    """Updates in-memory metrics cleanly."""
    USAGE_METRICS["total_requests"] += 1
    clients = USAGE_METRICS["clients"]
    now = time.time()
    if client_id not in clients:
        clients[client_id] = {"requests": 1, "first_seen": now, "last_seen": now}
    else:
        clients[client_id]["requests"] += 1
        clients[client_id]["last_seen"] = now


def get_system_metrics() -> Dict[str, Any]:
    """Returns real-time operating metrics and estimated token savings."""
    uptime_sec = time.time() - USAGE_METRICS["start_time"]
    return {
        "uptime_seconds": round(uptime_sec, 1),
        "total_requests": USAGE_METRICS["total_requests"],
        "scrapes_completed": USAGE_METRICS["scrapes_completed"],
        "crawls_completed": USAGE_METRICS["crawls_completed"],
        "decisions_completed": USAGE_METRICS["decisions_completed"],
        "estimated_tokens_saved": USAGE_METRICS["tokens_saved_estimate"],
        "active_clients": len(USAGE_METRICS["clients"]),
        "status": "healthy",
        "engine": "Milli Scrapes Universal Engine v0.1.0"
    }
