# backend/src/core/llm/model_providers/claude_provider.py

"""Anthropic Claude provider implementation."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import httpx

from utils.errors import LLMError
from .base_provider import BaseModelProvider, ModelResponse


class ClaudeProvider(BaseModelProvider):
    """Anthropic Claude models provider."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Claude provider."""
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.base_url = "https://api.anthropic.com/v1"
        self.api_version = "2023-06-01"
        
    def is_available(self) -> bool:
        """Check if Claude is configured."""
        return bool(self.api_key)
    
    def get_default_model(self) -> str:
        """Default to Claude 3 Sonnet for balanced performance."""
        return "claude-3-sonnet-20240229"
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using Claude models.
        
        Supports: claude-3-opus, claude-3-sonnet, claude-3-haiku, claude-2.1
        """
        if not self.api_key:
            raise LLMError("Anthropic API key not configured")
        
        model = model or self.get_default_model()
        start_time = time.time()
        
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,  # Claude requires max_tokens
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract content from Claude response
            content = data["content"][0]["text"]
            tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
            
            self._request_count += 1
            self._total_tokens += tokens_used
            
            return ModelResponse(
                content=content,
                model=model,
                provider="claude",
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "stop_reason": data.get("stop_reason"),
                    "input_tokens": data["usage"]["input_tokens"],
                    "output_tokens": data["usage"]["output_tokens"],
                },
                timestamp=datetime.utcnow(),
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            raise LLMError(f"Claude HTTP error: {e.response.status_code} - {error_detail}")
        except KeyError as e:
            raise LLMError(f"Unexpected Claude response format: missing {str(e)}")
        except Exception as e:
            raise LLMError(f"Unexpected error in Claude provider: {str(e)}")
    
    async def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Generate text with streaming."""
        if not self.api_key:
            raise LLMError("Anthropic API key not configured")
        
        model = model or self.get_default_model()
        url = f"{self.base_url}/messages"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            import json
                            try:
                                data = json.loads(line[6:])
                                if data.get("type") == "content_block_delta":
                                    if "delta" in data and "text" in data["delta"]:
                                        yield data["delta"]["text"]
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Claude streaming error: {e.response.status_code}")
