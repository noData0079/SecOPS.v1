# backend/src/core/agentic/__init__.py

"""
Agentic core framework for autonomous AI operations.

10-Layer Architecture:
- Layer 5: Reasoning Orchestrator (Poly-LLM Router)
- Layer 6: Code Context Engine, Fix Proposal Engine
- Layer 7: Approval Gates, Action Executor
- Layer 8: Execution Engine
- Layer 9: Verification Engine
- Layer 10: Trust Ledger
"""

from .agent_core import Agent, AgentConfig, AgentState
from .reasoning_loop import ReasoningLoop, ReasoningStep
from .memory_manager import MemoryManager, MemoryType
from .action_executor import ActionExecutor, Action, ActionResult, ActionType
from .approval_gates import ApprovalGate, ApprovalPolicy, ApprovalStatus, RiskLevel
from .reasoning_orchestrator import (
    ReasoningOrchestrator,
    ReasoningRequest,
    ReasoningResponse,
    TaskType,
    ReasoningModel,
)
from .code_context_engine import CodeContextEngine, CodeFile, ImpactAnalysis
from .fix_proposal_engine import (
    FixProposalEngine,
    FixProposal,
    FixType,
    FixRiskLevel,
    RollbackPlan,
)
from .execution_engine import ExecutionEngine, ExecutionRecord, ExecutionStatus
from .verification_engine import (
    VerificationEngine,
    VerificationResult,
    VerificationCheck,
    VerificationStatus,
    VerificationType,
)
from .trust_ledger import (
    TrustLedger,
    TrustReport,
    TrustState,
    EvidenceRecord,
    EvidenceType,
)

__all__ = [
    # Core agent
    "Agent",
    "AgentConfig",
    "AgentState",
    "ReasoningLoop",
    "ReasoningStep",
    "MemoryManager",
    "MemoryType",
    # Layer 5 - Reasoning
    "ReasoningOrchestrator",
    "ReasoningRequest",
    "ReasoningResponse",
    "TaskType",
    "ReasoningModel",
    # Layer 6 - Code Context & Fix Proposal
    "CodeContextEngine",
    "CodeFile",
    "ImpactAnalysis",
    "FixProposalEngine",
    "FixProposal",
    "FixType",
    "FixRiskLevel",
    "RollbackPlan",
    # Layer 7 - Approval & Action
    "ApprovalGate",
    "ApprovalPolicy",
    "ApprovalStatus",
    "RiskLevel",
    "ActionExecutor",
    "Action",
    "ActionResult",
    "ActionType",
    # Layer 8 - Execution
    "ExecutionEngine",
    "ExecutionRecord",
    "ExecutionStatus",
    # Layer 9 - Verification
    "VerificationEngine",
    "VerificationResult",
    "VerificationCheck",
    "VerificationStatus",
    "VerificationType",
    # Layer 10 - Trust
    "TrustLedger",
    "TrustReport",
    "TrustState",
    "EvidenceRecord",
    "EvidenceType",
]
