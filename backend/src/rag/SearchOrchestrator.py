from __future__ import annotations

from typing import List

from backend.src.integrations.storage.vector_store import vector_store
from backend.src.rag.AdvancedRAGTypes import RAGChunk, RAGQuery
from backend.src.rag.CitationProcessor import citation_processor
from backend.src.rag.llm_client import llm_client


class SearchOrchestrator:
    async def search(self, query: RAGQuery) -> List[RAGChunk]:
        """
        Hybrid search:
        - semantic vector search
        - keyword fallback
        - metadata routing
        """

        vector_results = await vector_store.search(query.query, top_k=query.top_k)

        if not vector_results:
            keyword_matches = vector_store.keyword_search(query.query)
            vector_results = keyword_matches

        return citation_processor.merge_and_rank(vector_results)

    async def rag_explain_ci_failure(self, run_data: str):
        prompt = f"""
Explain this CI/CD failure in detail:

{run_data}

Return:
- High-level explanation
- Root cause
- Fix steps
- Risks
- How to prevent it
"""
        return await llm_client.ask(prompt)
from integrations.storage.vector_store import vector_store
from rag.AdvancedRAGTypes import RAGChunk, RAGQuery
from rag.CitationProcessor import citation_processor


class SearchOrchestrator:
    """Coordinates retrieval pipelines for RAG queries."""

    async def search(self, query: RAGQuery) -> List[RAGChunk]:
        vector_results = await vector_store.search(query.query, top_k=query.top_k)

        if not vector_results:
            vector_results = vector_store.keyword_search(query.query)

        return citation_processor.merge_and_rank(vector_results)


search_orchestrator = SearchOrchestrator()
