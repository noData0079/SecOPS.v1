# backend/src/core/llm/__init__.py (UPDATE)

"""
Poly-LLM Orchestration Layer.

Routes requests to optimal LLM providers:
- ChatGPT: Reasoning and correlation
- Gemini: Search and research
- Claude: Code generation
"""

from .llm_router import LLMRouter, TaskType
from .data_isolation import DataIsolationManager
from .model_providers import (
    BaseModelProvider,
    OpenAIProvider,
    GeminiProvider,
    ClaudeProvider,
    LocalProvider,
)


def get_llm_router(enable_data_isolation: bool = True) -> LLMRouter:
    """
    Factory function to get configured LLM router.
    
    Args:
        enable_data_isolation: Enable data isolation and audit logging
        
    Returns:
        Configured LLMRouter instance
    """
    return LLMRouter(enable_data_isolation=enable_data_isolation)


__all__ = [
    "LLMRouter",
    "TaskType",
    "DataIsolationManager",
    "BaseModelProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "ClaudeProvider",
    "LocalProvider",
    "get_llm_router",
]
