"""
Local Execution Module

All execution within customer trusted boundary.
"""

from .engine import (
    LocalExecutionEngine,
    ApprovalGate,
    ApprovalRequest,
    ApprovalPolicy,
    RiskBasedPolicy,
    AlwaysRequireHumanPolicy,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
    LocalExecutor,
    CodePatchExecutor,
)

__all__ = [
    "LocalExecutionEngine",
    "ApprovalGate",
    "ApprovalRequest",
    "ApprovalPolicy",
    "RiskBasedPolicy",
    "AlwaysRequireHumanPolicy",
    "ExecutionResult",
    "ExecutionStatus",
    "ExecutionType",
    "LocalExecutor",
    "CodePatchExecutor",
]

__version__ = "1.0.0"
