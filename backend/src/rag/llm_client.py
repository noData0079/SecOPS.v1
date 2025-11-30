# backend/src/rag/llm_client.py

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Generic async client for chat-style LLMs.

    This is designed to work with:
      - OpenAI API
      - Any OpenAI-compatible endpoint (custom base URL)
      - A simple 'mock' provider for local development

    It exposes a single main method:

        await client.chat(
            messages=[{"role": "system", "content": "..."}, ...],
            model="gpt-4.1-mini",
            max_tokens=512,
            temperature=0.2,
        )

    and returns a dict of the form:

        {
          "content": str,  # assistant message
          "usage": {
              "model": str | None,
              "provider": str | None,
              "prompt_tokens": int | None,
              "completion_tokens": int | None,
              "total_tokens": int | None,
              "latency_ms": float | None,
          },
          "raw": {...},  # raw provider response for logging/debug
        }
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Provider selection
        # e.g. "openai", "openai_compatible", "mock"
        self.provider: str = getattr(settings, "LLM_PROVIDER", None) or os.getenv(
            "LLM_PROVIDER", "openai"
        ).lower()

        # Model defaults (can be overridden per call)
        self.default_model: Optional[str] = getattr(
            settings, "LLM_DEFAULT_MODEL", None
        ) or os.getenv("LLM_DEFAULT_MODEL")

        # OpenAI / compatible API configuration
        self._api_key = (
            getattr(settings, "OPENAI_API_KEY", None)
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("LLM_API_KEY")
        )
        self._api_base = (
            getattr(settings, "OPENAI_API_BASE", None)
            or os.getenv("OPENAI_API_BASE")
            or os.getenv("LLM_API_BASE")
            or "https://api.openai.com/v1"
        )

        # For OpenAI-compatible chat completions
        self._chat_path = "/chat/completions"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def chat(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the configured provider.

        :param messages: list of {"role": "...", "content": "..."} messages
        :param model: optional override for model; falls back to default_model
        :param max_tokens: optional max tokens for response
        :param temperature: sampling temperature
        :return: dict with keys "content", "usage", "raw"
        """
        provider = self.provider
        chosen_model = model or self.default_model

        if provider == "mock":
            return self._chat_mock(messages=messages, model=chosen_model)

        # Treat anything else as OpenAI-compatible for now
        return await self._chat_openai_compatible(
            messages=messages,
            model=chosen_model,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # ------------------------------------------------------------------
    # Provider: OpenAI / OpenAI-compatible
    # ------------------------------------------------------------------

    async def _chat_openai_compatible(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str],
        max_tokens: Optional[int],
        temperature: Optional[float],
    ) -> Dict[str, Any]:
        """
        Call an OpenAI-compatible /v1/chat/completions endpoint via HTTP.
        """
        if not self._api_key:
            logger.error("LLMClient: OPENAI_API_KEY / LLM_API_KEY is not configured")
            # Fail soft: return a helpful error-like response instead of raising
            return {
                "content": "LLM is not configured on the server (missing API key).",
                "usage": {
                    "model": model,
                    "provider": self.provider,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None,
                    "latency_ms": None,
                },
                "raw": {"error": "missing_api_key"},
            }

        if not model:
            logger.warning("LLMClient: no model specified, using 'gpt-4.1-mini' fallback")
            model = "gpt-4.1-mini"

        url = f"{self._api_base.rstrip('/')}{self._chat_path}"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        logger.debug("LLMClient: sending chat request to %s with model=%s", url, model)

        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(url, headers=headers, json=payload)
            except Exception as exc:
                logger.exception("LLMClient: HTTP error during chat request")
                latency_ms = (time.perf_counter() - started) * 1000.0
                return {
                    "content": f"LLM request failed: {type(exc).__name__}",
                    "usage": {
                        "model": model,
                        "provider": self.provider,
                        "prompt_tokens": None,
                        "completion_tokens": None,
                        "total_tokens": None,
                        "latency_ms": latency_ms,
                    },
                    "raw": {"error": str(exc)},
                }

        latency_ms = (time.perf_counter() - started) * 1000.0

        if resp.status_code >= 400:
            logger.error(
                "LLMClient: non-200 status code %s from LLM provider: %s",
                resp.status_code,
                resp.text[:500],
            )
            return {
                "content": f"LLM provider returned an error (status {resp.status_code}).",
                "usage": {
                    "model": model,
                    "provider": self.provider,
                    "prompt_tokens": None,
                    "completion_tokens": None,
                    "total_tokens": None,
                    "latency_ms": latency_ms,
                },
                "raw": {"status_code": resp.status_code, "body": resp.text},
            }

        data = resp.json()

        # OpenAI-style response parsing
        try:
            choices = data.get("choices") or []
            if not choices:
                content = ""
            else:
                content = (
                    choices[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
        except Exception:
            logger.exception("LLMClient: failed to parse LLM response body")
            content = ""

        usage_data = data.get("usage") or {}
        prompt_tokens = usage_data.get("prompt_tokens")
        completion_tokens = usage_data.get("completion_tokens")
        total_tokens = usage_data.get("total_tokens")

        usage = {
            "model": data.get("model") or model,
            "provider": self.provider,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "latency_ms": latency_ms,
        }

        return {
            "content": content,
            "usage": usage,
            "raw": data,
        }

    # ------------------------------------------------------------------
    # Provider: mock
    # ------------------------------------------------------------------

    def _chat_mock(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str],
    ) -> Dict[str, Any]:
        """
        Lightweight local mock for dev / tests.

        It simply echoes the last user message with a prefix. No external calls.
        """
        user_content = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_content = msg.get("content", "")
                break

        content = (
            "MOCK LLM RESPONSE (no real model used).\n\n"
            "You asked:\n"
            f"{user_content}"
        )

        usage = {
            "model": model or "mock-model",
            "provider": "mock",
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "latency_ms": 0.0,
        }

        return {
            "content": content,
            "usage": usage,
            "raw": {"provider": "mock"},
        }
