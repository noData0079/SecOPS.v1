# backend/src/rag/AdvancedRAGTypes.py

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Query context – shared across retrieval & synthesis
# ---------------------------------------------------------------------------


@dataclass
class RAGQueryContext:
    """
    Execution context for a single RAG query.

    This object is passed down into:
    - SearchOrchestrator.search(...)
    - RAGSynthesizer.synthesize(...)

    so both layers can make decisions based on:
    - org_id / user_id
    - mode (security, code, default, etc.)
    - retrieval depth (top_k)
    - generation budget (max_tokens)
    - strictness of source requirements
    """

    org_id: str
    user_id: str

    mode: str = "default"
    top_k: int = 8
    max_tokens: int = 512

    strict_sources: bool = False
    debug: bool = False

    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Retrieval structures – chunks & sources
# ---------------------------------------------------------------------------


@dataclass
class RetrievedChunk:
    """
    Single snippet of text or code retrieved from some source.

    - id: internal identifier for this chunk
    - source_id: identifier of the parent source (document, repo, log stream)
    - text: the content given to the LLM as context
    - score: relevance score (higher is more relevant)
    - metadata: arbitrary extra data (e.g. file path, line numbers, timestamps)
    """

    id: str
    source_id: str
    text: str
    score: float

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievedSource:
    """
    Logical source that produced one or more chunks.

    Example types:
    - 'document'  (knowledge base docs)
    - 'code'      (repo files)
    - 'log'       (logs / events)
    - 'web'       (live web search)
    """

    id: str
    source_type: str
    title: Optional[str] = None
    uri: Optional[str] = None

    score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Chunks related to this source (optional, not always populated)
    chunks: List[RetrievedChunk] = field(default_factory=list)


@dataclass
class RetrievedContext:
    """
    Aggregated retrieval result for a query.

    - query: original user query
    - expanded_queries: optional query rewrites / paraphrases
    - chunks: list of retrieved chunks actually sent to the LLM
    - sources: normalized list of sources (used later for citations)
    """

    query: str
    expanded_queries: List[str] = field(default_factory=list)
    chunks: List[RetrievedChunk] = field(default_factory=list)
    sources: List[RetrievedSource] = field(default_factory=list)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        """
        Lightweight serialization for debugging or logging.
        """
        return {
            "query": self.query,
            "expanded_queries": list(self.expanded_queries),
            "chunk_count": len(self.chunks),
            "source_count": len(self.sources),
        }


# ---------------------------------------------------------------------------
# Answer / usage structures
# ---------------------------------------------------------------------------


@dataclass
class RAGUsage:
    """
    Normalized usage information for a single RAG answer.

    - model: underlying LLM model identifier
    - provider: logical provider name (openai, emergent, gemini, etc.)
    - prompt_tokens / completion_tokens / total_tokens: token counts if available
    - latency_ms: end-to-end LLM latency for the main generation call
    """

    model: Optional[str] = None
    provider: Optional[str] = None

    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None

    latency_ms: Optional[float] = None

    def as_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RAGSection:
    """
    Optional higher-level structure for segmenting an answer.

    - heading: section title (e.g. 'Summary', 'Root Cause', 'Fix')
    - content: text for this section
    - citation_source_ids: list of source ids primarily used in this section
    """

    heading: str
    content: str
    citation_source_ids: List[str] = field(default_factory=list)


@dataclass
class RAGAnswer:
    """
    Structured result returned by the RAGSynthesizer.

    - text: full answer text as it should be shown to the user
    - sections: optional structured breakdown of the answer
    - usage: token / model usage info
    - raw: optional provider-specific payload for logging or internal use
    """

    text: str
    sections: List[RAGSection] = field(default_factory=list)
    usage: Optional[RAGUsage] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def primary_text(self) -> str:
        """
        Returns the main answer text used by the API layer.

        For now this simply returns `text`, but this method makes it easy
        to change behavior (e.g. join sections) without touching callers.
        """
        return self.text
