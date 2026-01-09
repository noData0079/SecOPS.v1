# backend/src/core/workflow/__init__.py

"""
Closed-Loop Workflow Engine.

Detection → Reasoning → Action → Validation
Always on. Continuous operation.
"""

from .signal_collector import SignalCollector, Signal, SignalType
from .correlation_orchestrator import CorrelationOrchestrator
from .decision_engine import DecisionEngine, Decision
from .execution_coordinator import ExecutionCoordinator
from .verification_loop import VerificationLoop

__all__ = [
    "SignalCollector",
    "Signal",
    "SignalType",
    "CorrelationOrchestrator",
    "DecisionEngine",
    "Decision",
    "ExecutionCoordinator",
    "VerificationLoop",
]
