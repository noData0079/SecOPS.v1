"""
Confidence Updater - Updates confidence scores for tools and policies.

This is the learning signal that drives improvement:
- Tool confidence based on outcomes
- Policy confidence based on effectiveness
- Automatic decay for unused rules
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceRecord:
    """Historical confidence record."""
    entity_id: str
    entity_type: str  # "tool" or "policy"
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    reason: str = ""


class ConfidenceUpdater:
    """
    Updates and manages confidence scores.
    
    Key principles:
    - Confidence increases with positive outcomes
    - Confidence decreases with failures
    - Unused entities decay over time
    - All changes are logged for auditability
    """
    
    def __init__(self):
        # Current confidence scores
        self.tool_confidence: Dict[str, float] = {}
        self.policy_confidence: Dict[str, float] = {}
        
        # History for auditing
        self.history: List[ConfidenceRecord] = []
        
        # Configuration
        self.config = {
            "min_confidence": 0.1,
            "max_confidence": 0.99,
            "success_boost": 0.05,
            "failure_penalty": 0.08,
            "decay_rate": 0.01,  # Per day of non-use
            "decay_threshold_days": 7,
        }
    
    def get_tool_confidence(self, tool: str) -> float:
        """Get current confidence for a tool."""
        return self.tool_confidence.get(tool, 0.5)  # Default 50%
    
    def get_policy_confidence(self, policy_id: str) -> float:
        """Get current confidence for a policy."""
        return self.policy_confidence.get(policy_id, 0.5)
    
    def update_tool(
        self,
        tool: str,
        outcome_score: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Update tool confidence based on outcome.
        
        Args:
            tool: Tool name
            outcome_score: Outcome score (0-100)
            context: Additional context
        
        Returns:
            New confidence score
        """
        current = self.get_tool_confidence(tool)
        
        # Calculate adjustment based on outcome
        if outcome_score >= 70:
            # Success: boost confidence
            adjustment = self.config["success_boost"] * (outcome_score / 100)
            reason = f"Success with score {outcome_score:.1f}"
        elif outcome_score >= 40:
            # Partial: small adjustment
            adjustment = (outcome_score - 50) / 1000
            reason = f"Partial success with score {outcome_score:.1f}"
        else:
            # Failure: reduce confidence
            adjustment = -self.config["failure_penalty"] * (1 - outcome_score / 100)
            reason = f"Failure with score {outcome_score:.1f}"
        
        # Apply adjustment with bounds
        new_confidence = max(
            self.config["min_confidence"],
            min(self.config["max_confidence"], current + adjustment)
        )
        
        self.tool_confidence[tool] = new_confidence
        
        # Record history
        self.history.append(ConfidenceRecord(
            entity_id=tool,
            entity_type="tool",
            confidence=new_confidence,
            reason=reason,
        ))
        
        logger.info(
            f"Tool '{tool}' confidence: {current:.3f} -> {new_confidence:.3f} ({reason})"
        )
        
        return new_confidence
    
    def update_policy(
        self,
        policy_id: str,
        was_effective: bool,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Update policy confidence based on effectiveness.
        
        Args:
            policy_id: Policy identifier
            was_effective: Whether the policy led to good outcomes
            context: Additional context
        
        Returns:
            New confidence score
        """
        current = self.get_policy_confidence(policy_id)
        
        if was_effective:
            adjustment = self.config["success_boost"]
            reason = "Policy led to positive outcome"
        else:
            adjustment = -self.config["failure_penalty"]
            reason = "Policy led to negative outcome"
        
        new_confidence = max(
            self.config["min_confidence"],
            min(self.config["max_confidence"], current + adjustment)
        )
        
        self.policy_confidence[policy_id] = new_confidence
        
        self.history.append(ConfidenceRecord(
            entity_id=policy_id,
            entity_type="policy",
            confidence=new_confidence,
            reason=reason,
        ))
        
        logger.info(
            f"Policy '{policy_id}' confidence: {current:.3f} -> {new_confidence:.3f}"
        )
        
        return new_confidence
    
    def apply_decay(self, last_used: Dict[str, datetime]):
        """
        Apply confidence decay to unused entities.
        
        Args:
            last_used: Map of entity_id -> last used timestamp
        """
        now = datetime.now()
        threshold = timedelta(days=self.config["decay_threshold_days"])
        
        # Decay tools
        for tool, confidence in list(self.tool_confidence.items()):
            if tool in last_used:
                days_unused = (now - last_used[tool]).days
                if days_unused > self.config["decay_threshold_days"]:
                    decay = self.config["decay_rate"] * (days_unused - self.config["decay_threshold_days"])
                    new_confidence = max(self.config["min_confidence"], confidence - decay)
                    self.tool_confidence[tool] = new_confidence
                    logger.debug(f"Decayed tool '{tool}': {confidence:.3f} -> {new_confidence:.3f}")
        
        # Decay policies
        for policy_id, confidence in list(self.policy_confidence.items()):
            if policy_id in last_used:
                days_unused = (now - last_used[policy_id]).days
                if days_unused > self.config["decay_threshold_days"]:
                    decay = self.config["decay_rate"] * (days_unused - self.config["decay_threshold_days"])
                    new_confidence = max(self.config["min_confidence"], confidence - decay)
                    self.policy_confidence[policy_id] = new_confidence
    
    def get_low_confidence_tools(self, threshold: float = 0.3) -> List[str]:
        """Get tools with confidence below threshold."""
        return [
            tool for tool, conf in self.tool_confidence.items()
            if conf < threshold
        ]
    
    def get_high_confidence_tools(self, threshold: float = 0.8) -> List[str]:
        """Get tools with confidence above threshold."""
        return [
            tool for tool, conf in self.tool_confidence.items()
            if conf >= threshold
        ]
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state for persistence."""
        return {
            "tool_confidence": dict(self.tool_confidence),
            "policy_confidence": dict(self.policy_confidence),
            "history_count": len(self.history),
            "exported_at": datetime.now().isoformat(),
        }
    
    def import_state(self, state: Dict[str, Any]):
        """Import state from persistence."""
        self.tool_confidence = state.get("tool_confidence", {})
        self.policy_confidence = state.get("policy_confidence", {})
        logger.info(f"Imported confidence state: {len(self.tool_confidence)} tools, {len(self.policy_confidence)} policies")


# Global instance
confidence_updater = ConfidenceUpdater()


__all__ = [
    "ConfidenceUpdater",
    "ConfidenceRecord",
    "confidence_updater",
]
