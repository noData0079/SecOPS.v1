"""
Policy Engine - Deterministic Rules (NO ML)

This is the MOAT. The model is never trusted to execute.
All decisions pass through this policy layer.

Rules:
- Deterministic
- Auditable
- Explainable
- Trusted by enterprises
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PolicyDecision(str, Enum):
    """Possible policy decisions."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class RiskLevel(str, Enum):
    """Risk levels for tools."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class AgentState:
    """Current state of the agent loop."""
    actions_taken: int = 0
    environment: str = "development"
    max_actions: int = 3
    escalation_count: int = 0
    last_action_failed: bool = False


@dataclass
class ProposedAction:
    """Action proposed by the model."""
    tool: str
    args: Dict[str, Any]
    confidence: float
    risk: RiskLevel
    prod_allowed: bool


def policy_check(action: ProposedAction, state: AgentState) -> PolicyDecision:
    """
    Core policy check - NO ML, pure rules.
    
    This is the function that prevents disasters.
    """
    
    # Rule 1: Action limit
    if state.actions_taken >= state.max_actions:
        logger.warning(f"Action limit reached ({state.max_actions}). Escalating.")
        return PolicyDecision.ESCALATE
    
    # Rule 2: High-risk actions require high confidence
    if action.risk == RiskLevel.HIGH and action.confidence < 0.85:
        logger.warning(
            f"High-risk action '{action.tool}' has low confidence ({action.confidence:.2f}). Escalating."
        )
        return PolicyDecision.ESCALATE
    
    # Rule 3: Block prod-disallowed actions in prod
    if not action.prod_allowed and state.environment == "production":
        logger.warning(
            f"Action '{action.tool}' is not allowed in production. Blocking."
        )
        return PolicyDecision.BLOCK
    
    # Rule 4: Escalate after consecutive failures
    if state.last_action_failed and state.escalation_count >= 2:
        logger.warning("Multiple failures detected. Escalating.")
        return PolicyDecision.ESCALATE
    
    # Rule 5: Medium-risk actions need moderate confidence
    if action.risk == RiskLevel.MEDIUM and action.confidence < 0.70:
        logger.warning(
            f"Medium-risk action '{action.tool}' has insufficient confidence ({action.confidence:.2f}). Escalating."
        )
        return PolicyDecision.ESCALATE
    
    # All checks passed
    logger.info(f"Action '{action.tool}' ALLOWED with confidence {action.confidence:.2f}")
    return PolicyDecision.ALLOW


def validate_action_schema(action: Dict[str, Any], tool_registry: Dict[str, Any]) -> bool:
    """Validate that the action matches the tool registry schema."""
    tool_name = action.get("tool")
    
    if tool_name not in tool_registry:
        logger.error(f"Unknown tool: {tool_name}")
        return False
    
    tool_spec = tool_registry[tool_name]
    required_inputs = tool_spec.get("inputs", [])
    provided_args = action.get("args", {})
    
    for required_input in required_inputs:
        if required_input not in provided_args:
            logger.error(f"Missing required input '{required_input}' for tool '{tool_name}'")
            return False
    
    return True


class PolicyEngine:
    """
    Main Policy Engine class.
    
    Usage:
        engine = PolicyEngine(tool_registry)
        decision = engine.evaluate(proposed_action, agent_state)
    """
    
    def __init__(self, tool_registry: Dict[str, Any]):
        self.tool_registry = tool_registry
        self.decision_log: list = []
    
    def evaluate(
        self, 
        action_dict: Dict[str, Any], 
        state: AgentState
    ) -> tuple[PolicyDecision, Optional[str]]:
        """
        Evaluate a proposed action against policy rules.
        
        Returns:
            (decision, reason) tuple
        """
        # Schema validation
        if not validate_action_schema(action_dict, self.tool_registry):
            return PolicyDecision.BLOCK, "Schema validation failed"
        
        tool_name = action_dict["tool"]
        tool_spec = self.tool_registry[tool_name]
        
        # Build ProposedAction
        action = ProposedAction(
            tool=tool_name,
            args=action_dict.get("args", {}),
            confidence=action_dict.get("confidence", 0.0),
            risk=RiskLevel(tool_spec.get("risk", "none")),
            prod_allowed=tool_spec.get("prod_allowed", False),
        )
        
        # Run policy check
        decision = policy_check(action, state)
        
        # Log decision
        self.decision_log.append({
            "tool": tool_name,
            "confidence": action.confidence,
            "decision": decision.value,
            "state": {
                "actions_taken": state.actions_taken,
                "environment": state.environment,
            }
        })
        
        reason = None
        if decision == PolicyDecision.BLOCK:
            reason = f"Action '{tool_name}' blocked by policy"
        elif decision == PolicyDecision.ESCALATE:
            reason = f"Action '{tool_name}' requires human review"
        
        return decision, reason


__all__ = [
    "PolicyEngine",
    "PolicyDecision",
    "RiskLevel",
    "AgentState",
    "ProposedAction",
    "policy_check",
]
