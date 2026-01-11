"""
Local LLM Provider - Offline-first open-source model strategy.

Provides sovereignty by running models locally:
- Ollama integration
- vLLM server integration
- llama.cpp fallback

NO PAID API DEPENDENCY.
"""

from __future__ import annotations

import logging
import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class LocalModelConfig:
    """Configuration for a local model."""
    name: str
    provider: str  # "ollama", "vllm", "llamacpp"
    model_path: str
    context_length: int = 4096
    temperature: float = 0.1
    
    # Capabilities
    supports_json: bool = True
    supports_tools: bool = False
    
    # Performance
    max_tokens: int = 1024
    batch_size: int = 1


class LocalLLMProvider:
    """
    Local LLM provider for offline-first operation.
    
    Supports:
    - Ollama (recommended for ease of use)
    - vLLM (recommended for production)
    - llama.cpp (CPU fallback)
    
    CRITICAL: This enables true sovereignty.
    Ice-Age deployments MUST use this.
    """
    
    def __init__(self):
        # Available providers
        self.providers: Dict[str, Dict[str, Any]] = {
            "ollama": {
                "base_url": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                "available": False,
            },
            "vllm": {
                "base_url": os.getenv("VLLM_HOST", "http://localhost:8000"),
                "available": False,
            },
            "llamacpp": {
                "base_url": os.getenv("LLAMACPP_HOST", "http://localhost:8080"),
                "available": False,
            },
        }
        
        # Default models by provider
        self.default_models = {
            "ollama": "deepseek-coder:6.7b",
            "vllm": "deepseek-coder-6.7b-instruct",
            "llamacpp": "deepseek-coder-6.7b-instruct-q4_k_m.gguf",
        }
        
        # Fallback order
        self.fallback_order = ["ollama", "vllm", "llamacpp"]
        
        # Current active provider
        self.active_provider: Optional[str] = None
        self.active_model: Optional[str] = None
    
    async def initialize(self) -> bool:
        """Initialize and find available providers."""
        for provider in self.fallback_order:
            if await self._check_provider(provider):
                self.providers[provider]["available"] = True
                if not self.active_provider:
                    self.active_provider = provider
                    self.active_model = self.default_models[provider]
                    logger.info(f"Local LLM: Using {provider} with {self.active_model}")
        
        return self.active_provider is not None
    
    async def _check_provider(self, provider: str) -> bool:
        """Check if a provider is available."""
        try:
            import httpx
            
            base_url = self.providers[provider]["base_url"]
            
            if provider == "ollama":
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{base_url}/api/tags")
                    return resp.status_code == 200
            
            elif provider == "vllm":
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{base_url}/v1/models")
                    return resp.status_code == 200
            
            elif provider == "llamacpp":
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(f"{base_url}/health")
                    return resp.status_code == 200
            
        except Exception as e:
            logger.debug(f"Provider {provider} not available: {e}")
            return False
        
        return False
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.1,
        json_mode: bool = False,
    ) -> str:
        """
        Generate text using the local model.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            json_mode: Whether to enforce JSON output
        
        Returns:
            Generated text
        """
        if not self.active_provider:
            await self.initialize()
            if not self.active_provider:
                raise RuntimeError("No local LLM provider available")
        
        try:
            if self.active_provider == "ollama":
                return await self._generate_ollama(prompt, system_prompt, max_tokens, temperature, json_mode)
            elif self.active_provider == "vllm":
                return await self._generate_vllm(prompt, system_prompt, max_tokens, temperature, json_mode)
            elif self.active_provider == "llamacpp":
                return await self._generate_llamacpp(prompt, system_prompt, max_tokens, temperature, json_mode)
        except Exception as e:
            logger.error(f"Generation failed with {self.active_provider}: {e}")
            # Try fallback
            return await self._try_fallback(prompt, system_prompt, max_tokens, temperature, json_mode)
        
        raise RuntimeError("All local LLM providers failed")
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        """Generate using Ollama."""
        import httpx
        
        base_url = self.providers["ollama"]["base_url"]
        
        payload = {
            "model": self.active_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if json_mode:
            payload["format"] = "json"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
    
    async def _generate_vllm(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        """Generate using vLLM (OpenAI-compatible API)."""
        import httpx
        
        base_url = self.providers["vllm"]["base_url"]
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.active_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base_url}/v1/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    
    async def _generate_llamacpp(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        """Generate using llama.cpp server."""
        import httpx
        
        base_url = self.providers["llamacpp"]["base_url"]
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "prompt": full_prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
        }
        
        if json_mode:
            payload["grammar"] = "json"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base_url}/completion", json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("content", "")
    
    async def _try_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        """Try fallback providers."""
        current_index = self.fallback_order.index(self.active_provider)
        
        for i in range(current_index + 1, len(self.fallback_order)):
            provider = self.fallback_order[i]
            if self.providers[provider]["available"]:
                self.active_provider = provider
                self.active_model = self.default_models[provider]
                logger.info(f"Falling back to {provider}")
                return await self.generate(prompt, system_prompt, max_tokens, temperature, json_mode)
        
        raise RuntimeError("All local LLM providers exhausted")
    
    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "active_provider": self.active_provider,
            "active_model": self.active_model,
            "providers": {
                name: {"available": info["available"], "url": info["base_url"]}
                for name, info in self.providers.items()
            },
        }


# Global instance
local_llm = LocalLLMProvider()


__all__ = [
    "LocalLLMProvider",
    "LocalModelConfig",
    "local_llm",
]
