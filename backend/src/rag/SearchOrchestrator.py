# backend/src/rag/SearchOrchestrator.py

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rag.AdvancedRAGTypes import (
    RAGQueryContext,
    RetrievedChunk,
    RetrievedContext,
    RetrievedSource,
)
from rag.llm_client import LLMClient
from integrations.storage.vector_store import get_vector_store  # to be implemented

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """
    Orchestrates retrieval for the Advanced RAG system.

    Responsibilities (MVP):
      - optional query expansion using LLMClient
      - perform semantic search against a pluggable vector store
      - normalize hits into RetrievedChunk + RetrievedSource
      - return a RetrievedContext object to the synthesizer

    The vector store implementation is abstracted behind
    integrations.storage.vector_store.get_vector_store(settings),
    which should return an object with:

        async def search(
            self,
            *,
            namespace: str,
            query: str,
            top_k: int,
            filters: Optional[Dict[str, Any]] = None,
        ) -> List[Dict[str, Any]]:

    where each hit dict is expected to look like:

        {
          "id": "chunk-id",
          "content": "text snippet",
          "score": 0.87,
          "metadata": {
              "source_id": "doc-123",
              "source_type": "document" | "code" | "log" | "web",
              "title": "My Document",
              "uri": "https://example.com",
              ... anything else ...
          }
        }
    """

    def __init__(self, settings: Any, llm_client: LLMClient) -> None:
        self.settings = settings
        self.llm_client = llm_client

        # Vector store abstraction (qdrant/supabase/pgvector/mock)
        self.vector_store = get_vector_store(settings=settings)

        # Feature flags / knobs (can be set in settings later)
        self.enable_query_expansion: bool = getattr(
            settings, "RAG_ENABLE_QUERY_EXPANSION", True
        )
        self.max_expansion_variants: int = getattr(
            settings, "RAG_MAX_EXPANSION_VARIANTS", 2
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(
        self,
        *,
        query: str,
        context: RAGQueryContext,
    ) -> RetrievedContext:
        """
        Main entrypoint called by AdvancedRAGSystem.

        Steps:
          1) Optionally expand the query into paraphrases.
          2) Run vector search for each variant.
          3) Merge and normalize hits into chunks + sources.
        """
        expanded_queries = await self._expand_queries_if_needed(query=query, context=context)
        queries_to_run = [query] + expanded_queries

        all_hits: List[Dict[str, Any]] = []

        for q in queries_to_run:
            try:
                hits = await self._vector_search(
                    query=q,
                    context=context,
                    top_k=context.top_k,
                )
                all_hits.extend(hits)
            except Exception as exc:
                logger.exception("Vector search failed for query variant: %s", q)
                # We continue with other variants; failure on one variant
                # should not kill the entire request.
                continue

        chunks, sources = self._normalize_hits(
            hits=all_hits,
            context=context,
        )

        return RetrievedContext(
            query=query,
            expanded_queries=expanded_queries,
            chunks=chunks,
            sources=sources,
        )

    # ------------------------------------------------------------------
    # Query expansion
    # ------------------------------------------------------------------

    async def _expand_queries_if_needed(
        self,
        *,
        query: str,
        context: RAGQueryContext,
    ) -> List[str]:
        """
        Optionally generate paraphrased variants of the query.

        Uses the LLM to propose a few alternative phrasings, which can
        improve recall for semantic search in some cases.

        This is intentionally conservative:
          - disabled if feature flag is off
          - limited number of variants
          - safe fallback on any error
        """
        if not self.enable_query_expansion:
            return []

        variants: List[str] = []
        max_variants = max(0, self.max_expansion_variants)

        if max_variants == 0:
            return variants

        prompt = (
            "You are helping improve search recall. Given the user's question, "
            "generate a few alternative phrasings that are semantically equivalent "
            "but phrased differently. Return them as a plain numbered list.\n\n"
            f"Question: {query}"
        )

        try:
            messages = [
                {"role": "system", "content": "You generate search query paraphrases."},
                {"role": "user", "content": prompt},
            ]
            response = await self.llm_client.chat(
                messages=messages,
                model=getattr(self.settings, "RAG_EXPANSION_MODEL", None),
                max_tokens=128,
                temperature=0.5,
            )

            text = (response.get("content") or "").strip()
            for line in text.splitlines():
                # Accept lines like "1. some paraphrase" or "- some paraphrase"
                line = line.strip()
                if not line:
                    continue
                # Remove simple list markers
                if line[0].isdigit() and "." in line:
                    line = line.split(".", 1)[1].strip()
                elif line.startswith(("-", "*")):
                    line = line[1:].strip()

                if line and line.lower() != query.lower():
                    variants.append(line)
                if len(variants) >= max_variants:
                    break
        except Exception:
            logger.exception("Query expansion failed, continuing with original query only")
            return []

        return variants

    # ------------------------------------------------------------------
    # Vector search
    # ------------------------------------------------------------------

    async def _vector_search(
        self,
        *,
        query: str,
        context: RAGQueryContext,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        Call the underlying vector store.

        The vector store is responsible for:
          - embedding the query (if needed)
          - performing similarity search
          - returning hits as dicts matching the expected shape
        """
        namespace = context.org_id  # simple multi-tenant isolation
        filters: Dict[str, Any] = {}

        # You can route based on mode if desired, e.g.:
        #   filters["mode"] = context.mode
        # or choose a specific collection per mode.
        if context.mode:
            filters["mode"] = context.mode

        hits = await self.vector_store.search(
            namespace=namespace,
            query=query,
            top_k=top_k,
            filters=filters or None,
        )
        return hits or []

    # ------------------------------------------------------------------
    # Normalization of hits
    # ------------------------------------------------------------------

    def _normalize_hits(
        self,
        *,
        hits: List[Dict[str, Any]],
        context: RAGQueryContext,
    ) -> (List[RetrievedChunk], List[RetrievedSource]):
        """
        Convert raw vector hits into our internal retrieval types.

        - Deduplicates chunks by id.
        - Aggregates chunks by source_id into RetrievedSource objects.
        """
        if not hits:
            return [], []

        chunk_by_id: Dict[str, RetrievedChunk] = {}
        source_by_id: Dict[str, RetrievedSource] = {}

        for hit in hits:
            if not hit:
                continue

            hit_id = str(hit.get("id") or "")
            content = (hit.get("content") or "").strip()
            score = float(hit.get("score") or 0.0)
            meta: Dict[str, Any] = hit.get("metadata") or {}

            if not hit_id:
                # Ensure we always have some id; not ideal but safe
                hit_id = f"chunk-{len(chunk_by_id) + 1}"

            if not content:
                # Skip empty snippets – they don't help the model
                continue

            source_id = str(
                meta.get("source_id")
                or meta.get("doc_id")
                or meta.get("file_id")
                or "unknown-source"
            )

            source_type = str(meta.get("source_type") or "document")
            title = meta.get("title") or meta.get("name")
            uri = meta.get("uri") or meta.get("url")

            # Build or update RetrievedSource
            if source_id not in source_by_id:
                source_by_id[source_id] = RetrievedSource(
                    id=source_id,
                    source_type=source_type,
                    title=title,
                    uri=uri,
                    score=score,
                    metadata={k: v for k, v in meta.items() if k not in {"source_id", "source_type"}},
                    chunks=[],
                )
            else:
                # Keep highest score
                existing_score = source_by_id[source_id].score or 0.0
                if score > existing_score:
                    source_by_id[source_id].score = score

            # Build RetrievedChunk
            if hit_id in chunk_by_id:
                # Already seen this chunk; keep the highest score
                if score > chunk_by_id[hit_id].score:
                    chunk_by_id[hit_id].score = score
                continue

            chunk = RetrievedChunk(
                id=hit_id,
                source_id=source_id,
                text=content,
                score=score,
                metadata=meta,
            )

            chunk_by_id[hit_id] = chunk
            source_by_id[source_id].chunks.append(chunk)

        chunks = list(chunk_by_id.values())
        sources = list(source_by_id.values())

        # Sort chunks + sources by score descending for consistency
        chunks.sort(key=lambda c: c.score, reverse=True)
        sources.sort(key=lambda s: (s.score or 0.0), reverse=True)

        return chunks, sources
