# backend/src/core/llm/llm_router.py

"""
Poly-LLM router with task-based intelligent routing.

Routes different types of tasks to the most suitable LLM provider:
- Reasoning tasks → ChatGPT (GPT-4)
- Search/grounding → Gemini
- Code generation → Claude
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Optional, Any
import asyncio

from utils.errors import LLMError
from .model_providers import (
    BaseModelProvider,
    ModelResponse,
    OpenAIProvider,
    GeminiProvider,
    ClaudeProvider,
    LocalProvider,
)
from .data_isolation import DataIsolationManager


logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of tasks for intelligent LLM routing."""
    
    REASONING = "reasoning"  # Complex reasoning, analysis, decision-making
    SEARCH = "search"  # Web search, information retrieval, grounding
    CODE = "code"  # Code generation, refactoring, code review
    GENERAL = "general"  # General purpose tasks
    CHAT = "chat"  # Conversational tasks


class LLMRouter:
    """
    Intelligent router that selects the best LLM provider for each task.
    
    Features:
    - Task-based routing to optimal provider
    - Automatic fallback on failure
    - Data isolation and audit logging
    - Rate limiting and cost tracking
    - Unified interface for all providers
    """
    
    def __init__(self, enable_data_isolation: bool = True):
        """
        Initialize LLM router.
        
        Args:
            enable_data_isolation: Enable data isolation and audit logging
        """
        # Initialize all providers
        self.providers: Dict[str, BaseModelProvider] = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
            "local": LocalProvider(),
        }
        
        # Task routing rules: TaskType -> (primary_provider, fallback_provider)
        self.routing_rules = {
            TaskType.REASONING: ("openai", "claude"),  # GPT-4 best for reasoning
            TaskType.SEARCH: ("gemini", "openai"),  # Gemini best for search/grounding
            TaskType.CODE: ("claude", "openai"),  # Claude best for code
            TaskType.GENERAL: ("openai", "gemini"),  # Default to GPT-4
            TaskType.CHAT: ("openai", "local"),  # Fast models for chat
        }
        
        # Provider-specific model preferences
        self.model_preferences = {
            TaskType.REASONING: {
                "openai": "gpt-4-turbo-preview",
                "claude": "claude-3-opus-20240229",
            },
            TaskType.SEARCH: {
                "gemini": "gemini-pro",
            },
            TaskType.CODE: {
                "claude": "claude-3-sonnet-20240229",
                "openai": "gpt-4-turbo-preview",
            },
            TaskType.GENERAL: {
                "openai": "gpt-4-turbo-preview",
                "gemini": "gemini-pro",
            },
            TaskType.CHAT: {
                "openai": "gpt-3.5-turbo",
                "local": "local-model",
            },
        }
        
        # Data isolation manager
        self.data_isolation = None
        if enable_data_isolation:
            self.data_isolation = DataIsolationManager()
        
        # Statistics
        self._total_requests = 0
        self._total_cost = 0.0
        self._provider_usage = {p: 0 for p in self.providers.keys()}
        
        logger.info("LLMRouter initialized with providers: %s", list(self.providers.keys()))
    
    def get_available_providers(self) -> List[str]:
        """Get list of available configured providers."""
        return [name for name, provider in self.providers.items() if provider.is_available()]
    
    def _select_provider(
        self,
        task_type: TaskType,
        preferred_provider: Optional[str] = None
    ) -> tuple[str, BaseModelProvider]:
        """
        Select the best provider for a task.
        
        Args:
            task_type: Type of task to perform
            preferred_provider: Optional specific provider to use
            
        Returns:
            Tuple of (provider_name, provider_instance)
            
        Raises:
            LLMError: If no suitable provider is available
        """
        # If preferred provider specified and available, use it
        if preferred_provider:
            if preferred_provider in self.providers:
                provider = self.providers[preferred_provider]
                if provider.is_available():
                    return preferred_provider, provider
                else:
                    logger.warning(f"Preferred provider {preferred_provider} not available")
        
        # Get routing rule for task type
        primary, fallback = self.routing_rules.get(task_type, ("openai", "local"))
        
        # Try primary provider
        if primary in self.providers and self.providers[primary].is_available():
            return primary, self.providers[primary]
        
        # Try fallback provider
        if fallback in self.providers and self.providers[fallback].is_available():
            logger.info(f"Primary provider {primary} unavailable, using fallback {fallback}")
            return fallback, self.providers[fallback]
        
        # Try any available provider
        for name, provider in self.providers.items():
            if provider.is_available():
                logger.warning(f"Using emergency fallback provider: {name}")
                return name, provider
        
        raise LLMError("No LLM providers are available. Please configure at least one provider.")
    
    def _select_model(self, task_type: TaskType, provider_name: str) -> str:
        """Select the best model for a task and provider."""
        preferences = self.model_preferences.get(task_type, {})
        return preferences.get(provider_name, self.providers[provider_name].get_default_model())
    
    async def generate(
        self,
        prompt: str,
        task_type: TaskType = TaskType.GENERAL,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text using the best provider for the task.
        
        Args:
            prompt: The input prompt
            task_type: Type of task for intelligent routing
            preferred_provider: Specific provider to use (overrides routing)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            metadata: Additional metadata for audit logging
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ModelResponse with generated content
            
        Raises:
            LLMError: If generation fails
        """
        # Select provider and model
        provider_name, provider = self._select_provider(task_type, preferred_provider)
        model = self._select_model(task_type, provider_name)
        
        logger.info(
            f"Routing {task_type.value} task to {provider_name} using {model}"
        )
        
        # Log request (data isolation)
        request_id = None
        if self.data_isolation:
            request_id = await self.data_isolation.log_request(
                provider=provider_name,
                model=model,
                prompt=prompt,
                task_type=task_type.value,
                metadata=metadata or {},
            )
        
        try:
            # Generate response
            response = await provider.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            # Update statistics
            self._total_requests += 1
            self._provider_usage[provider_name] += 1
            self._total_cost += response.cost_estimate
            
            # Log response (data isolation)
            if self.data_isolation and request_id:
                await self.data_isolation.log_response(
                    request_id=request_id,
                    response_content=response.content,
                    tokens_used=response.tokens_used,
                    latency_ms=response.latency_ms,
                    cost=response.cost_estimate,
                )
            
            return response
            
        except LLMError as e:
            logger.error(f"Generation failed with {provider_name}: {e}")
            
            # Log failure
            if self.data_isolation and request_id:
                await self.data_isolation.log_failure(request_id, str(e))
            
            raise
    
    async def generate_streaming(
        self,
        prompt: str,
        task_type: TaskType = TaskType.GENERAL,
        preferred_provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Generate text with streaming response.
        
        Args:
            prompt: The input prompt
            task_type: Type of task for routing
            preferred_provider: Specific provider to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        provider_name, provider = self._select_provider(task_type, preferred_provider)
        model = self._select_model(task_type, provider_name)
        
        logger.info(f"Streaming {task_type.value} task to {provider_name} using {model}")
        
        try:
            async for chunk in provider.generate_streaming(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                yield chunk
                
        except LLMError as e:
            logger.error(f"Streaming failed with {provider_name}: {e}")
            raise
    
    async def generate_with_fallback(
        self,
        prompt: str,
        task_type: TaskType = TaskType.GENERAL,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> ModelResponse:
        """
        Generate text with automatic fallback on failure.
        
        Tries primary provider, then fallback, then any available provider.
        
        Returns:
            ModelResponse from the first successful provider
            
        Raises:
            LLMError: If all providers fail
        """
        primary, fallback = self.routing_rules.get(task_type, ("openai", "local"))
        providers_to_try = [primary, fallback]
        
        # Add any other available providers
        for name in self.providers.keys():
            if name not in providers_to_try and self.providers[name].is_available():
                providers_to_try.append(name)
        
        errors = []
        
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                continue
            
            try:
                return await self.generate(
                    prompt=prompt,
                    task_type=task_type,
                    preferred_provider=provider_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            except LLMError as e:
                errors.append(f"{provider_name}: {e}")
                logger.warning(f"Provider {provider_name} failed, trying next...")
                continue
        
        # All providers failed
        error_msg = "All providers failed: " + "; ".join(errors)
        raise LLMError(error_msg)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        available = self.get_available_providers()
        return {
            "total_requests": self._total_requests,
            "total_cost_estimate": round(self._total_cost, 4),
            "provider_usage": self._provider_usage,
            "available_providers": available,
            "configured_providers": list(self.providers.keys()),
            "provider_stats": {
                name: provider.get_stats()
                for name, provider in self.providers.items()
            },
        }


# Global router instance (singleton)
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """Get the global LLM router instance."""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
