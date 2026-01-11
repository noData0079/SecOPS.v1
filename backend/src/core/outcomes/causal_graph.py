"""
Causal Graph - Attribute success/failure to specific actions.

This answers: "Which action actually fixed the issue?"
Critical for learning WHAT works, not just IF something worked.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class CausalRelation(str, Enum):
    """Types of causal relationships."""
    CAUSED = "caused"           # A directly caused B
    CONTRIBUTED = "contributed" # A contributed to B
    CORRELATED = "correlated"   # A and B happened together
    BLOCKED = "blocked"         # A prevented B
    UNKNOWN = "unknown"


@dataclass
class CausalNode:
    """A node in the causal graph."""
    id: str
    event_type: str  # "action", "outcome", "state_change"
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Edges
    causes: List[str] = field(default_factory=list)      # This node was caused by
    effects: List[str] = field(default_factory=list)     # This node caused


@dataclass
class CausalEdge:
    """An edge representing causal relationship."""
    source_id: str
    target_id: str
    relation: CausalRelation
    confidence: float = 0.5  # How confident we are in this relationship
    evidence: List[str] = field(default_factory=list)


@dataclass
class CausalAttribution:
    """Attribution of an outcome to actions."""
    outcome_id: str
    primary_cause: Optional[str] = None  # Main action that caused outcome
    contributors: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""


class CausalGraph:
    """
    Builds and queries causal relationships between actions and outcomes.
    
    This is essential for learning:
    - Which action fixed the issue
    - Which action made things worse
    - What sequence of actions works best
    """
    
    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: List[CausalEdge] = []
        self._adjacency: Dict[str, Set[str]] = {}  # source -> targets
    
    def add_action(
        self,
        action_id: str,
        tool: str,
        args: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> CausalNode:
        """Add an action node."""
        node = CausalNode(
            id=action_id,
            event_type="action",
            data={"tool": tool, "args": args},
            timestamp=timestamp or datetime.now(),
        )
        self.nodes[action_id] = node
        return node
    
    def add_outcome(
        self,
        outcome_id: str,
        success: bool,
        score: float,
        timestamp: Optional[datetime] = None,
    ) -> CausalNode:
        """Add an outcome node."""
        node = CausalNode(
            id=outcome_id,
            event_type="outcome",
            data={"success": success, "score": score},
            timestamp=timestamp or datetime.now(),
        )
        self.nodes[outcome_id] = node
        return node
    
    def add_state_change(
        self,
        state_id: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> CausalNode:
        """Add a state change node."""
        node = CausalNode(
            id=state_id,
            event_type="state_change",
            data={"before": before, "after": after},
            timestamp=timestamp or datetime.now(),
        )
        self.nodes[state_id] = node
        return node
    
    def link(
        self,
        source_id: str,
        target_id: str,
        relation: CausalRelation,
        confidence: float = 0.5,
        evidence: Optional[List[str]] = None,
    ) -> CausalEdge:
        """Create a causal link between nodes."""
        edge = CausalEdge(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            confidence=confidence,
            evidence=evidence or [],
        )
        self.edges.append(edge)
        
        # Update adjacency
        if source_id not in self._adjacency:
            self._adjacency[source_id] = set()
        self._adjacency[source_id].add(target_id)
        
        # Update node references
        if source_id in self.nodes:
            self.nodes[source_id].effects.append(target_id)
        if target_id in self.nodes:
            self.nodes[target_id].causes.append(source_id)
        
        return edge
    
    def attribute_outcome(
        self,
        outcome_id: str,
        actions: List[str],
    ) -> CausalAttribution:
        """
        Attribute an outcome to the most likely causing action(s).
        
        Uses:
        - Temporal proximity
        - Action-outcome correlation history
        - State change analysis
        """
        if outcome_id not in self.nodes:
            return CausalAttribution(outcome_id=outcome_id)
        
        outcome_node = self.nodes[outcome_id]
        outcome_time = outcome_node.timestamp
        
        # Score each action by likelihood of causing this outcome
        action_scores: Dict[str, float] = {}
        
        for action_id in actions:
            if action_id not in self.nodes:
                continue
            
            action_node = self.nodes[action_id]
            score = 0.0
            
            # Factor 1: Temporal proximity (closer = more likely cause)
            time_diff = (outcome_time - action_node.timestamp).total_seconds()
            if time_diff > 0:
                score += max(0, 50 - time_diff)  # Up to 50 points for proximity
            
            # Factor 2: Direct link exists
            if action_id in outcome_node.causes:
                score += 30
            
            # Factor 3: Tool-outcome correlation (from historical data)
            tool = action_node.data.get("tool", "")
            success = outcome_node.data.get("success", False)
            if success and tool in ["restart_service", "rollback_deploy"]:
                score += 20  # Known effective tools
            
            action_scores[action_id] = score
        
        if not action_scores:
            return CausalAttribution(
                outcome_id=outcome_id,
                reasoning="No action candidates found",
            )
        
        # Find primary cause and contributors
        sorted_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
        primary_cause = sorted_actions[0][0]
        primary_score = sorted_actions[0][1]
        
        contributors = [
            action_id for action_id, score in sorted_actions[1:]
            if score > primary_score * 0.5  # More than 50% of primary
        ]
        
        # Calculate confidence
        total_score = sum(action_scores.values())
        confidence = primary_score / total_score if total_score > 0 else 0
        
        attribution = CausalAttribution(
            outcome_id=outcome_id,
            primary_cause=primary_cause,
            contributors=contributors,
            confidence=confidence,
            reasoning=f"Primary action {primary_cause} scored {primary_score:.1f} out of {total_score:.1f} total",
        )
        
        # Create causal links
        self.link(
            primary_cause,
            outcome_id,
            CausalRelation.CAUSED,
            confidence=confidence,
            evidence=[f"Score: {primary_score:.1f}"],
        )
        
        for contributor in contributors:
            self.link(
                contributor,
                outcome_id,
                CausalRelation.CONTRIBUTED,
                confidence=action_scores[contributor] / total_score,
            )
        
        logger.info(
            f"Attributed outcome {outcome_id} to {primary_cause} "
            f"(confidence: {confidence:.2f})"
        )
        
        return attribution
    
    def get_action_effectiveness(self, tool: str) -> Dict[str, Any]:
        """Get effectiveness statistics for a tool."""
        success_count = 0
        failure_count = 0
        total_confidence = 0.0
        
        for edge in self.edges:
            if edge.relation not in (CausalRelation.CAUSED, CausalRelation.CONTRIBUTED):
                continue
            
            source_node = self.nodes.get(edge.source_id)
            target_node = self.nodes.get(edge.target_id)
            
            if not source_node or not target_node:
                continue
            
            if source_node.data.get("tool") != tool:
                continue
            
            if target_node.event_type == "outcome":
                if target_node.data.get("success"):
                    success_count += 1
                else:
                    failure_count += 1
                total_confidence += edge.confidence
        
        total = success_count + failure_count
        return {
            "tool": tool,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / total if total > 0 else 0,
            "avg_confidence": total_confidence / total if total > 0 else 0,
        }


__all__ = [
    "CausalGraph",
    "CausalNode",
    "CausalEdge",
    "CausalRelation",
    "CausalAttribution",
]
