# backend/src/rag/AdvancedRAGSystem.py

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import logging

from api.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
)
from rag.AdvancedRAGTypes import (
    RAGQueryContext,
    RetrievedContext,
    RAGAnswer,
)
from rag.SearchOrchestrator import SearchOrchestrator
from rag.RAGSynthesizer import RAGSynthesizer
from rag.CitationProcessor import CitationProcessor
from rag.llm_client import LLMClient
from utils.config import settings  # global settings instance

logger = logging.getLogger(__name__)


class AdvancedRAGSystem:
    """
    High-level Retrieval-Augmented Generation (RAG) engine.

    Responsibilities:
    - Build query context (org, user, mode, options)
    - Orchestrate multi-source retrieval (code, docs, logs, etc.)
    - Ask the LLM to synthesize a structured answer
    - Attach citations and normalize output into API DTOs

    This class is intentionally thin: most heavy logic lives in:
    - SearchOrchestrator: where & how to fetch context
    - RAGSynthesizer: how to prompt and structure the answer
    - CitationProcessor: how to map answer spans to sources
    - LLMClient: provider-agnostic LLM interface (OpenAI, Emergent, Gemini, etc.)
    """

    def __init__(self, app_settings: Any) -> None:
        self.settings = app_settings

        # Core LLM client used by search / synthesis
        self.llm_client = LLMClient(settings=self.settings)

        # Retrieval orchestrator (e.g., vector DB + live web + code search)
        self.search_orchestrator = SearchOrchestrator(
            settings=self.settings,
            llm_client=self.llm_client,
        )

        # Answer synthesizer that knows how to talk to the LLM
        self.synthesizer = RAGSynthesizer(
            settings=self.settings,
            llm_client=self.llm_client,
        )

        # Post-processing: citations, formatting, snippets
        self.citation_processor = CitationProcessor()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def answer_query(
        self,
        *,
        org_id: str,
        user_id: str,
        request: RAGQueryRequest,
    ) -> RAGQueryResponse:
        """
        Main entrypoint used by the /rag/query API route.

        - `org_id` and `user_id` come from auth / current user
        - `request` is the RAGQueryRequest DTO from the API layer
        """
        started_at = datetime.utcnow()
        logger.info(
            "RAG query started org_id=%s user_id=%s mode=%s",
            org_id,
            user_id,
            getattr(request, "mode", "default"),
        )

        # 1) Build query context
        qctx = self._build_query_context(
            org_id=org_id,
            user_id=user_id,
            request=request,
        )

        # 2) Retrieve context (multi-vector search, integrations, etc.)
        retrieved = await self._retrieve_context(
            query=request.query,
            context=qctx,
        )

        # 3) Synthesize answer with the LLM using retrieved context
        rag_answer = await self._synthesize_answer(
            query=request.query,
            retrieved=retrieved,
            context=qctx,
        )

        # 4) Attach citations & normalize for API
        final_text, sources_payload = self._attach_citations_and_sources(
            rag_answer=rag_answer,
            retrieved=retrieved,
        )

        # 5) Build usage + debug payloads
        usage = self._build_usage_payload(rag_answer=rag_answer)
        debug = self._build_debug_payload(
            request=request,
            context=qctx,
            retrieved=retrieved,
            rag_answer=rag_answer,
        ) if getattr(request, "debug", False) else None

        finished_at = datetime.utcnow()
        logger.info(
            "RAG query finished org_id=%s user_id=%s duration_ms=%.2f",
            org_id,
            user_id,
            (finished_at - started_at).total_seconds() * 1000.0,
        )

        # 6) Return as RAGQueryResponse DTO
        return RAGQueryResponse(
            answer=final_text,
            sources=sources_payload,
            mode=getattr(request, "mode", "default"),
            usage=usage,
            debug=debug,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_query_context(
        self,
        *,
        org_id: str,
        user_id: str,
        request: RAGQueryRequest,
    ) -> RAGQueryContext:
        """
        Build a context object passed through retrieval + synthesis.

        RAGQueryContext is defined in AdvancedRAGTypes.py and should minimally include:
        - org_id, user_id
        - mode (e.g. 'default', 'security', 'code')
        - top_k, max_tokens
        - any flags like `include_history` or `strict_sources`
        """
        mode = getattr(request, "mode", "default")
        top_k = getattr(request, "top_k", 8)
        max_tokens = getattr(request, "max_tokens", 512)
        strict_sources = getattr(request, "strict_sources", False)

        return RAGQueryContext(
            org_id=org_id,
            user_id=user_id,
            mode=mode,
            top_k=top_k,
            max_tokens=max_tokens,
            strict_sources=strict_sources,
            debug=getattr(request, "debug", False),
            metadata={
                "client": getattr(request, "client", None),
            },
        )

    async def _retrieve_context(
        self,
        *,
        query: str,
        context: RAGQueryContext,
    ) -> RetrievedContext:
        """
        Delegate to SearchOrchestrator to retrieve relevant context.

        SearchOrchestrator is responsible for:
        - query expansion / rewriting
        - hitting vector DBs / code search / documentation / logs / external APIs
        - returning a RetrievedContext structure with:
          - chunks: list of retrieved snippets
          - sources: normalized source descriptors
        """
        retrieved = await self.search_orchestrator.search(
            query=query,
            context=context,
        )
        return retrieved

    async def _synthesize_answer(
        self,
        *,
        query: str,
        retrieved: RetrievedContext,
        context: RAGQueryContext,
    ) -> RAGAnswer:
        """
        Call the RAGSynthesizer to generate an answer using the LLM.

        RAGSynthesizer is responsible for:
        - building the system + user prompts
        - structuring the answer (sections, bullets, code blocks, etc.)
        - returning a RAGAnswer object with:
          - text: final answer text (or skeleton)
          - sections / steps
          - usage (prompt_tokens, completion_tokens, model)
        """
        rag_answer = await self.synthesizer.synthesize(
            query=query,
            retrieved=retrieved,
            context=context,
        )
        return rag_answer

    def _attach_citations_and_sources(
        self,
        *,
        rag_answer: RAGAnswer,
        retrieved: RetrievedContext,
    ) -> Tuple[str, List[Any]]:
        """
        Use CitationProcessor to attach inline citations and build the
        final sources payload for the API.

        CitationProcessor should:
        - map answer spans / sections to retrieved chunks
        - build a list of API-facing source DTOs (api.schemas.rag.RAGSource)
        """
        processed = self.citation_processor.process(
            answer=rag_answer,
            retrieved=retrieved,
        )
        # `processed` is expected to be:
        # {
        #   "text": str,
        #   "sources": List[RAGSource]    # from api.schemas.rag
        # }
        final_text: str = processed["text"]
        sources_payload: List[Any] = processed["sources"]
        return final_text, sources_payload

    def _build_usage_payload(self, rag_answer: RAGAnswer) -> Dict[str, Any]:
        """
        Extract usage info (tokens, model, latency) from the RAGAnswer.

        RAGAnswer in AdvancedRAGTypes.py should expose .usage as a dict or
        a dataclass convertible via asdict().
        """
        usage = getattr(rag_answer, "usage", None)
        if usage is None:
            return {}

        # Support either dataclass or plain dict
        if hasattr(usage, "__dataclass_fields__"):
            return asdict(usage)  # type: ignore[arg-type]
        if isinstance(usage, dict):
            return usage

        # Fallback – something structured but safe
        return {"value": str(usage)}

    def _build_debug_payload(
        self,
        *,
        request: RAGQueryRequest,
        context: RAGQueryContext,
        retrieved: RetrievedContext,
        rag_answer: RAGAnswer,
    ) -> Dict[str, Any]:
        """
        Debug payload for advanced users / internal console.

        Only returned when request.debug == True.
        """
        # We keep this very lightweight to avoid leaking sensitive internals.
        # The actual structures (RAGQueryContext, RetrievedContext, RAGAnswer)
        # should be designed in AdvancedRAGTypes to be safe to inspect.
        try:
            sources_debug = [
                {
                    "id": getattr(s, "id", None),
                    "type": getattr(s, "source_type", None),
                    "title": getattr(s, "title", None),
                    "score": getattr(s, "score", None),
                }
                for s in getattr(retrieved, "sources", [])
            ]
        except Exception:
            sources_debug = []

        return {
            "mode": context.mode,
            "top_k": context.top_k,
            "max_tokens": context.max_tokens,
            "retrieved_chunks": getattr(retrieved, "chunk_count", None),
            "sources": sources_debug,
            "raw_usage": self._build_usage_payload(rag_answer),
        }


# ----------------------------------------------------------------------
# Singleton helper
# ----------------------------------------------------------------------

_rag_system: Optional[AdvancedRAGSystem] = None


def get_rag_system() -> AdvancedRAGSystem:
    """
    Lazily create a global AdvancedRAGSystem instance.

    This can be imported and used by the FastAPI router (routes/rag.py) as:

        from rag.AdvancedRAGSystem import get_rag_system
        rag_system = get_rag_system()
    """
    global _rag_system
    if _rag_system is None:
        logger.info("Initializing AdvancedRAGSystem singleton")
        _rag_system = AdvancedRAGSystem(app_settings=settings)
    return _rag_system
