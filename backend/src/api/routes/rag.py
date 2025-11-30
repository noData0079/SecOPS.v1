# backend/src/api/routes/rag.py

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGExplainRequest,
    RAGExplainResponse,
    RAGDebugRequest,
    RAGDebugResponse,
)
from rag.AdvancedRAGSystem import AdvancedRAGSystem
from services.metrics_collector import metrics_collector
from services.cost_tracker import cost_tracker
from utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"],
)


# --- RAG engine dependency ----------------------------------------------------


_rag_engine: AdvancedRAGSystem | None = None


def get_rag_engine() -> AdvancedRAGSystem:
    """
    Lazily instantiate a singleton RAG engine.

    This keeps `rag.py` stable: other modules can evolve internally as long
    as `AdvancedRAGSystem` exposes the same public methods used here.
    """
    global _rag_engine
    if _rag_engine is None:
        logger.info("Initializing AdvancedRAGSystem engine")
        _rag_engine = AdvancedRAGSystem(settings=settings)
    return _rag_engine


# --- Helper: safe error response ---------------------------------------------


def _build_error_response(
    message: str,
    *,
    debug: dict[str, Any] | None = None,
) -> RAGQueryResponse:
    """
    Construct a standardized error response without raising an HTTP exception.

    This ensures the API never returns raw stack traces to clients and always
    returns a consistent JSON shape.
    """
    return RAGQueryResponse(
        answer="",
        intent="auto",
        citations=[],
        usage=None,
        latency_ms=None,
        status="error",
        error_message=message,
        debug=debug or {},
    )


# --- Health / ping -----------------------------------------------------------


@router.get("/ping", summary="Lightweight RAG health check")
async def rag_ping() -> dict[str, str]:
    """
    Lightweight ping endpoint to verify that the RAG router is alive.

    This does not exercise the full RAG pipeline, only the API layer.
    """
    return {"status": "ok", "message": "RAG router is alive"}


# --- Main query endpoint -----------------------------------------------------


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Run a RAG query",
    response_description="Answer with citations and diagnostics.",
)
async def rag_query(
    request: Request,
    payload: RAGQueryRequest,
    engine: AdvancedRAGSystem = Depends(get_rag_engine),
) -> RAGQueryResponse:
    """
    Main endpoint for production RAG queries.

    - Validates and normalizes input.
    - Delegates to `AdvancedRAGSystem` for retrieval + reasoning.
    - Records metrics and cost.
    - Returns a stable, well-typed response even on internal errors.
    """
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    intent = payload.intent or "auto"
    user_id = payload.user_id
    org_id = payload.org_id

    start_time = time.perf_counter()

    try:
        result: RAGQueryResponse = await engine.run_query(
            request=payload,
            user_id=user_id,
            org_id=org_id,
        )
    except Exception as exc:
        logger.exception("RAG query failed with unexpected error")
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Record failed metrics with minimal info
        metrics_collector.record_query(
            query_id="unknown",
            duration=elapsed_ms / 1000.0,
            tokens=0,
            cost=0.0,
            intent=intent,
            status="error",
            citations_count=0,
            trust_score=0.0,
        )

        return _build_error_response(
            "Internal RAG error. The issue has been logged.",
            debug={"exception_type": type(exc).__name__},
        )

    # Safely handle missing usage in result
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    if result.usage is not None:
        input_tokens = getattr(result.usage, "input_tokens", 0) or 0
        output_tokens = getattr(result.usage, "output_tokens", 0) or 0
        total_tokens = getattr(result.usage, "total_tokens", 0) or (
            input_tokens + output_tokens
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    # Record metrics
    try:
        metrics_collector.record_query(
            query_id=getattr(result, "query_id", "unknown"),
            duration=elapsed_ms / 1000.0,
            tokens=total_tokens,
            cost=0.0,  # actual cost is computed below
            intent=result.intent or intent,
            status=result.status,
            citations_count=len(result.citations),
            trust_score=result.debug.get("avg_trust_score", 0.0)
            if result.debug
            else 0.0,
        )
    except Exception:
        logger.exception("Failed to record RAG metrics")

    # Record cost (if usage is available)
    try:
        if input_tokens or output_tokens:
            provider = getattr(result.debug, "llm_provider", None) if result.debug else None
            provider = provider or settings.DEFAULT_LLM_PROVIDER
            estimated_cost = cost_tracker.record_cost(
                provider=provider,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=getattr(result.debug, "llm_model", None)
                if result.debug
                else settings.DEFAULT_LLM_MODEL,
            )
            # Attach cost info into debug block (non-breaking)
            if result.debug is None:
                result.debug = {}
            result.debug.setdefault("billing", {})
            result.debug["billing"].update(
                {
                    "estimated_cost_usd": round(estimated_cost, 6),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }
            )
    except Exception:
        logger.exception("Failed to record RAG cost")

    # Attach latency to response
    result.latency_ms = elapsed_ms

    return result


# --- Explain endpoint (CRAG / reasoning view) --------------------------------


@router.post(
    "/explain",
    response_model=RAGExplainResponse,
    summary="Explain a RAG answer in detail",
    response_description="Step-by-step reasoning and CRAG explanation.",
)
async def rag_explain(
    payload: RAGExplainRequest,
    engine: AdvancedRAGSystem = Depends(get_rag_engine),
) -> RAGExplainResponse:
    """
    Return a detailed explanation / CRAG-style trace for a given question.

    This is primarily used by the internal console and power users.
    """
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    try:
        explanation: RAGExplainResponse = await engine.explain(payload)
        return explanation
    except Exception as exc:
        logger.exception("RAG explain failed with unexpected error")
        return RAGExplainResponse(
            question=question,
            steps=[],
            status="error",
            error_message="Internal RAG explanation error.",
            debug={"exception_type": type(exc).__name__},
        )


# --- Debug endpoint (for internal tooling) -----------------------------------


@router.post(
    "/debug",
    response_model=RAGDebugResponse,
    summary="Low-level debug information for a RAG query",
    response_description="Internal debug info (search results, prompts, scoring).",
)
async def rag_debug(
    payload: RAGDebugRequest,
    engine: AdvancedRAGSystem = Depends(get_rag_engine),
) -> RAGDebugResponse:
    """
    Internal-only endpoint exposing rich debug info for a query.

    Should be protected by authentication / role checks at a higher layer
    (e.g. dependency in `deps.py`) so that only admins / internal tools can
    access it.
    """
    question = (payload.question or "").strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question must not be empty.",
        )

    try:
        debug_info: RAGDebugResponse = await engine.debug(payload)
        return debug_info
    except Exception as exc:
        logger.exception("RAG debug failed with unexpected error")
        return RAGDebugResponse(
            question=question,
            status="error",
            error_message="Internal RAG debug error.",
            search_results=[],
            raw_prompts={},
            scoring={},
            internal_errors=[{"type": type(exc).__name__, "message": str(exc)}],
        )
