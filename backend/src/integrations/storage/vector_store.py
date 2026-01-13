from __future__ import annotations

import os
from typing import List, Optional, Dict, Any

import httpx

from src.rag.AdvancedRAGTypes import RAGChunk

# Check environment to decide which store to use
USE_QDRANT = os.getenv("USE_QDRANT", "true").lower() == "true"
QDRANT_URL = os.getenv("QDRANT_URL")

if USE_QDRANT or QDRANT_URL:
    from src.integrations.storage.qdrant_store import qdrant_store_instance
    # We alias it to vector_store so other modules pick it up transparently
    vector_store = qdrant_store_instance
else:
    # Fallback to Supabase implementation
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

    class SupabaseVectorStore:
        """Lightweight Supabase vector store wrapper with safe fallbacks."""

        async def search(self, query: str, top_k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List[RAGChunk]:
            if not SUPABASE_URL or not SUPABASE_KEY:
                return []

            url = f"{SUPABASE_URL}/rest/v1/rpc/match_documents"
            headers = {
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            }

            # Supabase match_documents typically takes query_embedding, match_threshold, match_count, filter
            # Here we are using a simplified version that takes query_text if using a hybrid search function
            # OR we assume the RPC function handles embedding generation (unlikely standard behavior but matched previous code).
            # Note: The previous code sent `query_text`.
            # We add `filter` support only if filters are provided to avoid breaking RPCs that don't expect it.

            payload = {"query_text": query, "match_count": top_k}
            if filters:
                payload["filter"] = filters

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            return [
                RAGChunk(
                    id=str(row.get("id", i)),
                    text=row.get("content", ""),
                    score=float(row.get("similarity", 0.0)),
                    source=row.get("source", "unknown"),
                    metadata=row.get("metadata", {}),
                )
                for i, row in enumerate(data)
            ]

        def keyword_search(self, query: str) -> List[RAGChunk]:
            # Placeholder keyword search for environments without Supabase
            return []

    vector_store = SupabaseVectorStore()
