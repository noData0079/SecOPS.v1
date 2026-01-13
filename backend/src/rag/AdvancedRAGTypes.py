from __future__ import annotations

from typing import List, Optional, Any, Dict

from pydantic import BaseModel


class RAGQuery(BaseModel):
    """Simple query container for the RAG pipeline."""

    query: str
    top_k: int = 8
    filters: Optional[dict] = None


class RAGChunk(BaseModel):
    """Normalized chunk returned from retrieval."""

    id: str
    text: str
    score: float
    source: str
    metadata: dict


class RAGResult(BaseModel):
    """Final synthesized result with citations."""

    query: str
    chunks: List[RAGChunk]
    synthesized_answer: str
    citations: List[dict]


class RAGQueryContext(BaseModel):
    """
    Context for a RAG query execution.
    Contains auth, config, and mode settings.
    """
    org_id: str
    user_id: str
    mode: str = "default"
    top_k: int = 8
    max_tokens: int = 512
    strict_sources: bool = False
    debug: bool = False
    metadata: Dict[str, Any] = {}


class RetrievedContext(BaseModel):
    """
    Standardized container for retrieval results.
    """
    chunks: List[RAGChunk] = []
    sources: List[Any] = []
    chunk_count: int = 0


class RAGAnswer(BaseModel):
    """
    Standardized structure for LLM-synthesized answers.
    """
    text: str
    usage: Optional[Dict[str, Any]] = None
    sections: Optional[List[Any]] = None
