"""
System 1 Non-Autoregressive Decision Route Handlers.
Microsecond cognitive reflexes (< 0.5 ms) without generative LLM token billing.
"""

from fastapi import APIRouter, Depends
from milli_scrapes.decision import MilliDecisionEngine
from ..models import (
    DecisionTriageRequest, DecisionTriageResponse,
    DecisionChoiceRequest, DecisionChoiceResponse,
    DecisionNoulRequest, DecisionNoulResponse
)
from ..auth import verify_api_key, USAGE_METRICS

router = APIRouter(prefix="/v1/decision", tags=["System 1 Decisions"])

# Shared decision engine
_engine = MilliDecisionEngine()


@router.post("/triage", response_model=DecisionTriageResponse)
async def evaluate_page_triage(
    req: DecisionTriageRequest,
    client_id: str = Depends(verify_api_key)
) -> DecisionTriageResponse:
    """
    Evaluates anti-bot challenge status, paywalls, layout type, and density in a single forward pass (< 1 ms).
    """
    res = _engine.evaluate_triage(req.html, req.url or "")
    USAGE_METRICS["decisions_completed"] += 1

    is_blocked_val = res["is_blocked"].value if hasattr(res.get("is_blocked"), "value") else bool(res.get("is_blocked", False))
    is_paywalled_val = res["is_paywall"].value if hasattr(res.get("is_paywall"), "value") else bool(res.get("is_paywall", False))
    has_pag_val = res["has_pagination"].value if hasattr(res.get("has_pagination"), "value") else bool(res.get("has_pagination", False))
    layout_val = res["layout_type"].selected if hasattr(res.get("layout_type"), "selected") else str(res.get("layout_type", "GENERIC_PAGE"))
    density_val = res["content_density"].score if hasattr(res.get("content_density"), "score") else float(res.get("content_density", 0.5))
    elapsed_val = float(res.get("total_triage_latency_ms", 0.25))

    return DecisionTriageResponse(
        success=True,
        url=req.url or "",
        is_blocked=is_blocked_val,
        is_paywalled=is_paywalled_val,
        has_pagination=has_pag_val,
        layout_type=layout_val,
        content_density_score=density_val,
        elapsed_ms=elapsed_val
    )


@router.post("/choice", response_model=DecisionChoiceResponse)
async def decide_choice(
    req: DecisionChoiceRequest,
    client_id: str = Depends(verify_api_key)
) -> DecisionChoiceResponse:
    """
    Evaluates state against discrete options and returns winning category + softmax confidence.
    """
    choice = _engine.decide_choice(req.state, req.options, req.question or "Select optimal category")
    USAGE_METRICS["decisions_completed"] += 1

    return DecisionChoiceResponse(
        success=True,
        selected=choice.selected,
        probabilities=choice.probabilities,
        confidence=choice.confidence,
        latency_ms=choice.latency_ms
    )


@router.post("/noul", response_model=DecisionNoulResponse)
async def decide_noul(
    req: DecisionNoulRequest,
    client_id: str = Depends(verify_api_key)
) -> DecisionNoulResponse:
    """
    Calibrated non-autoregressive boolean resolution with probability in < 0.05 ms.
    """
    noul = _engine.decide_noul(req.state, req.statement, req.threshold or 0.5)
    USAGE_METRICS["decisions_completed"] += 1

    return DecisionNoulResponse(
        success=True,
        value=noul.value,
        probability=noul.probability,
        confidence=noul.confidence,
        latency_ms=noul.latency_ms
    )
