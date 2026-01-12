from __future__ import annotations

from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, TenantMixin


class BillingRecord(Base, TimestampMixin, TenantMixin):
    """
    Tracks billable events and costs.
    """
    __tablename__ = "billing_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    item_type: Mapped[str] = mapped_column(String, nullable=False) # e.g., "token_usage", "agent_run"
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)

    currency: Mapped[str] = mapped_column(String, default="USD")

    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default={})

    def __repr__(self) -> str:
        return f"<BillingRecord(tenant={self.tenant_id}, cost={self.total_cost})>"


class UsageMetric(Base, TimestampMixin, TenantMixin):
    """
    Granular usage metrics for metering and limits.
    """
    __tablename__ = "usage_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    metric_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, default=0.0)
    window_start: Mapped[Optional[str]] = mapped_column(String, nullable=True) # ISO8601 string or timestamp

    tags: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})

    def __repr__(self) -> str:
        return f"<UsageMetric(metric={self.metric_name}, value={self.metric_value})>"
