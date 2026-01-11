"""
Policy Memory - Track which rules are brittle or effective.

This enables:
- Policy confidence scoring
- Identifying rules that need review
- Safe policy evolution
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PolicyRecord:
    """Record of a policy's performance."""
    policy_id: str
    rule_type: str  # "risk_gate", "action_limit", "environment_block", etc.
    
    # Effectiveness tracking
    times_applied: int = 0
    times_effective: int = 0  # Led to good outcome
    times_bypassed: int = 0   # Was overridden
    times_wrong: int = 0      # Led to bad outcome
    
    # Confidence
    confidence: float = 0.5
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    last_applied: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Metadata
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def effectiveness_rate(self) -> float:
        if self.times_applied == 0:
            return 0.5
        return self.times_effective / self.times_applied
    
    @property
    def is_brittle(self) -> bool:
        """A policy is brittle if it's often wrong or bypassed."""
        if self.times_applied < 5:
            return False  # Not enough data
        wrong_rate = (self.times_wrong + self.times_bypassed) / self.times_applied
        return wrong_rate > 0.3


class PolicyMemory:
    """
    Memory for policy performance tracking.
    
    Enables:
    - Identifying which policies work
    - Which need adjustment
    - Safe evolution over time
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/policy_memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.policies: Dict[str, PolicyRecord] = {}
        self._load()
    
    def register_policy(
        self,
        policy_id: str,
        rule_type: str,
        description: str = "",
    ) -> PolicyRecord:
        """Register a new policy for tracking."""
        if policy_id in self.policies:
            return self.policies[policy_id]
        
        record = PolicyRecord(
            policy_id=policy_id,
            rule_type=rule_type,
            description=description,
        )
        self.policies[policy_id] = record
        self._persist()
        return record
    
    def record_application(
        self,
        policy_id: str,
        was_effective: bool,
        was_bypassed: bool = False,
    ):
        """Record a policy application."""
        if policy_id not in self.policies:
            self.register_policy(policy_id, "unknown")
        
        record = self.policies[policy_id]
        record.times_applied += 1
        record.last_applied = datetime.now()
        
        if was_bypassed:
            record.times_bypassed += 1
            record.confidence = max(0.1, record.confidence - 0.05)
        elif was_effective:
            record.times_effective += 1
            record.confidence = min(0.99, record.confidence + 0.02)
        else:
            record.times_wrong += 1
            record.confidence = max(0.1, record.confidence - 0.08)
        
        record.last_updated = datetime.now()
        self._persist()
        
        logger.debug(
            f"Policy {policy_id}: applied={record.times_applied}, "
            f"confidence={record.confidence:.2f}"
        )
    
    def get_policy_confidence(self, policy_id: str) -> float:
        """Get confidence score for a policy."""
        if policy_id in self.policies:
            return self.policies[policy_id].confidence
        return 0.5  # Default
    
    def get_brittle_policies(self) -> List[PolicyRecord]:
        """Get policies that need review."""
        return [p for p in self.policies.values() if p.is_brittle]
    
    def get_effective_policies(self, threshold: float = 0.7) -> List[PolicyRecord]:
        """Get policies with high effectiveness."""
        return [
            p for p in self.policies.values()
            if p.effectiveness_rate >= threshold and p.times_applied >= 5
        ]
    
    def get_unused_policies(self, days: int = 30) -> List[PolicyRecord]:
        """Get policies not applied recently."""
        threshold = datetime.now()
        from datetime import timedelta
        threshold = threshold - timedelta(days=days)
        
        return [
            p for p in self.policies.values()
            if p.last_applied is None or p.last_applied < threshold
        ]
    
    def suggest_policy_changes(self) -> List[Dict[str, Any]]:
        """Suggest policy changes based on performance."""
        suggestions = []
        
        # Brittle policies need tightening or removal
        for policy in self.get_brittle_policies():
            suggestions.append({
                "policy_id": policy.policy_id,
                "action": "review",
                "reason": f"High failure rate ({policy.times_wrong}/{policy.times_applied})",
                "current_confidence": policy.confidence,
            })
        
        # Unused policies might be obsolete
        for policy in self.get_unused_policies():
            suggestions.append({
                "policy_id": policy.policy_id,
                "action": "consider_removal",
                "reason": f"Not applied in 30+ days",
            })
        
        return suggestions
    
    def export_report(self) -> Dict[str, Any]:
        """Export full policy memory report."""
        return {
            "total_policies": len(self.policies),
            "policies": [
                {
                    "policy_id": p.policy_id,
                    "rule_type": p.rule_type,
                    "times_applied": p.times_applied,
                    "effectiveness_rate": p.effectiveness_rate,
                    "confidence": p.confidence,
                    "is_brittle": p.is_brittle,
                }
                for p in self.policies.values()
            ],
            "brittle_count": len(self.get_brittle_policies()),
            "effective_count": len(self.get_effective_policies()),
            "exported_at": datetime.now().isoformat(),
        }
    
    def _persist(self):
        filepath = self.storage_path / "policies.json"
        with open(filepath, "w") as f:
            json.dump({
                pid: {
                    "policy_id": p.policy_id,
                    "rule_type": p.rule_type,
                    "times_applied": p.times_applied,
                    "times_effective": p.times_effective,
                    "times_bypassed": p.times_bypassed,
                    "times_wrong": p.times_wrong,
                    "confidence": p.confidence,
                    "created_at": p.created_at.isoformat(),
                    "last_applied": p.last_applied.isoformat() if p.last_applied else None,
                    "last_updated": p.last_updated.isoformat(),
                    "description": p.description,
                    "metadata": p.metadata,
                }
                for pid, p in self.policies.items()
            }, f, indent=2)
    
    def _load(self):
        filepath = self.storage_path / "policies.json"
        if not filepath.exists():
            return
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            for pid, pd in data.items():
                self.policies[pid] = PolicyRecord(
                    policy_id=pd["policy_id"],
                    rule_type=pd["rule_type"],
                    times_applied=pd.get("times_applied", 0),
                    times_effective=pd.get("times_effective", 0),
                    times_bypassed=pd.get("times_bypassed", 0),
                    times_wrong=pd.get("times_wrong", 0),
                    confidence=pd.get("confidence", 0.5),
                    created_at=datetime.fromisoformat(pd["created_at"]),
                    last_applied=datetime.fromisoformat(pd["last_applied"]) if pd.get("last_applied") else None,
                    last_updated=datetime.fromisoformat(pd["last_updated"]),
                    description=pd.get("description", ""),
                    metadata=pd.get("metadata", {}),
                )
        except Exception as e:
            logger.warning(f"Failed to load policy memory: {e}")


__all__ = [
    "PolicyMemory",
    "PolicyRecord",
]
