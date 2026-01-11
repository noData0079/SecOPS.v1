from __future__ import annotations

from src.rag.AdvancedRAGTypes import RAGChunk, RAGQuery
from src.rag.llm_client import llm_client


class RAGSynthesizer:
    """Turn retrieved knowledge into a T79-focused answer."""

    def __init__(self, settings=None, llm_client=None):
        self.settings = settings
        self.llm_client = llm_client

    async def synthesize(self, query: RAGQuery, chunks: list[RAGChunk], context=None) -> str:
        context = "\n\n".join([f"[{i + 1}] {c.text}" for i, c in enumerate(chunks)])
        prompt = f"""
You are T79AI — an autonomous DevT79 assistant.

USER QUESTION:
{query.query}

CONTEXT (retrieved from customer systems, logs, errors, scans):
{context}

TASK:
- Answer the user's question accurately.
- Use ONLY provided context.
- Include step-by-step reasoning.
- Provide actionable DevT79 recommendations.
- Explain security risks if relevant.

FORMAT:
Answer only, no system text.
"""
        return await llm_client.ask(prompt)


synthesizer = RAGSynthesizer()
