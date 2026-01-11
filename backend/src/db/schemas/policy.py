from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import String, Float, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin


class PolicyDecision(Base, TimestampMixin):
    """
    Dedicated table for policy decisions.
    Records why a decision was made for audit and analysis.
    """
    __tablename__ = "policy_decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    episode_id: Mapped[str] = mapped_column(String, ForeignKey("episodes.episode_id"), nullable=False, index=True)

    # Policy ID is a string reference (e.g., "policy_risk_gate_001")
    policy_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Decision: ALLOW | BLOCK | ESCALATE | WAIT_APPROVAL
    decision: Mapped[str] = mapped_column(String, nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    reason: Mapped[str] = mapped_column(String, default="")

    def __repr__(self) -> str:
        return f"<PolicyDecision(id={self.id}, policy={self.policy_id}, decision={self.decision})>"


class PolicyRecord(Base, TimestampMixin):
    """
    Persistence for PolicyMemory.
    Tracks long-term performance and stats of a policy.
    """
    __tablename__ = "policy_records"

    policy_id: Mapped[str] = mapped_column(String, primary_key=True)
    rule_type: Mapped[str] = mapped_column(String, default="unknown")  # risk_gate, action_limit, etc.
    description: Mapped[str] = mapped_column(String, default="")

    # Effectiveness Stats
    times_applied: Mapped[int] = mapped_column(Integer, default=0)
    times_effective: Mapped[int] = mapped_column(Integer, default=0)
    times_bypassed: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)

    current_confidence: Mapped[float] = mapped_column(Float, default=0.5)

    last_applied: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default={})

    def __repr__(self) -> str:
        return f"<PolicyRecord(id={self.policy_id}, confidence={self.current_confidence})>"
