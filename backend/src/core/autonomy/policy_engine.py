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
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class PolicyDecision(str, Enum):
    """Possible policy decisions."""
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"
    WAIT_APPROVAL = "wait_approval"


class RiskLevel(str, Enum):
    """Risk levels for tools."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ToolState:
    """State tracking for a single tool."""
    confidence: float = 1.0
    failure_count: int = 0
    usage_count: int = 0
    last_used_at: Optional[datetime] = None
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None


@dataclass
class AgentState:
    """Current state of the agent loop."""
    actions_taken: int = 0
    environment: str = "development"
    max_actions: int = 3
    escalation_count: int = 0
    last_action_failed: bool = False
    # Map of tool_name -> ToolState
    tool_states: Dict[str, ToolState] = field(default_factory=dict)


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
    # Assertions for safety boundaries
    assert isinstance(state, AgentState), "Invalid state object"
    assert isinstance(action, ProposedAction), "Invalid action object"
    
    # Get tool state (initialize if not present)
    tool_state = state.tool_states.get(action.tool)
    if not tool_state:
        # Default state
        tool_state = ToolState()
        state.tool_states[action.tool] = tool_state

    # Rule 0: Blacklisted tools are BLOCKED
    if tool_state.is_blacklisted:
        logger.warning(f"Tool '{action.tool}' is blacklisted: {tool_state.blacklist_reason}")
        return PolicyDecision.BLOCK

    # Rule 1: Action limit
    if state.actions_taken >= state.max_actions:
        logger.warning(f"Action limit reached ({state.max_actions}). Escalating.")
        return PolicyDecision.ESCALATE
    
    # Rule 2: Block prod-disallowed actions in prod
    if not action.prod_allowed and state.environment == "production":
        logger.warning(
            f"Action '{action.tool}' is not allowed in production. Blocking."
        )
        return PolicyDecision.BLOCK

    # Rule 3: High-risk actions require HUMAN APPROVAL
    if action.risk == RiskLevel.HIGH:
        logger.info(f"High-risk action '{action.tool}' requires human approval.")
        return PolicyDecision.WAIT_APPROVAL
    
    # Rule 4: Escalate after consecutive failures
    if state.last_action_failed and state.escalation_count >= 2:
        logger.warning("Multiple failures detected. Escalating.")
        return PolicyDecision.ESCALATE
    
    # Rule 5: Medium-risk actions need moderate confidence (Model + Policy)
    # Check both model confidence and policy tool confidence
    if action.risk == RiskLevel.MEDIUM:
        if action.confidence < 0.70:
            logger.warning(
                f"Medium-risk action '{action.tool}' has insufficient model confidence ({action.confidence:.2f}). Escalating."
            )
            return PolicyDecision.ESCALATE
        if tool_state.confidence < 0.5:
             logger.warning(
                f"Medium-risk action '{action.tool}' has insufficient policy confidence ({tool_state.confidence:.2f}). Escalating."
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
    
    # Constants for decay
    DECAY_FACTOR_UNUSED = 0.99
    DECAY_FACTOR_FAILED = 0.95
    MIN_CONFIDENCE = 0.10
    BOOST_FACTOR = 1.05 # Mild boost or reset? "Reinforced". Let's slightly boost up to 1.0.

    # Constants for Blacklisting
    MAX_FAILURES_INCIDENT = 2
    MIN_TOOL_CONFIDENCE_BLACKLIST = 0.2

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
        # Runtime assertions
        assert isinstance(state, AgentState)
        assert isinstance(action_dict, dict)

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

        # Ensure tool state exists
        if tool_name not in state.tool_states:
            state.tool_states[tool_name] = ToolState()
        
        # Run policy check
        decision = policy_check(action, state)
        
        # Runtime Assertion on Decision
        if decision == PolicyDecision.ALLOW:
            assert not state.tool_states[tool_name].is_blacklisted, "Allowed a blacklisted tool!"
            if state.environment == "production":
                assert action.prod_allowed, "Allowed non-prod tool in production!"

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
        elif decision == PolicyDecision.WAIT_APPROVAL:
            reason = f"Action '{tool_name}' waiting for approval token"
        
        return decision, reason

    def update_tool_stats(self, state: AgentState, used_tool_name: str, success: bool) -> None:
        """
        Update tool stats: usage, failure count, and confidence decay.
        """
        # 1. Update the used tool
        if used_tool_name not in state.tool_states:
             state.tool_states[used_tool_name] = ToolState()

        used_tool = state.tool_states[used_tool_name]
        used_tool.usage_count += 1
        used_tool.last_used_at = datetime.now()

        if success:
             # Boost confidence for success
             used_tool.confidence = min(1.0, used_tool.confidence * self.BOOST_FACTOR)
        else:
             used_tool.failure_count += 1
             # Decay for failure
             used_tool.confidence = max(self.MIN_CONFIDENCE, used_tool.confidence * self.DECAY_FACTOR_FAILED)

        # 2. Apply decay to ALL tools (including the one used, if we treat "usage" separate from "time decay"?
        # User said: "Decay happens when: A rule/tool is unused OR used but fails".
        # So successful used tool does NOT decay.
        # Unused tools decay.
        # Failed tools decayed above.

        for tool_name in self.tool_registry.keys():
            if tool_name == used_tool_name:
                continue

            if tool_name not in state.tool_states:
                state.tool_states[tool_name] = ToolState()

            t_state = state.tool_states[tool_name]
            # Unused decay
            t_state.confidence = max(self.MIN_CONFIDENCE, t_state.confidence * self.DECAY_FACTOR_UNUSED)

        # 3. Check Dynamic Blacklisting for ALL tools
        for name, t_state in state.tool_states.items():
            if t_state.is_blacklisted:
                continue # Already blacklisted

            # Check conditions
            if t_state.failure_count >= self.MAX_FAILURES_INCIDENT:
                t_state.is_blacklisted = True
                t_state.blacklist_reason = f"Too many failures ({t_state.failure_count})"

            elif t_state.confidence <= self.MIN_TOOL_CONFIDENCE_BLACKLIST:
                t_state.is_blacklisted = True
                t_state.blacklist_reason = f"Confidence too low ({t_state.confidence:.2f})"

            if t_state.is_blacklisted:
                logger.warning(f"Tool '{name}' has been dynamically BLACKLISTED: {t_state.blacklist_reason}")

__all__ = [
    "PolicyEngine",
    "PolicyDecision",
    "RiskLevel",
    "AgentState",
    "ProposedAction",
    "ToolState",
    "policy_check",
]
