"""
Memory System - 4 distinct memory layers for true autonomy.

Components:
1. Episodic Memory - Complete incident snapshots
2. Semantic Memory - Abstracted lessons ("what usually works")
3. Policy Memory - Track which rules are brittle
4. Economic Memory - Cost vs benefit analysis

This is NOT logs. This is structured, queryable intelligence.
"""

from .episodic_store import (
    EpisodicStore,
    EpisodeSnapshot,
    IncidentMemory,
)

from .semantic_store import (
    SemanticStore,
    SemanticFact,
    ToolPattern,
)

from .policy_memory import (
    PolicyMemory,
    PolicyRecord,
)

from .economic_memory import (
    EconomicMemory,
    ActionCost,
    CostBudget,
)


__all__ = [
    # Episodic
    "EpisodicStore",
    "EpisodeSnapshot",
    "IncidentMemory",
    # Semantic
    "SemanticStore",
    "SemanticFact",
    "ToolPattern",
    # Policy
    "PolicyMemory",
    "PolicyRecord",
    # Economic
    "EconomicMemory",
    "ActionCost",
    "CostBudget",
]
