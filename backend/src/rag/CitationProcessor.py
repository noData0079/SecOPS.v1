# backend/src/rag/CitationProcessor.py

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from api.schemas.rag import RAGSource  # Pydantic DTO for API responses
from rag.AdvancedRAGTypes import (
    RAGAnswer,
    RetrievedContext,
    RetrievedSource,
)

logger = logging.getLogger(__name__)


class CitationProcessor:
    """
    Responsible for turning internal retrieval metadata into API-facing sources.

    Current behavior (MVP):
      - Does NOT modify the answer text (no inline [1], [2] markers yet).
      - Converts RetrievedSource objects into RAGSource DTOs.
      - Adds a short snippet per source using its most relevant chunk.
      - Optionally annotates sources with section headings that referenced them
        (if RAGAnswer.sections.citation_source_ids are populated).

    This is intentionally simple and deterministic. You can later extend it to:
      - inject inline markers into the answer text,
      - rank / filter sources more aggressively,
      - or produce per-paragraph citation metadata.
    """

    def process(
        self,
        *,
        answer: RAGAnswer,
        retrieved: RetrievedContext,
    ) -> Dict[str, Any]:
        """
        Convert answer + retrieved context into:
        {
          "text": <final answer text>,
          "sources": List[RAGSource],
        }
        """
        text = answer.primary_text()
        sources = self._build_sources_payload(answer=answer, retrieved=retrieved)

        return {
            "text": text,
            "sources": sources,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_sources_payload(
        self,
        *,
        answer: RAGAnswer,
        retrieved: RetrievedContext,
    ) -> List[RAGSource]:
        """
        Build the list of RAGSource DTOs for the API layer.

        Strategy:
        - Take all RetrievedSource objects.
        - For each, compute a snippet from its highest-scoring chunk.
        - Optionally record which answer sections referenced each source.
        """
        if not retrieved.sources:
            return []

        # Map source_id -> RetrievedSource
        source_by_id: Dict[str, RetrievedSource] = {
            src.id: src for src in retrieved.sources
        }

        # Compute which sections referenced which source ids, if any
        section_map: Dict[str, List[str]] = self._compute_section_map(answer=answer)

        # Build API sources
        api_sources: List[RAGSource] = []
        for src_id, src in source_by_id.items():
            snippet = self._best_snippet_for_source(src)

            # Merge metadata with section usage
            metadata = dict(src.metadata or {})
            if src_id in section_map:
                metadata["referenced_in_sections"] = section_map[src_id]

            # Try to infer a usable URI / title from metadata if missing
            uri = src.uri or metadata.get("url") or metadata.get("uri")
            title = src.title or metadata.get("title") or metadata.get("name")

            api_sources.append(
                RAGSource(
                    id=src.id,
                    source_type=src.source_type,
                    title=title,
                    uri=uri,
                    score=src.score,
                    snippet=snippet,
                    metadata=metadata,
                )
            )

        # Optionally: sort by score (highest first) and truncate to a sane number
        api_sources.sort(key=lambda s: (s.score or 0.0), reverse=True)
        return api_sources[:20]

    def _best_snippet_for_source(self, src: RetrievedSource) -> Optional[str]:
        """
        Choose a short representative snippet for this source.

        For now:
        - pick the highest-scoring chunk attached to the source (if any),
        - fallback to the first chunk,
        - truncate to ~400 characters for readability.
        """
        chunks = src.chunks or []
        if not chunks:
            return None

        # Pick by score descending
        chunks_sorted = sorted(chunks, key=lambda c: c.score, reverse=True)
        top_chunk = chunks_sorted[0]

        text = (top_chunk.text or "").strip()
        if not text:
            return None

        max_len = 400
        if len(text) <= max_len:
            return text

        return text[: max_len - 3].rstrip() + "..."

    def _compute_section_map(self, answer: RAGAnswer) -> Dict[str, List[str]]:
        """
        Build a mapping: source_id -> list of section headings that referenced it.

        We rely on RAGSection.citation_source_ids, which the synthesizer
        may or may not populate. If empty, we simply return {}.
        """
        mapping: Dict[str, List[str]] = {}

        if not answer.sections:
            return mapping

        for section in answer.sections:
            heading = section.heading
            for sid in section.citation_source_ids:
                if not sid:
                    continue
                if sid not in mapping:
                    mapping[sid] = []
                if heading not in mapping[sid]:
                    mapping[sid].append(heading)

        return mapping
