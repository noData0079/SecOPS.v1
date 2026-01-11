from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, Float, Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin


class ToolUsage(Base, TimestampMixin):
    """
    Dedicated table for tool usage.
    Tracks tool execution, risk, and economic metrics.
    """
    __tablename__ = "tool_usages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    episode_id: Mapped[str] = mapped_column(String, ForeignKey("episodes.episode_id"), nullable=False, index=True)

    tool_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, default=False)

    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cost_estimate: Mapped[float] = mapped_column(Float, default=0.0)

    confidence_at_time: Mapped[float] = mapped_column(Float, default=0.0)
    blacklisted_after: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ToolUsage(id={self.id}, tool={self.tool_name}, success={self.success})>"
