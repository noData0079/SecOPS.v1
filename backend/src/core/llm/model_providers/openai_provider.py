# backend/src/core/llm/model_providers/openai_provider.py

"""OpenAI/ChatGPT provider implementation."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import httpx
from openai import AsyncOpenAI, OpenAIError

from utils.errors import LLMError
from .base_provider import BaseModelProvider, ModelResponse


class OpenAIProvider(BaseModelProvider):
    """OpenAI GPT models provider."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider."""
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        
    def is_available(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.api_key)
    
    def get_default_model(self) -> str:
        """Default to GPT-4 Turbo for best quality."""
        return "gpt-4-turbo-preview"
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using OpenAI models.
        
        Supports: gpt-4, gpt-4-turbo, gpt-3.5-turbo, etc.
        """
        if not self.client:
            raise LLMError("OpenAI API key not configured")
        
        model = model or self.get_default_model()
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            self._request_count += 1
            self._total_tokens += tokens_used
            
            return ModelResponse(
                content=content,
                model=model,
                provider="openai",
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "model_used": response.model,
                },
                timestamp=datetime.utcnow(),
            )
            
        except OpenAIError as e:
            raise LLMError(f"OpenAI generation failed: {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error in OpenAI provider: {str(e)}")
    
    async def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Generate text with streaming."""
        if not self.client:
            raise LLMError("OpenAI API key not configured")
        
        model = model or self.get_default_model()
        
        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except OpenAIError as e:
            raise LLMError(f"OpenAI streaming failed: {str(e)}")
