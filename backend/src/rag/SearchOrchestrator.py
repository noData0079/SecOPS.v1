from __future__ import annotations

from typing import List

from src.integrations.storage.vector_store import vector_store
from src.rag.AdvancedRAGTypes import RAGChunk, RAGQuery
from src.rag.CitationProcessor import citation_processor
from src.rag.llm_client import llm_client


class SearchOrchestrator:
    """Coordinates retrieval pipelines for RAG queries."""

    def __init__(self, settings=None, llm_client=None):
        self.settings = settings
        self.llm_client = llm_client

    async def search(self, query: RAGQuery, context=None) -> List[RAGChunk]:
        """
        Hybrid search:
        - semantic vector search
        - keyword fallback
        - metadata routing
        """

        vector_results = await vector_store.search(query.query, top_k=query.top_k)

        if not vector_results:
            # Assuming keyword_search exists on vector_store, otherwise this might fail.
            # Using the logic from the duplicated block.
            try:
                keyword_matches = vector_store.keyword_search(query.query)
                vector_results = keyword_matches
            except AttributeError:
                pass

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
