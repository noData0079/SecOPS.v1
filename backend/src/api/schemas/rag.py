# backend/src/api/schemas/rag.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Common submodels
# ---------------------------------------------------------------------------


class RAGUsage(BaseModel):
    """
    LLM token usage for a single RAG call.
    """

    input_tokens: int = Field(0, ge=0)
    output_tokens: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)


class RAGCitation(BaseModel):
    """
    A single citation / evidence item used for the answer.

    Flexible enough to support:
    - web pages
    - code files
    - config resources
    - internal docs
    """

    id: Optional[str] = Field(
        default=None,
        description="Internal identifier (e.g., doc id, URL hash).",
    )
    title: Optional[str] = Field(
        default=None,
        description="Human-readable title of the source.",
    )
    url: Optional[str] = Field(
        default=None,
        description="Canonical URL or resource locator.",
    )
    snippet: Optional[str] = Field(
        default=None,
        description="Relevant snippet or excerpt used in the answer.",
    )
    source_type: Optional[str] = Field(
        default=None,
        description="Type of source: web, code, config, log, cve, kb, etc.",
    )
    trust_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Normalized trust score assigned by the engine.",
    )
    rank: Optional[int] = Field(
        default=None,
        ge=0,
        description="Rank/order among all retrieved sources.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider- or engine-specific metadata.",
    )


# ---------------------------------------------------------------------------
# /api/rag/query
# ---------------------------------------------------------------------------


class RAGQueryRequest(BaseModel):
    """
    Input DTO for the main RAG query endpoint.
    """

    question: str = Field(..., min_length=1, description="User question / query.")
    intent: Optional[str] = Field(
        default="auto",
        description="Optional intent hint: auto, security, ops, code, etc.",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional caller user id (for audit / personalization).",
    )
    org_id: Optional[str] = Field(
        default=None,
        description="Optional organization id (multi-tenant context).",
    )
    # Optional additional context payload (e.g. live object, config, log slice)
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional structured context for the query.",
    )

    class Config:
        extra = "ignore"


class RAGQueryResponse(BaseModel):
    """
    Output DTO for the main RAG query endpoint.

    This is what your frontend and other services consume.
    """

    answer: str = Field(
        "",
        description="Final synthesized answer text.",
    )
    intent: str = Field(
        "auto",
        description="Resolved intent: auto, security, ops, etc.",
    )

    citations: List[RAGCitation] = Field(
        default_factory=list,
        description="List of citations / evidence supporting the answer.",
    )

    usage: Optional[RAGUsage] = Field(
        default=None,
        description="LLM token usage for this call, if available.",
    )

    latency_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="End-to-end latency in milliseconds.",
    )

    status: str = Field(
        "ok",
        description="Status of the query: ok, error, partial, etc.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Human-readable error message if status != ok.",
    )

    debug: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional debug info (prompt ids, trust metrics, provider/model, "
            "billing details). Not guaranteed to be stable."
        ),
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this response object was created.",
    )

    class Config:
        extra = "ignore"
        arbitrary_types_allowed = True


# ---------------------------------------------------------------------------
# /api/rag/explain  (CRAG / reasoning view)
# ---------------------------------------------------------------------------


class ExplainStep(BaseModel):
    """
    A single step in the CRAG / reasoning trace.
    """

    name: str = Field(
        ...,
        description="Short name of the step (e.g., 'retrieve', 'filter', 'synthesize').",
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of what happened in this step.",
    )
    raw_prompt: Optional[str] = Field(
        default=None,
        description="Raw prompt sent to the LLM for this step, if applicable.",
    )
    raw_output: Optional[str] = Field(
        default=None,
        description="Raw model output for this step, if applicable.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary engine-specific metadata (scores, timings, etc.).",
    )


class RAGExplainRequest(BaseModel):
    """
    Input DTO for /api/rag/explain.

    Typically mirrors RAGQueryRequest but can be more explicit about options.
    """

    question: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    org_id: Optional[str] = None

    class Config:
        extra = "ignore"


class RAGExplainResponse(BaseModel):
    """
    Detailed explanation / CRAG trace for a given question.
    """

    question: str = Field(..., description="Original question being explained.")
    steps: List[ExplainStep] = Field(
        default_factory=list,
        description="Ordered list of reasoning / pipeline steps.",
    )
    status: str = Field(
        "ok",
        description="Status of explanation: ok, error, partial, etc.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if explanation failed.",
    )
    debug: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional, engine-specific debug info.",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# /api/rag/debug  (internal debug endpoint)
# ---------------------------------------------------------------------------


class DebugSearchResult(BaseModel):
    """
    Low-level representation of a single retrieved search result.

    Intended for internal console / engineers, not end-users.
    """

    provider: Optional[str] = Field(
        default=None,
        description="Search provider: google, bing, cve_api, internal, etc.",
    )
    title: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    snippet: Optional[str] = Field(default=None)
    score: Optional[float] = Field(
        default=None,
        description="Raw retrieval score from the search provider.",
    )
    trust_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Engine-assigned trust score.",
    )
    rank: Optional[int] = Field(
        default=None,
        ge=0,
        description="Position in the ranked list.",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InternalErrorInfo(BaseModel):
    """
    Structured description of an internal error during debug run.
    """

    type: str = Field(..., description="Exception class name.")
    message: str = Field(..., description="Exception message.")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional extra details / context.",
    )


class RAGDebugRequest(BaseModel):
    """
    Input DTO for /api/rag/debug.
    """

    question: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    org_id: Optional[str] = None

    # Optional flags to control how much debug info to include
    include_prompts: bool = Field(
        default=True,
        description="If true, includes raw prompts in the response.",
    )
    include_scoring: bool = Field(
        default=True,
        description="If true, includes scoring/trust information.",
    )
    include_search_results: bool = Field(
        default=True,
        description="If true, includes raw search results.",
    )

    class Config:
        extra = "ignore"


class RAGDebugResponse(BaseModel):
    """
    Low-level debug information about a RAG query.

    Not meant for end users; used by internal console & engineers.
    """

    question: str = Field(..., description="Original question.")
    status: str = Field(
        "ok",
        description="Status of debug run: ok, error, partial, etc.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if debug run failed.",
    )

    search_results: List[DebugSearchResult] = Field(
        default_factory=list,
        description="Raw or semi-processed search results.",
    )
    raw_prompts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Map of prompt names/ids → raw prompt text.",
    )
    scoring: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any scoring / ranking / trust metrics.",
    )
    internal_errors: List[InternalErrorInfo] = Field(
        default_factory=list,
        description="Any internal errors encountered along the pipeline.",
    )

    class Config:
        extra = "ignore"
