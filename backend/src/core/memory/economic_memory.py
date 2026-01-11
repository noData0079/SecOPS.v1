"""
Economic Memory - Track cost vs benefit per action.

ENTERPRISE REQUIRED:
- Cost budget per tenant
- Action cost estimation
- ROI scoring
- Emergency cost cut-off
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ActionCost:
    """Cost record for an action."""
    action_id: str
    tool: str
    
    # Cost components
    compute_cost: float = 0.0      # CPU/GPU cost
    api_cost: float = 0.0          # External API calls
    human_time_cost: float = 0.0   # If required human review
    
    # Value delivered
    incident_severity: str = "medium"  # Determines value
    resolution_contribution: float = 0.0  # 0-1, how much it contributed
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def total_cost(self) -> float:
        return self.compute_cost + self.api_cost + self.human_time_cost
    
    @property
    def roi(self) -> float:
        """Return on investment (value / cost)."""
        if self.total_cost == 0:
            return 0
        # Severity to value mapping
        severity_values = {"critical": 10000, "high": 5000, "medium": 1000, "low": 100}
        value = severity_values.get(self.incident_severity, 1000) * self.resolution_contribution
        return value / self.total_cost


@dataclass
class CostBudget:
    """Cost budget for a tenant or time period."""
    budget_id: str
    tenant_id: str
    
    # Budget limits
    daily_limit: float = 100.0
    monthly_limit: float = 2000.0
    
    # Current usage
    daily_used: float = 0.0
    monthly_used: float = 0.0
    
    # Tracking
    period_start: datetime = field(default_factory=datetime.now)
    last_reset: datetime = field(default_factory=datetime.now)
    
    @property
    def daily_remaining(self) -> float:
        return max(0, self.daily_limit - self.daily_used)
    
    @property
    def monthly_remaining(self) -> float:
        return max(0, self.monthly_limit - self.monthly_used)
    
    @property
    def is_over_budget(self) -> bool:
        return self.daily_used >= self.daily_limit or self.monthly_used >= self.monthly_limit


class EconomicMemory:
    """
    Economic intelligence for cost-aware autonomy.
    
    Features:
    - Cost tracking per action
    - Budget management
    - ROI analysis
    - Cost cut-off enforcement
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("./data/economic_memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Cost history
        self.action_costs: List[ActionCost] = []
        
        # Budgets by tenant
        self.budgets: Dict[str, CostBudget] = {}
        
        # Tool cost estimates (base costs)
        self.tool_costs: Dict[str, Dict[str, float]] = {
            "restart_service": {"compute": 0.01, "api": 0.0},
            "scale_pod": {"compute": 0.02, "api": 0.0},
            "rollback_deploy": {"compute": 0.05, "api": 0.0},
            "get_logs": {"compute": 0.001, "api": 0.0},
            "run_diagnostic": {"compute": 0.01, "api": 0.0},
            "apply_patch": {"compute": 0.02, "api": 0.0},
            "update_config": {"compute": 0.01, "api": 0.0},
            "escalate": {"compute": 0.0, "api": 0.0, "human": 10.0},
            # LLM costs
            "llm_call_small": {"compute": 0.0, "api": 0.001},
            "llm_call_large": {"compute": 0.0, "api": 0.03},
        }
        
        self._load()
    
    def set_budget(
        self,
        tenant_id: str,
        daily_limit: float = 100.0,
        monthly_limit: float = 2000.0,
    ) -> CostBudget:
        """Set budget for a tenant."""
        budget = CostBudget(
            budget_id=f"budget_{tenant_id}",
            tenant_id=tenant_id,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
        )
        self.budgets[tenant_id] = budget
        self._persist()
        return budget
    
    def get_budget(self, tenant_id: str) -> Optional[CostBudget]:
        """Get budget for a tenant."""
        return self.budgets.get(tenant_id)
    
    def estimate_action_cost(self, tool: str) -> float:
        """Estimate cost for an action before executing."""
        costs = self.tool_costs.get(tool, {"compute": 0.01, "api": 0.0})
        return sum(costs.values())
    
    def can_afford_action(self, tenant_id: str, tool: str) -> tuple[bool, str]:
        """Check if tenant can afford an action."""
        budget = self.budgets.get(tenant_id)
        if not budget:
            return True, "No budget set"
        
        # Check for reset
        self._check_budget_reset(budget)
        
        estimated_cost = self.estimate_action_cost(tool)
        
        if budget.daily_remaining < estimated_cost:
            return False, f"Daily budget exhausted ({budget.daily_used:.2f}/{budget.daily_limit:.2f})"
        
        if budget.monthly_remaining < estimated_cost:
            return False, f"Monthly budget exhausted ({budget.monthly_used:.2f}/{budget.monthly_limit:.2f})"
        
        return True, "Within budget"
    
    def record_action_cost(
        self,
        tenant_id: str,
        action_id: str,
        tool: str,
        compute_cost: Optional[float] = None,
        api_cost: Optional[float] = None,
        human_time_cost: float = 0.0,
        incident_severity: str = "medium",
        resolution_contribution: float = 0.0,
    ) -> ActionCost:
        """Record the cost of an action."""
        # Use estimates if not provided
        tool_costs = self.tool_costs.get(tool, {})
        if compute_cost is None:
            compute_cost = tool_costs.get("compute", 0.01)
        if api_cost is None:
            api_cost = tool_costs.get("api", 0.0)
        
        cost = ActionCost(
            action_id=action_id,
            tool=tool,
            compute_cost=compute_cost,
            api_cost=api_cost,
            human_time_cost=human_time_cost,
            incident_severity=incident_severity,
            resolution_contribution=resolution_contribution,
        )
        
        self.action_costs.append(cost)
        
        # Update budget
        if tenant_id in self.budgets:
            budget = self.budgets[tenant_id]
            self._check_budget_reset(budget)
            budget.daily_used += cost.total_cost
            budget.monthly_used += cost.total_cost
        
        self._persist()
        
        logger.info(
            f"Recorded cost for {tool}: ${cost.total_cost:.4f}, ROI={cost.roi:.2f}"
        )
        
        return cost
    
    def _check_budget_reset(self, budget: CostBudget):
        """Check and reset budget if period has passed."""
        now = datetime.now()
        
        # Daily reset
        if now.date() > budget.last_reset.date():
            budget.daily_used = 0.0
            budget.last_reset = now
        
        # Monthly reset
        if now.month != budget.period_start.month or now.year != budget.period_start.year:
            budget.monthly_used = 0.0
            budget.period_start = now
    
    def get_cost_report(
        self,
        tenant_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get cost report."""
        cutoff = datetime.now() - timedelta(days=days)
        costs = [c for c in self.action_costs if c.timestamp > cutoff]
        
        by_tool: Dict[str, float] = {}
        for cost in costs:
            by_tool[cost.tool] = by_tool.get(cost.tool, 0) + cost.total_cost
        
        total_cost = sum(c.total_cost for c in costs)
        total_value = sum(
            c.resolution_contribution * {"critical": 10000, "high": 5000, "medium": 1000, "low": 100}.get(c.incident_severity, 1000)
            for c in costs
        )
        
        return {
            "period_days": days,
            "total_cost": total_cost,
            "total_value": total_value,
            "overall_roi": total_value / max(0.01, total_cost),
            "cost_by_tool": by_tool,
            "action_count": len(costs),
            "budget_status": {
                tid: {
                    "daily_used": b.daily_used,
                    "daily_limit": b.daily_limit,
                    "monthly_used": b.monthly_used,
                    "monthly_limit": b.monthly_limit,
                    "is_over_budget": b.is_over_budget,
                }
                for tid, b in self.budgets.items()
            },
        }
    
    def get_tool_roi_rankings(self) -> List[tuple]:
        """Get tools ranked by ROI."""
        tool_stats: Dict[str, Dict[str, float]] = {}
        
        for cost in self.action_costs:
            if cost.tool not in tool_stats:
                tool_stats[cost.tool] = {"total_cost": 0, "total_roi": 0, "count": 0}
            tool_stats[cost.tool]["total_cost"] += cost.total_cost
            tool_stats[cost.tool]["total_roi"] += cost.roi
            tool_stats[cost.tool]["count"] += 1
        
        rankings = []
        for tool, stats in tool_stats.items():
            avg_roi = stats["total_roi"] / max(1, stats["count"])
            rankings.append((tool, avg_roi, stats["count"]))
        
        return sorted(rankings, key=lambda x: x[1], reverse=True)
    
    def _persist(self):
        # Budgets
        filepath = self.storage_path / "budgets.json"
        with open(filepath, "w") as f:
            json.dump({
                tid: {
                    "budget_id": b.budget_id,
                    "tenant_id": b.tenant_id,
                    "daily_limit": b.daily_limit,
                    "monthly_limit": b.monthly_limit,
                    "daily_used": b.daily_used,
                    "monthly_used": b.monthly_used,
                    "period_start": b.period_start.isoformat(),
                    "last_reset": b.last_reset.isoformat(),
                }
                for tid, b in self.budgets.items()
            }, f, indent=2)
        
        # Keep only recent costs in memory (last 1000)
        self.action_costs = self.action_costs[-1000:]
    
    def _load(self):
        filepath = self.storage_path / "budgets.json"
        if not filepath.exists():
            return
        
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            for tid, bd in data.items():
                self.budgets[tid] = CostBudget(
                    budget_id=bd["budget_id"],
                    tenant_id=bd["tenant_id"],
                    daily_limit=bd["daily_limit"],
                    monthly_limit=bd["monthly_limit"],
                    daily_used=bd.get("daily_used", 0),
                    monthly_used=bd.get("monthly_used", 0),
                    period_start=datetime.fromisoformat(bd["period_start"]),
                    last_reset=datetime.fromisoformat(bd["last_reset"]),
                )
        except Exception as e:
            logger.warning(f"Failed to load economic memory: {e}")


__all__ = [
    "EconomicMemory",
    "ActionCost",
    "CostBudget",
]
