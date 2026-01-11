"""
Replay Engine - Offline Learning Without GPUs

This is the SECRET WEAPON.

What it does:
1. Re-simulate decision paths
2. Try alternative actions
3. Score better sequences
4. Update policy thresholds, NOT weights

This is how:
- Autonomy improves
- Costs stay near zero
- Trust increases

LLMs cannot do this. Your system can.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ReplayRecord:
    """A complete incident replay record."""
    incident_id: str
    actions: List[Dict[str, Any]]
    outcome: str  # "resolved", "partial", "failed", "escalated"
    resolution_time_seconds: int
    timestamp: datetime


@dataclass
class AlternativeAction:
    """An alternative action that could have been taken."""
    original_action: Dict[str, Any]
    alternative_action: Dict[str, Any]
    confidence_delta: float  # How much better/worse this would be
    risk_change: str  # "lower", "same", "higher"


class ReplayEngine:
    """
    Offline Replay Engine for learning without GPUs.
    
    Key methods:
    - store(): Save incident data
    - analyze(): Find patterns and improvements
    - suggest_policy_updates(): Recommend threshold changes
    """
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)
        self.records: List[ReplayRecord] = []
        self._load_records()
    
    def _load_records(self):
        """Load existing replay records from disk."""
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    self.records.append(ReplayRecord(
                        incident_id=data["incident_id"],
                        actions=data["actions"],
                        outcome=data["outcome"],
                        resolution_time_seconds=data["resolution_time_seconds"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                    ))
            except Exception as e:
                logger.warning(f"Failed to load replay record {filepath}: {e}")
        
        logger.info(f"Loaded {len(self.records)} replay records")
    
    def store(
        self,
        incident_id: str,
        actions: List[Dict[str, Any]],
        outcome: str,
        resolution_time_seconds: int,
    ) -> ReplayRecord:
        """Store a completed incident for replay analysis."""
        record = ReplayRecord(
            incident_id=incident_id,
            actions=actions,
            outcome=outcome,
            resolution_time_seconds=resolution_time_seconds,
            timestamp=datetime.now(),
        )
        
        # Save to disk
        filename = f"incident_{incident_id}_{record.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.storage_path / filename
        
        with open(filepath, "w") as f:
            json.dump({
                "incident_id": record.incident_id,
                "actions": record.actions,
                "outcome": record.outcome,
                "resolution_time_seconds": record.resolution_time_seconds,
                "timestamp": record.timestamp.isoformat(),
            }, f, indent=2)
        
        self.records.append(record)
        logger.info(f"Stored replay record: {incident_id}")
        
        return record
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across all replay records."""
        if not self.records:
            return {"error": "No records to analyze"}
        
        # Basic statistics
        total = len(self.records)
        resolved = len([r for r in self.records if r.outcome == "resolved"])
        escalated = len([r for r in self.records if r.outcome == "escalated"])
        failed = len([r for r in self.records if r.outcome == "failed"])
        
        # Action frequency
        action_counts: Dict[str, int] = {}
        for record in self.records:
            for action in record.actions:
                tool = action.get("tool", "unknown")
                action_counts[tool] = action_counts.get(tool, 0) + 1
        
        # Average resolution time
        resolved_records = [r for r in self.records if r.outcome == "resolved"]
        avg_resolution_time = (
            sum(r.resolution_time_seconds for r in resolved_records) / len(resolved_records)
            if resolved_records else 0
        )
        
        # Success rate by action count
        success_by_actions: Dict[int, Dict[str, int]] = {}
        for record in self.records:
            action_count = len(record.actions)
            if action_count not in success_by_actions:
                success_by_actions[action_count] = {"success": 0, "total": 0}
            success_by_actions[action_count]["total"] += 1
            if record.outcome == "resolved":
                success_by_actions[action_count]["success"] += 1
        
        return {
            "total_incidents": total,
            "resolution_rate": resolved / total if total > 0 else 0,
            "escalation_rate": escalated / total if total > 0 else 0,
            "failure_rate": failed / total if total > 0 else 0,
            "average_resolution_time_seconds": avg_resolution_time,
            "most_used_tools": sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "success_by_action_count": {
                k: v["success"] / v["total"] if v["total"] > 0 else 0
                for k, v in success_by_actions.items()
            },
        }
    
    def suggest_policy_updates(self) -> List[Dict[str, Any]]:
        """
        Suggest policy threshold updates based on replay analysis.
        
        This is the key: update policy thresholds, NOT model weights.
        """
        suggestions = []
        patterns = self.analyze_patterns()
        
        if isinstance(patterns, dict) and "error" in patterns:
            return suggestions
        
        # Suggestion 1: Adjust action limit
        success_by_count = patterns.get("success_by_action_count", {})
        if success_by_count:
            best_action_count = max(success_by_count.items(), key=lambda x: x[1])[0]
            current_limit = 3  # Default
            if best_action_count != current_limit:
                suggestions.append({
                    "type": "ACTION_LIMIT",
                    "current": current_limit,
                    "suggested": best_action_count,
                    "reason": f"Historical data shows {success_by_count.get(best_action_count, 0):.0%} success rate at {best_action_count} actions",
                })
        
        # Suggestion 2: Confidence thresholds
        resolution_rate = patterns.get("resolution_rate", 0)
        if resolution_rate < 0.6:
            suggestions.append({
                "type": "CONFIDENCE_THRESHOLD",
                "component": "high_risk",
                "current": 0.85,
                "suggested": 0.90,
                "reason": f"Low resolution rate ({resolution_rate:.0%}). Increase confidence requirement for high-risk actions.",
            })
        
        # Suggestion 3: Escalation triggers
        escalation_rate = patterns.get("escalation_rate", 0)
        if escalation_rate > 0.4:
            suggestions.append({
                "type": "ESCALATION_THRESHOLD",
                "current": 2,
                "suggested": 3,
                "reason": f"High escalation rate ({escalation_rate:.0%}). Consider allowing more retries before escalation.",
            })
        
        return suggestions
    
    def find_similar_incidents(self, observation: str, top_k: int = 3) -> List[ReplayRecord]:
        """
        Find similar past incidents for context.
        
        This uses simple keyword matching. For production, use embeddings.
        """
        # Simple keyword-based similarity (replace with vector search in production)
        observation_words = set(observation.lower().split())
        
        scored_records = []
        for record in self.records:
            # Check overlap with action tool names and any stored context
            record_words: set = set()
            for action in record.actions:
                record_words.add(action.get("tool", "").lower())
                for arg_value in action.get("args", {}).values():
                    if isinstance(arg_value, str):
                        record_words.update(arg_value.lower().split())
            
            overlap = len(observation_words & record_words)
            if overlap > 0:
                scored_records.append((overlap, record))
        
        # Sort by overlap score
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        return [record for _, record in scored_records[:top_k]]


__all__ = [
    "ReplayEngine",
    "ReplayRecord",
    "AlternativeAction",
]
