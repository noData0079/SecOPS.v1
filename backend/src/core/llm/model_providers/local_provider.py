# backend/src/core/llm/model_providers/local_provider.py

"""Local model provider for LM Studio, Ollama, vLLM, etc."""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional

import httpx

from utils.errors import LLMError
from .base_provider import BaseModelProvider, ModelResponse


class LocalProvider(BaseModelProvider):
    """Local model provider (LM Studio, Ollama, vLLM)."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize local provider."""
        super().__init__(api_key, **kwargs)
        self.base_url = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")
        self.model_name = os.getenv("LOCAL_LLM_MODEL", "local-model")
        
    def is_available(self) -> bool:
        """Check if local LLM endpoint is available."""
        try:
            import httpx
            response = httpx.get(f"{self.base_url}/models", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    def get_default_model(self) -> str:
        """Get local model name."""
        return self.model_name
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using local model endpoint.
        
        Supports OpenAI-compatible API (LM Studio, vLLM, text-generation-webui)
        """
        model = model or self.get_default_model()
        start_time = time.time()
        
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:  # Local can be slow
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # Parse OpenAI-compatible response
            content = data["choices"][0]["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", 0)
            
            self._request_count += 1
            self._total_tokens += tokens_used
            
            return ModelResponse(
                content=content,
                model=model,
                provider="local",
                tokens_used=tokens_used,
                latency_ms=latency_ms,
                metadata={
                    "finish_reason": data["choices"][0].get("finish_reason"),
                    "endpoint": self.base_url,
                },
                timestamp=datetime.utcnow(),
            )
            
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Local LLM HTTP error: {e.response.status_code} - {e.response.text}")
        except httpx.ConnectError:
            raise LLMError(f"Cannot connect to local LLM at {self.base_url}")
        except Exception as e:
            raise LLMError(f"Unexpected error in local provider: {str(e)}")
    
    async def generate_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Generate text with streaming."""
        model = model or self.get_default_model()
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": True,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            import json
                            try:
                                data = json.loads(line[6:])
                                if "choices" in data:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            raise LLMError(f"Local LLM streaming error: {e.response.status_code}")
        except httpx.ConnectError:
            raise LLMError(f"Cannot connect to local LLM at {self.base_url}")
