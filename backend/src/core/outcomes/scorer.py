"""
Outcome Scorer - Convert action results into numeric intelligence.

This is CRITICAL for real autonomy:
- Scores actions (0-100)
- Provides learning signal
- Feeds confidence updates
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OutcomeCategory(str, Enum):
    """Categories of outcomes."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    ESCALATED = "escalated"


@dataclass
class OutcomeScore:
    """Scored outcome with attribution."""
    score: float  # 0-100
    category: OutcomeCategory
    confidence: float  # 0-1, how confident we are in this score
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_positive(self) -> bool:
        return self.score >= 70
    
    @property
    def is_learning_signal(self) -> bool:
        """High-confidence scores provide better learning signals."""
        return self.confidence >= 0.7


@dataclass
class ActionOutcome:
    """Complete outcome record for an action."""
    action_id: str
    incident_id: str
    tool_used: str
    args: Dict[str, Any]
    
    # Result
    success: bool
    error: Optional[str] = None
    side_effects: bool = False
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Scoring (filled by OutcomeScorer)
    score: Optional[OutcomeScore] = None
    
    @property
    def duration_ms(self) -> int:
        if self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return 0


class OutcomeScorer:
    """
    Scores action outcomes to generate learning signals.
    
    Scoring factors:
    - Immediate success/failure
    - Time to resolution
    - Side effects
    - Resource usage
    - Downstream impact
    """
    
    def __init__(self):
        # Configurable weights
        self.weights = {
            "success": 40.0,
            "speed": 20.0,
            "no_side_effects": 15.0,
            "first_attempt": 15.0,
            "low_risk": 10.0,
        }
        
        # Historical baselines (updated by learning)
        self.baselines = {
            "avg_resolution_time_ms": 5000,
            "avg_attempts": 1.5,
        }
    
    def score(
        self,
        outcome: ActionOutcome,
        context: Optional[Dict[str, Any]] = None,
    ) -> OutcomeScore:
        """
        Score an action outcome.
        
        Args:
            outcome: The action outcome to score
            context: Additional context (incident history, tool history, etc.)
        
        Returns:
            OutcomeScore with numeric score and breakdown
        """
        context = context or {}
        factors: Dict[str, float] = {}
        
        # Factor 1: Success/Failure (40 points max)
        if outcome.success:
            factors["success"] = self.weights["success"]
        else:
            factors["success"] = 0.0
        
        # Factor 2: Speed (20 points max)
        if outcome.duration_ms > 0:
            speed_ratio = self.baselines["avg_resolution_time_ms"] / max(outcome.duration_ms, 1)
            factors["speed"] = min(self.weights["speed"], self.weights["speed"] * speed_ratio)
        else:
            factors["speed"] = self.weights["speed"] * 0.5  # Unknown speed
        
        # Factor 3: No side effects (15 points max)
        if not outcome.side_effects:
            factors["no_side_effects"] = self.weights["no_side_effects"]
        else:
            factors["no_side_effects"] = 0.0
        
        # Factor 4: First attempt success (15 points max)
        attempt_number = context.get("attempt_number", 1)
        if attempt_number == 1 and outcome.success:
            factors["first_attempt"] = self.weights["first_attempt"]
        else:
            factors["first_attempt"] = max(0, self.weights["first_attempt"] - (attempt_number - 1) * 5)
        
        # Factor 5: Low risk action (10 points max)
        risk_level = context.get("risk_level", "medium")
        risk_scores = {"none": 10, "low": 8, "medium": 5, "high": 2}
        factors["low_risk"] = risk_scores.get(risk_level, 5)
        
        # Calculate total score
        total_score = sum(factors.values())
        
        # Determine category
        if total_score >= 80:
            category = OutcomeCategory.SUCCESS
        elif total_score >= 50:
            category = OutcomeCategory.PARTIAL_SUCCESS
        elif outcome.error and "timeout" in outcome.error.lower():
            category = OutcomeCategory.TIMEOUT
        else:
            category = OutcomeCategory.FAILURE
        
        # Calculate confidence in score
        confidence = self._calculate_confidence(outcome, context)
        
        score = OutcomeScore(
            score=total_score,
            category=category,
            confidence=confidence,
            factors=factors,
        )
        
        outcome.score = score
        logger.info(f"Scored action {outcome.action_id}: {total_score:.1f} ({category.value})")
        
        return score
    
    def _calculate_confidence(
        self,
        outcome: ActionOutcome,
        context: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the score."""
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if context.get("historical_data_points", 0) > 10:
            confidence += 0.2
        
        # Clear success/failure = higher confidence
        if outcome.success and not outcome.side_effects:
            confidence += 0.2
        elif not outcome.success and outcome.error:
            confidence += 0.1
        
        # Known tool = higher confidence
        if context.get("tool_known", False):
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def update_baselines(self, outcomes: List[ActionOutcome]):
        """Update baselines from historical outcomes."""
        if not outcomes:
            return
        
        # Update average resolution time
        times = [o.duration_ms for o in outcomes if o.duration_ms > 0]
        if times:
            self.baselines["avg_resolution_time_ms"] = sum(times) / len(times)
        
        logger.info(f"Updated baselines: {self.baselines}")


class OutcomeBatcher:
    """Batches outcomes for efficient processing."""
    
    def __init__(self, scorer: OutcomeScorer, batch_size: int = 100):
        self.scorer = scorer
        self.batch_size = batch_size
        self.pending: List[ActionOutcome] = []
    
    def add(self, outcome: ActionOutcome) -> Optional[OutcomeScore]:
        """Add outcome and score immediately."""
        score = self.scorer.score(outcome)
        self.pending.append(outcome)
        
        if len(self.pending) >= self.batch_size:
            self.flush()
        
        return score
    
    def flush(self):
        """Flush pending outcomes and update baselines."""
        if self.pending:
            self.scorer.update_baselines(self.pending)
            self.pending = []


__all__ = [
    "OutcomeScorer",
    "OutcomeScore",
    "ActionOutcome",
    "OutcomeCategory",
    "OutcomeBatcher",
]
