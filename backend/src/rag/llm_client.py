# backend/src/rag/llm_client.py

"""
Multi-provider LLM client with fallback support.

Fallback priority:
1. OpenAI (GPT-4, GPT-3.5)
2. Google Gemini
3. Anthropic Claude
4. Local LM Studio
"""

from __future__ import annotations

import os
import logging
from typing import Optional, Dict, Any

import httpx

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client with multi-provider fallback support.
    
    Automatically falls back through available providers:
    1. OpenAI
    2. Google Gemini
    3. Anthropic Claude
    4. Local LM Studio
    """

    def __init__(self):
        """Initialize LLM client."""
        self._openai_key = os.getenv("OPENAI_API_KEY")
        self._gemini_key = os.getenv("GEMINI_API_KEY")
        self._claude_key = os.getenv("ANTHROPIC_API_KEY")
        self._local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:1234")

    async def ask(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Send a prompt to the best available LLM provider.
        
        Args:
            prompt: The input prompt
            model: Optional model override
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
            
        Raises:
            RuntimeError: If all providers fail
        """
        errors = []

        # ========= OpenAI =========
        if self._openai_key:
            try:
                return await self._openai(prompt, model, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"OpenAI failed: {e}")
                errors.append(f"OpenAI: {e}")

        # ========= Gemini =========
        if self._gemini_key:
            try:
                return await self._gemini(prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Gemini failed: {e}")
                errors.append(f"Gemini: {e}")

        # ========= Claude =========
        if self._claude_key:
            try:
                return await self._claude(prompt, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Claude failed: {e}")
                errors.append(f"Claude: {e}")

        # ========= Local LM Studio =========
        try:
            return await self._local(prompt, temperature, max_tokens)
        except Exception as e:
            logger.warning(f"Local LLM failed: {e}")
            errors.append(f"Local: {e}")

        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")

    async def _openai(
        self,
        prompt: str,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using OpenAI API."""
        import openai

        client = openai.AsyncOpenAI(api_key=self._openai_key)
        response = await client.chat.completions.create(
            model=model or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _gemini(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using Google Gemini API."""
        import google.generativeai as genai

        genai.configure(api_key=self._gemini_key)
        model = genai.GenerativeModel("gemini-pro")
        
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    async def _claude(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using Anthropic Claude API."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self._claude_key)
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def _local(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate using local LM Studio or compatible endpoint."""
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self._local_url}/v1/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


# Global instance
llm_client = LLMClient()
