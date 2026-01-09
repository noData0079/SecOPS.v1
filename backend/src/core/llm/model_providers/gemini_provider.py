# backend/src/core/llm/model_providers/gemini_provider.py

"""Google Gemini provider implementation."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import httpx

from utils.errors import LLMError
from .base_provider import BaseModelProvider, ModelResponse


class GeminiProvider(BaseModelProvider):
    """Google Gemini models provider."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Gemini provider."""
        super().__init__(api_key, **kwargs)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        return bool(self.api_key)
    
    def get_default_model(self) -> str:
        """Default to Gemini Pro."""
        return "gemini-pro"
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using Gemini models.
        
        Supports: gemini-pro, gemini-pro-vision
        """
        if not self.api_key:
            raise LLMError("Gemini API key not configured")
        
        model = model or self.get_default_model()
        start_time = time.time()
        
        url = f"{self.base_url}/models/{model}:generateContent"
        params = {"key": self.api_key}
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, params=params, json=payload)
                response.raise_for_status()
                data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract content from Gemini response
            if "candidates" not in data or not data["candidates"]:
                raise LLMError("Gemini returned no candidates")
            
            candidate = data["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            
            # Estimate tokens (Gemini doesn't always provide exact count)
            tokens_used = len(prompt.split()) + len(content.split())
            
            self._request_count += 1
            self._total_tokens += tokens_used
            
            return ModelResponse(
                content=content,
                model=model,
                provider="gemini",
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": candidate.get("finishReason", "STOP"),
                    "safety_ratings": candidate.get("safetyRatings", []),
                },
                timestamp=datetime.utcnow(),
            )
            
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Gemini HTTP error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise LLMError(f"Unexpected error in Gemini provider: {str(e)}")
    
    async def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Generate text with streaming (Gemini supports this via streamGenerateContent)."""
        if not self.api_key:
            raise LLMError("Gemini API key not configured")
        
        model = model or self.get_default_model()
        url = f"{self.base_url}/models/{model}:streamGenerateContent"
        params = {"key": self.api_key, "alt": "sse"}
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, params=params, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            # Parse SSE data and extract text chunks
                            import json
                            try:
                                data = json.loads(line[6:])
                                if "candidates" in data:
                                    text = data["candidates"][0]["content"]["parts"][0].get("text", "")
                                    if text:
                                        yield text
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Gemini streaming error: {e.response.status_code}")
