"""
TSM99 Core Autonomy Module

This module implements the locked Final Architecture:
OBSERVATION → MODEL → POLICY → TOOLS → OUTCOME → REPLAY

Components:
- PolicyEngine: Deterministic rules (NO ML - this is the moat)
- AutonomyLoop: Core execution cycle
- ReplayEngine: Offline learning without GPUs

Usage:
    from core.autonomy import PolicyEngine, AutonomyLoop, ReplayEngine
"""

from .policy_engine import (
    PolicyEngine,
    PolicyDecision,
    RiskLevel,
    AgentState,
    ProposedAction,
    policy_check,
)

from .loop import (
    AutonomyLoop,
    Observation,
    Outcome,
    ReplayEntry,
)

from .replay import (
    ReplayEngine,
    ReplayRecord,
    AlternativeAction,
)


__all__ = [
    # Policy Engine
    "PolicyEngine",
    "PolicyDecision",
    "RiskLevel",
    "AgentState",
    "ProposedAction",
    "policy_check",
    # Autonomy Loop
    "AutonomyLoop",
    "Observation",
    "Outcome",
    "ReplayEntry",
    # Replay Engine
    "ReplayEngine",
    "ReplayRecord",
    "AlternativeAction",
]
