from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin, TenantMixin


class CostBudget(Base, TimestampMixin, TenantMixin):
    """
    Cost budget for a tenant.
    """
    __tablename__ = "cost_budgets"

    budget_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Limits
    daily_limit: Mapped[float] = mapped_column(Float, default=100.0)
    monthly_limit: Mapped[float] = mapped_column(Float, default=2000.0)

    # Current Usage
    daily_used: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_used: Mapped[float] = mapped_column(Float, default=0.0)

    # Reset tracking
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)
    last_reset: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    def __repr__(self) -> str:
        return f"<CostBudget(tenant={self.tenant_id}, daily_left={self.daily_limit - self.daily_used})>"


class ActionCost(Base, TimestampMixin, TenantMixin):
    """
    Detailed cost breakdown for an action.
    """
    __tablename__ = "action_costs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Link to action (could be episode + tool or explicit action_id if available)
    # Using generic action_id string to be flexible
    action_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    tool: Mapped[str] = mapped_column(String, nullable=False)

    # Cost Components
    compute_cost: Mapped[float] = mapped_column(Float, default=0.0)
    api_cost: Mapped[float] = mapped_column(Float, default=0.0)
    human_time_cost: Mapped[float] = mapped_column(Float, default=0.0)

    @property
    def total_cost(self) -> float:
        return self.compute_cost + self.api_cost + self.human_time_cost

    def __repr__(self) -> str:
        return f"<ActionCost(action={self.action_id}, total={self.total_cost})>"
