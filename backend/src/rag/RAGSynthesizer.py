# backend/src/rag/RAGSynthesizer.py

from __future__ import annotations

import logging
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, List, Optional

from rag.AdvancedRAGTypes import (
    RAGAnswer,
    RAGQueryContext,
    RAGSection,
    RAGUsage,
    RetrievedContext,
)
from rag.llm_client import LLMClient

logger = logging.getLogger(__name__)


class RAGSynthesizer:
    """
    Responsible for turning retrieved context + a user query into a final answer.

    High-level flow:
      1. Build system and user prompts based on mode (default / security / code).
      2. Pack retrieved chunks into a compact context block.
      3. Call LLMClient.chat(...) to generate the answer.
      4. Wrap into RAGAnswer with usage info and optional sections.

    This class is provider-agnostic: all provider specifics are hidden in LLMClient.
    """

    def __init__(self, settings: Any, llm_client: LLMClient) -> None:
        self.settings = settings
        self.llm_client = llm_client

        # Default LLM parameters; can be overridden by settings if desired.
        self.default_model = getattr(settings, "RAG_MODEL", None)
        self.default_max_tokens = getattr(settings, "RAG_MAX_TOKENS", 768)
        self.default_temperature = getattr(settings, "RAG_TEMPERATURE", 0.2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def synthesize(
        self,
        *,
        query: str,
        retrieved: RetrievedContext,
        context: RAGQueryContext,
    ) -> RAGAnswer:
        """
        Main entrypoint: synthesize an answer for the query.

        Parameters:
            query: the user question
            retrieved: retrieval result (chunks + sources)
            context: query context (org, user, mode, limits, flags)

        Returns:
            RAGAnswer
        """
        # 1. Prepare prompt components
        system_prompt = self._build_system_prompt(context=context)
        user_prompt = self._build_user_prompt(
            query=query,
            retrieved=retrieved,
            context=context,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        model = self.default_model
        max_tokens = min(context.max_tokens or self.default_max_tokens, self.default_max_tokens)
        temperature = self.default_temperature

        logger.debug(
            "RAG synthesis call: model=%s max_tokens=%s temperature=%s mode=%s",
            model,
            max_tokens,
            temperature,
            context.mode,
        )

        # 2. Call the LLM via LLMClient
        started_at = datetime.utcnow()
        llm_response = await self.llm_client.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        finished_at = datetime.utcnow()

        # Expected llm_response shape (contract with LLMClient):
        # {
        #   "content": str,
        #   "usage": {
        #       "model": str,
        #       "provider": str,
        #       "prompt_tokens": int | None,
        #       "completion_tokens": int | None,
        #       "total_tokens": int | None,
        #       "latency_ms": float | None,
        #   },
        #   "raw": {...}  # provider specific payload
        # }

        text = llm_response.get("content", "").strip()
        raw_usage = llm_response.get("usage") or {}
        raw_payload = llm_response.get("raw") or {}

        latency_ms = (finished_at - started_at).total_seconds() * 1000.0

        usage = RAGUsage(
            model=raw_usage.get("model"),
            provider=raw_usage.get("provider"),
            prompt_tokens=raw_usage.get("prompt_tokens"),
            completion_tokens=raw_usage.get("completion_tokens"),
            total_tokens=raw_usage.get("total_tokens"),
            latency_ms=raw_usage.get("latency_ms") or latency_ms,
        )

        # 3. Build optional sections (simple heuristic for now)
        sections = self._infer_sections_from_text(text=text, mode=context.mode)

        return RAGAnswer(
            text=text,
            sections=sections,
            usage=usage,
            raw=raw_payload,
        )

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_system_prompt(self, *, context: RAGQueryContext) -> str:
        """
        Build a mode-aware system prompt.

        Modes:
          - default: general assistant grounded in supplied context
          - security: SecOps / devsecops expert
          - code: senior full-stack / infra engineer
        """
        base = dedent(
            """
            You are an AI assistant that answers strictly based on the context you receive.
            If the context is insufficient to answer confidently, you must say you are
            not sure and clearly state what is missing. Never fabricate tools, systems,
            or events that are not supported by the provided context.

            Always:
            - Explain your reasoning clearly, but keep it concise.
            - Highlight potential risks, tradeoffs, and caveats when relevant.
            - When giving step-by-step guidance, make each step actionable.
            """
        ).strip()

        if context.mode == "security":
            specialization = dedent(
                """
                You are acting as a senior security and reliability engineer specializing
                in application security, infrastructure security, and DevSecOps.
                Focus on:
                - vulnerabilities, misconfigurations, and risk
                - root cause analysis
                - concrete remediation steps and safe rollout strategies.
                """
            ).strip()
        elif context.mode == "code":
            specialization = dedent(
                """
                You are acting as a senior full-stack engineer and SRE.
                Focus on:
                - correct, idiomatic code
                - clear architecture and tradeoffs
                - performance, reliability, and maintainability.
                """
            ).strip()
        else:
            specialization = dedent(
                """
                You are acting as a pragmatic technical assistant.
                Focus on:
                - clarity
                - correctness
                - practical, minimally risky advice.
                """
            ).strip()

        return f"{base}\n\n{specialization}"

    def _build_user_prompt(
        self,
        *,
        query: str,
        retrieved: RetrievedContext,
        context: RAGQueryContext,
    ) -> str:
        """
        Build the user-facing prompt containing:
        - the original question
        - a compact context block from retrieved chunks
        """
        context_block = self._format_context_block(retrieved=retrieved, top_k=context.top_k)

        instructions = dedent(
            """
            Use ONLY the information in the CONTEXT block below when answering.
            If the context does not contain enough information to answer safely,
            say so clearly and suggest what additional input or telemetry would help.

            Structure your answer with:
            - a very short direct answer first (1–3 lines),
            - then a more detailed explanation,
            - and concrete next steps / actions if relevant.
            """
        ).strip()

        return dedent(
            f"""
            QUESTION:
            {query}

            {instructions}

            CONTEXT:
            {context_block}
            """
        ).strip()

    def _format_context_block(
        self,
        *,
        retrieved: RetrievedContext,
        top_k: int,
    ) -> str:
        """
        Convert retrieved chunks into a compact context block.

        We keep it simple: take up to `top_k` chunks, ordered by score desc.
        """
        if not retrieved.chunks:
            return "[no retrieved context available]"

        # Sort by score (desc) and take top_k
        chunks_sorted = sorted(retrieved.chunks, key=lambda c: c.score, reverse=True)[:top_k]

        lines: List[str] = []
        for idx, chunk in enumerate(chunks_sorted, start=1):
            source_id = chunk.source_id
            score_str = f"{chunk.score:.3f}"
            lines.append(
                f"[{idx}] (source={source_id}, score={score_str})\n{chunk.text}\n"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Simple sectioning heuristic
    # ------------------------------------------------------------------

    def _infer_sections_from_text(self, *, text: str, mode: str) -> List[RAGSection]:
        """
        Very lightweight section inference.

        For now this does NOT call the model again; it just builds a single
        section or a couple of coarse sections based on mode. This keeps the
        synthesizer fast and predictable.

        You can later replace this with a more advanced structured format
        (e.g. asking the LLM for JSON) without changing callers.
        """
        text = (text or "").strip()
        if not text:
            return []

        # For security mode, we try to structure into a few logical buckets.
        if mode == "security":
            return [
                RAGSection(
                    heading="Summary",
                    content=text,
                    citation_source_ids=[],
                )
            ]

        # For code mode and default, we just return a single section for now.
        return [
            RAGSection(
                heading="Answer",
                content=text,
                citation_source_ids=[],
            )
        ]
