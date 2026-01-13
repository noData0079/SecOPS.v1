from __future__ import annotations

import os
import logging
from typing import List, Optional, Dict, Any

from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding

from src.rag.AdvancedRAGTypes import RAGChunk

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    """
    Qdrant-backed vector store with local FastEmbed embeddings.
    Supports 'Sovereign' architecture with client isolation via filters.
    """

    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        # Use :memory: if specifically requested, otherwise default to url
        if self.url == ":memory:":
             self.client = QdrantClient(location=":memory:")
        else:
             self.client = QdrantClient(url=self.url)

        self.collection_name = "sovereign_docs"
        # BAAI/bge-small-en-v1.5 is a good balance of speed/performance (384 dim)
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        # We ensure collection exists on startup to avoid runtime errors
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            if not self.client.collection_exists(self.collection_name):
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.warning(f"Could not ensure collection exists (might be connection error): {e}")

    async def search(self, query: str, top_k: int = 8, filters: Optional[Dict[str, Any]] = None) -> List[RAGChunk]:
        """
        Search for documents using vector similarity.

        Args:
            query: The user query string
            top_k: Number of results to return
            filters: Dictionary of metadata filters (e.g., {'client_id': '123'})
        """
        try:
            # Generate embedding locally
            # fastembed returns a generator, we get the first item
            query_vector = list(self.embedding_model.embed([query]))[0]

            # Build Qdrant filter
            query_filter = None
            if filters:
                must_conditions = []
                for key, value in filters.items():
                    # We assume equality match for filters
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
                if must_conditions:
                    query_filter = models.Filter(must=must_conditions)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(), # Convert numpy to list
                query_filter=query_filter,
                limit=top_k
            )

            return [
                RAGChunk(
                    id=str(res.id),
                    text=res.payload.get("text", "") if res.payload else "",
                    score=float(res.score),
                    source=res.payload.get("source", "unknown") if res.payload else "unknown",
                    metadata=res.payload or {}
                )
                for res in results
            ]
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def keyword_search(self, query: str) -> List[RAGChunk]:
        # Qdrant supports full text search but needs configuration.
        # For now return empty or implement basic logic if needed.
        return []

# Create a global instance, but it might not be used if we stick to Supabase default
# This will be selectively imported by vector_store.py
qdrant_store_instance = QdrantVectorStore()
