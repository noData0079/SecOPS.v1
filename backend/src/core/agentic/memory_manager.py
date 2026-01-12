# backend/src/core/agentic/memory_manager.py

"""Memory management for agents - short-term and long-term storage."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.memory.episodic_store import EpisodicStore

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory."""
    PERCEPTION = "perception"
    GOAL = "goal"
    PLAN = "plan"
    ACTION_RESULT = "action_result"
    REFLECTION = "reflection"


class MemoryManager:
    """Manages agent memory (short-term and long-term)."""
    
    def __init__(self, agent_id: str, episodic_store: Optional[EpisodicStore] = None):
        """Initialize memory manager."""
        self.agent_id = agent_id
        self._short_term: Dict[str, List[Dict[str, Any]]] = {}
        self.episodic_store = episodic_store or EpisodicStore()
        logger.info(f"MemoryManager initialized for agent {agent_id}")
    
    def store_goal(self, goal: str) -> None:
        """Store the agent's goal."""
        if MemoryType.GOAL not in self._short_term:
            self._short_term[MemoryType.GOAL] = []
        self._short_term[MemoryType.GOAL].append({
            "goal": goal,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def store_perception(self, signals: Dict[str, Any]) -> None:
        """Store perceived signals."""
        if MemoryType.PERCEPTION not in self._short_term:
            self._short_term[MemoryType.PERCEPTION] = []
        self._short_term[MemoryType.PERCEPTION].append({
            "signals": signals,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def store_plan(self, plan: Any) -> None:
        """Store a reasoning plan."""
        if MemoryType.PLAN not in self._short_term:
            self._short_term[MemoryType.PLAN] = []
        self._short_term[MemoryType.PLAN].append({
            "plan": plan.to_dict() if hasattr(plan, 'to_dict') else str(plan),
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def store_action_result(self, action: Any, result: Any) -> None:
        """Store action execution result."""
        if MemoryType.ACTION_RESULT not in self._short_term:
            self._short_term[MemoryType.ACTION_RESULT] = []
        self._short_term[MemoryType.ACTION_RESULT].append({
            "action": action.to_dict() if hasattr(action, 'to_dict') else str(action),
            "result": result.to_dict() if hasattr(result, 'to_dict') else str(result),
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def store_reflection(self, reflection: Dict[str, Any]) -> None:
        """Store reflection."""
        if MemoryType.REFLECTION not in self._short_term:
            self._short_term[MemoryType.REFLECTION] = []
        self._short_term[MemoryType.REFLECTION].append(reflection)
    
    async def get_reasoning_context(self) -> Dict[str, Any]:
        """Get context for reasoning (recent memories)."""
        return {
            "recent_perceptions": self._short_term.get(MemoryType.PERCEPTION, [])[-5:],
            "current_goal": self._short_term.get(MemoryType.GOAL, [])[-1:],
            "recent_results": self._short_term.get(MemoryType.ACTION_RESULT, [])[-3:],
            "recent_reflections": self._short_term.get(MemoryType.REFLECTION, [])[-2:],
        }

    def find_similar_episodes(self, query: str, limit: int = 3) -> List[Any]:
        """Find similar past episodes (Long-Term Memory / RAG)."""
        if not self.episodic_store:
            return []
        return self.episodic_store.find_similar(query, limit)
