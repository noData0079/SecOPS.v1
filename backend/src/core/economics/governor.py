"""
Economic Governor - Cost control and budget enforcement.

ENTERPRISE REQUIRED:
- Cost budget per tenant
- Action cost estimation
- ROI scoring
- Emergency cost cut-off

Autonomy without cost control = bankruptcy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.memory.economic_memory import EconomicMemory, CostBudget

logger = logging.getLogger(__name__)


@dataclass
class CostDecision:
    """Decision about whether to proceed based on cost."""
    allowed: bool
    reason: str
    estimated_cost: float
    remaining_budget: float
    roi_score: float


class EconomicGovernor:
    """
    Enforces cost governance for autonomous actions.
    
    Features:
    - Budget enforcement
    - Cost estimation
    - ROI-based prioritization
    - Emergency cost cut-off
    """
    
    def __init__(self, economic_memory: Optional[EconomicMemory] = None):
        self.memory = economic_memory or EconomicMemory()
        
        # Emergency mode
        self.emergency_cutoff_active = False
        self.cutoff_reason: Optional[str] = None
        
        # ROI threshold
        self.min_roi_threshold = 0.5  # Minimum ROI to allow action
    
    def can_afford(
        self,
        tenant_id: str,
        tool: str,
        incident_severity: str = "medium",
    ) -> CostDecision:
        """
        Check if an action can be afforded.
        
        Args:
            tenant_id: Tenant identifier
            tool: Tool to use
            incident_severity: Severity of incident being addressed
        
        Returns:
            CostDecision with allow/deny and reasoning
        """
        # Emergency cutoff check
        if self.emergency_cutoff_active:
            return CostDecision(
                allowed=False,
                reason=f"Emergency cost cutoff: {self.cutoff_reason}",
                estimated_cost=0,
                remaining_budget=0,
                roi_score=0,
            )
        
        # Get budget
        budget = self.memory.get_budget(tenant_id)
        if not budget:
            # No budget = no limits (but log warning)
            logger.warning(f"No budget set for tenant {tenant_id}")
            return CostDecision(
                allowed=True,
                reason="No budget configured",
                estimated_cost=self.memory.estimate_action_cost(tool),
                remaining_budget=float('inf'),
                roi_score=1.0,
            )
        
        # Estimate cost
        estimated_cost = self.memory.estimate_action_cost(tool)
        
        # Check budget
        can_afford, budget_reason = self.memory.can_afford_action(tenant_id, tool)
        
        if not can_afford:
            return CostDecision(
                allowed=False,
                reason=budget_reason,
                estimated_cost=estimated_cost,
                remaining_budget=budget.daily_remaining,
                roi_score=0,
            )
        
        # Calculate expected ROI
        severity_values = {"critical": 10000, "high": 5000, "medium": 1000, "low": 100}
        expected_value = severity_values.get(incident_severity, 1000) * 0.7  # Assume 70% success
        roi = expected_value / max(0.001, estimated_cost)
        
        # ROI check (skip for very low cost)
        if estimated_cost > 0.1 and roi < self.min_roi_threshold:
            return CostDecision(
                allowed=False,
                reason=f"ROI too low ({roi:.2f} < {self.min_roi_threshold})",
                estimated_cost=estimated_cost,
                remaining_budget=budget.daily_remaining,
                roi_score=roi,
            )
        
        return CostDecision(
            allowed=True,
            reason="Within budget and ROI threshold",
            estimated_cost=estimated_cost,
            remaining_budget=budget.daily_remaining,
            roi_score=roi,
        )
    
    def activate_emergency_cutoff(self, reason: str):
        """Activate emergency cost cutoff."""
        self.emergency_cutoff_active = True
        self.cutoff_reason = reason
        logger.critical(f"EMERGENCY COST CUTOFF ACTIVATED: {reason}")
    
    def deactivate_emergency_cutoff(self):
        """Deactivate emergency cost cutoff."""
        self.emergency_cutoff_active = False
        self.cutoff_reason = None
        logger.info("Emergency cost cutoff deactivated")
    
    def prioritize_actions(
        self,
        tenant_id: str,
        actions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Prioritize actions by ROI.
        
        Args:
            tenant_id: Tenant identifier
            actions: List of potential actions with 'tool' and 'severity' keys
        
        Returns:
            Actions sorted by ROI (highest first)
        """
        scored_actions = []
        
        for action in actions:
            decision = self.can_afford(
                tenant_id,
                action.get("tool", "unknown"),
                action.get("severity", "medium"),
            )
            
            scored_actions.append({
                **action,
                "_roi": decision.roi_score,
                "_cost": decision.estimated_cost,
                "_allowed": decision.allowed,
            })
        
        # Sort by ROI, filter out disallowed
        sorted_actions = sorted(
            scored_actions,
            key=lambda x: x["_roi"],
            reverse=True
        )
        
        return sorted_actions
    
    def get_spending_report(self, tenant_id: str) -> Dict[str, Any]:
        """Get spending report for a tenant."""
        return self.memory.get_cost_report(tenant_id)
    
    def check_budget_health(self, tenant_id: str) -> Dict[str, Any]:
        """Check budget health for a tenant."""
        budget = self.memory.get_budget(tenant_id)
        if not budget:
            return {"status": "no_budget", "message": "No budget configured"}
        
        daily_pct = (budget.daily_used / budget.daily_limit) * 100 if budget.daily_limit else 0
        monthly_pct = (budget.monthly_used / budget.monthly_limit) * 100 if budget.monthly_limit else 0
        
        if budget.is_over_budget:
            status = "exhausted"
        elif daily_pct > 80 or monthly_pct > 80:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "daily_used_pct": daily_pct,
            "monthly_used_pct": monthly_pct,
            "daily_remaining": budget.daily_remaining,
            "monthly_remaining": budget.monthly_remaining,
        }


# Global instance
economic_governor = EconomicGovernor()


__all__ = [
    "EconomicGovernor",
    "CostDecision",
    "economic_governor",
]
