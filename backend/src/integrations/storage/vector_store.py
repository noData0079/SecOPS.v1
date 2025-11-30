# backend/src/integrations/storage/vector_store.py

from __future__ import annotations

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from utils.config import Settings  # type: ignore[attr-defined]
from integrations.storage.supabase_client import (
    SupabaseClient,
    get_supabase_client,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public contract
# ---------------------------------------------------------------------------


class VectorStore(ABC):
    """
    Abstract vector/semantic store interface.

    Expected by rag.SearchOrchestrator:

        async def search(
            *,
            namespace: str,
            query: str,
            top_k: int,
            filters: Optional[Dict[str, Any]] = None,
        ) -> List[Dict[str, Any]]:
            # returns a list of "hits":
            # {
            #   "id": "chunk-id",
            #   "content": "text snippet",
            #   "score": float,
            #   "metadata": {...},
            # }

    We ALSO expose a basic upsert API for indexing jobs:

        async def upsert_documents(
            *,
            namespace: str,
            documents: List[Dict[str, Any]],
        ) -> None:

    where each document is:
        {
          "id": str (optional; if missing, server will generate one),
          "content": str,
          "metadata": dict (optional),
        }
    """

    @abstractmethod
    async def search(
        self,
        *,
        namespace: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_documents(
        self,
        *,
        namespace: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mock / in-memory implementation (safe default)
# ---------------------------------------------------------------------------


class MockVectorStore(VectorStore):
    """
    Simple in-memory implementation for local development and tests.

    It does NOT perform real vector similarity – just returns documents
    stored under the given namespace in insertion order, up to top_k,
    with a dummy score. That is enough to keep the RAG pipeline working
    in environments where no real vector DB is configured.
    """

    def __init__(self) -> None:
        # namespace -> list[doc]
        self._store: Dict[str, List[Dict[str, Any]]] = {}

        logger.info(
            "MockVectorStore initialized. This is suitable for local dev, "
            "but not for production semantic search."
        )

    async def search(
        self,
        *,
        namespace: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        docs = list(self._store.get(namespace, []))

        # Very naive filtering: if filters provided, require exact metadata match
        if filters:
            def matches(doc: Dict[str, Any]) -> bool:
                meta = doc.get("metadata") or {}
                return all(meta.get(k) == v for k, v in filters.items())
            docs = [d for d in docs if matches(d)]

        # We ignore the query for now; a future version could implement simple
        # keyword scoring. For now, just return the most recent docs.
        docs = list(reversed(docs))  # newest first

        hits: List[Dict[str, Any]] = []
        for d in docs[:top_k]:
            hits.append(
                {
                    "id": d["id"],
                    "content": d["content"],
                    "score": 1.0,  # dummy score
                    "metadata": d.get("metadata") or {},
                }
            )

        return hits

    async def upsert_documents(
        self,
        *,
        namespace: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        if namespace not in self._store:
            self._store[namespace] = []

        for doc in documents:
            if "id" not in doc or not doc["id"]:
                doc["id"] = str(uuid.uuid4())

            # Remove any existing doc with same id
            self._store[namespace] = [
                d for d in self._store[namespace] if d["id"] != doc["id"]
            ]
            self._store[namespace].append(
                {
                    "id": doc["id"],
                    "content": doc.get("content") or "",
                    "metadata": doc.get("metadata") or {},
                }
            )


# ---------------------------------------------------------------------------
# Supabase-based implementation (pgvector / custom RPC)
# ---------------------------------------------------------------------------


class SupabaseVectorStore(VectorStore):
    """
    Vector/semantic store backed by Supabase.

    This implementation is deliberately flexible so you can evolve
    your schema and search strategy without touching the Python code.

    Two modes:

      1) RPC mode (recommended for production):
         - Configure a Postgres function for vector search, e.g.:

           CREATE OR REPLACE FUNCTION match_rag_documents(
               namespace text,
               query_text text,
               match_count int,
               filters jsonb DEFAULT '{}'::jsonb
           )
           RETURNS TABLE (
               id text,
               content text,
               score double precision,
               metadata jsonb
           )
           ...

         - Set env / settings:

           VECTOR_STORE_SUPABASE_RPC = "match_rag_documents"
           VECTOR_STORE_SUPABASE_TABLE = "rag_documents"    -- used only for upsert

         - search() calls /rest/v1/rpc/match_rag_documents.

      2) Fallback "keyword-ish" mode:
         - If RPC name is not configured, search() will:
           - select recent rows from a table (default: rag_documents)
           - return them with a dummy score (no real similarity).

    Table expectation for upsert:
      - table name = VECTOR_STORE_SUPABASE_TABLE (default "rag_documents")
      - columns:
          id          text (PK or unique)
          namespace   text
          content     text
          metadata    jsonb
    """

    def __init__(self, settings: Settings, supabase: SupabaseClient) -> None:
        self.settings = settings
        self.supabase = supabase

        self.table_name: str = (
            getattr(settings, "VECTOR_STORE_SUPABASE_TABLE", None)
            or os.getenv("VECTOR_STORE_SUPABASE_TABLE")
            or "rag_documents"
        )

        self.rpc_function: Optional[str] = (
            getattr(settings, "VECTOR_STORE_SUPABASE_RPC", None)
            or os.getenv("VECTOR_STORE_SUPABASE_RPC")
        )

        if self.rpc_function:
            logger.info(
                "SupabaseVectorStore initialized in RPC mode (function=%s, table=%s)",
                self.rpc_function,
                self.table_name,
            )
        else:
            logger.info(
                "SupabaseVectorStore initialized in fallback mode (no RPC). "
                "search() will NOT perform semantic similarity – only recent docs "
                "per namespace will be returned."
            )

    # --------------------------- public API -----------------------------

    async def search(
        self,
        *,
        namespace: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self.rpc_function:
            return await self._search_via_rpc(
                namespace=namespace,
                query=query,
                top_k=top_k,
                filters=filters,
            )

        # Fallback: simple "recent docs in namespace", ignoring query.
        return await self._search_recent_docs(
            namespace=namespace,
            top_k=top_k,
            filters=filters,
        )

    async def upsert_documents(
        self,
        *,
        namespace: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        if not documents:
            return

        rows = []
        for doc in documents:
            doc_id = doc.get("id") or str(uuid.uuid4())
            content = doc.get("content") or ""
            metadata = doc.get("metadata") or {}

            rows.append(
                {
                    "id": doc_id,
                    "namespace": namespace,
                    "content": content,
                    "metadata": json.dumps(metadata),
                }
            )

        try:
            # Use upsert on "id" so updates overwrite previous content.
            await self.supabase.upsert(
                self.table_name,
                rows,
                on_conflict="id",
                returning="minimal",
            )
        except Exception:
            logger.exception(
                "SupabaseVectorStore: upsert_documents failed for namespace=%s", namespace
            )

    # --------------------------- internals ------------------------------

    async def _search_via_rpc(
        self,
        *,
        namespace: str,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Call a Postgres RPC function that implements vector search.

        Expects RPC response:
          [
            {
              "id": "chunk-id",
              "content": "text snippet",
              "score": 0.87,
              "metadata": { ... },
            },
            ...
          ]
        """
        if not self.supabase._enabled:  # type: ignore[attr-defined]
            logger.debug("SupabaseVectorStore._search_via_rpc: Supabase disabled")
            return []

        # Use the raw REST /rpc endpoint via SupabaseClient's underlying client.
        # We don't add a dedicated method on SupabaseClient for RPC to keep it small;
        # instead we call the REST path directly here.
        try:
            client = await self.supabase._get_client()  # type: ignore[attr-defined]
        except Exception:
            logger.exception("SupabaseVectorStore: failed to get Supabase client")
            return []

        payload = {
            "namespace": namespace,
            "query_text": query,
            "match_count": top_k,
            "filters": filters or {},
        }

        try:
            resp = await client.post(
                f"/rest/v1/rpc/{self.rpc_function}",
                content=json.dumps(payload),
            )
        except Exception:
            logger.exception("SupabaseVectorStore: error calling RPC %s", self.rpc_function)
            return []

        if resp.status_code >= 400:
            logger.warning(
                "SupabaseVectorStore: RPC %s failed status=%s body=%s",
                self.rpc_function,
                resp.status_code,
                resp.text[:500],
            )
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.error(
                "SupabaseVectorStore: RPC %s returned non-JSON response",
                self.rpc_function,
            )
            return []

        if not isinstance(data, list):
            logger.warning(
                "SupabaseVectorStore: RPC %s returned non-list JSON %r",
                self.rpc_function,
                type(data),
            )
            return []

        hits: List[Dict[str, Any]] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            hit_id = str(row.get("id") or "")
            content = (row.get("content") or "").strip()
            score = float(row.get("score") or 0.0)
            meta = row.get("metadata") or {}
            if not isinstance(meta, dict):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            if not hit_id or not content:
                continue

            hits.append(
                {
                    "id": hit_id,
                    "content": content,
                    "score": score,
                    "metadata": meta,
                }
            )

        return hits

    async def _search_recent_docs(
        self,
        *,
        namespace: str,
        top_k: int,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fallback search if no RPC is configured.

        This is NOT real semantic search. It simply fetches recent documents
        in the given namespace and returns them with a dummy score.

        For better results, configure VECTOR_STORE_SUPABASE_RPC and a
        proper pgvector-based function.
        """
        if not self.supabase._enabled:  # type: ignore[attr-defined]
            logger.debug("SupabaseVectorStore._search_recent_docs: Supabase disabled")
            return []

        query_filters: Dict[str, Any] = {"namespace": namespace}

        # We ignore arbitrary filters here for simplicity; if you need more,
        # you can extend this method or prefer RPC mode instead.
        try:
            rows = await self.supabase.select(
                self.table_name,
                columns="id,namespace,content,metadata",
                filters=query_filters,
                limit=top_k,
            )
        except Exception:
            logger.exception(
                "SupabaseVectorStore: fallback select failed for namespace=%s", namespace
            )
            return []

        hits: List[Dict[str, Any]] = []
        for row in rows:
            hit_id = str(row.get("id") or "")
            content = (row.get("content") or "").strip()
            meta = row.get("metadata") or {}
            if not isinstance(meta, dict):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            if not hit_id or not content:
                continue

            hits.append(
                {
                    "id": hit_id,
                    "content": content,
                    "score": 1.0,  # dummy score
                    "metadata": meta,
                }
            )

        return hits


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_vector_store(settings: Settings) -> VectorStore:
    """
    Factory used by rag.SearchOrchestrator.

    Configuration:

      VECTOR_STORE_BACKEND = "supabase" | "mock"

    Defaults to "mock" for safety. For production, set:

      VECTOR_STORE_BACKEND = "supabase"
      SUPABASE_URL = ...
      SUPABASE_SERVICE_ROLE / SUPABASE_ANON_KEY = ...
      VECTOR_STORE_SUPABASE_TABLE = "rag_documents"         (optional)
      VECTOR_STORE_SUPABASE_RPC   = "match_rag_documents"   (optional but recommended)

    Example usage in other modules:

        from integrations.storage.vector_store import get_vector_store
        from utils.config import settings

        vs = get_vector_store(settings)
        hits = await vs.search(namespace="org-123", query="TLS misconfig", top_k=5)
    """
    backend = (
        getattr(settings, "VECTOR_STORE_BACKEND", None)
        or os.getenv("VECTOR_STORE_BACKEND")
        or "mock"
    ).lower()

    if backend == "supabase":
        supabase = get_supabase_client(settings)
        return SupabaseVectorStore(settings=settings, supabase=supabase)

    # Default
    return MockVectorStore()
