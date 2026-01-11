from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy import String, Integer, Float, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.src.db.base import Base, TimestampMixin, TenantMixin


class Incident(Base, TimestampMixin, TenantMixin):
    """
    Complete memory of an incident.
    Corresponds to IncidentMemory in episodic_store.py.
    """
    __tablename__ = "incidents"

    incident_id: Mapped[str] = mapped_column(String, primary_key=True)

    # State
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    final_outcome: Mapped[str] = mapped_column(String, default="")  # resolved, escalated, failed

    # Summary Metrics (computed)
    resolution_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    actions_taken_count: Mapped[int] = mapped_column(Integer, default=0)
    successful_actions_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    episodes: Mapped[List["Episode"]] = relationship("Episode", back_populates="incident", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Incident(id={self.incident_id}, outcome={self.final_outcome})>"


class Episode(Base, TimestampMixin):
    """
    Complete snapshot of an incident episode.
    Corresponds to EpisodeSnapshot in episodic_store.py.
    """
    __tablename__ = "episodes"

    episode_id: Mapped[str] = mapped_column(String, primary_key=True)
    incident_id: Mapped[str] = mapped_column(String, ForeignKey("incidents.incident_id"), nullable=False, index=True)

    # State at this point
    observation: Mapped[str] = mapped_column(String, default="")
    system_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})

    # Decision made (summary - detailed decision in PolicyDecision)
    action_taken: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Outcome summary (detailed outcome in ActionOutcome)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # Metadata
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default={})

    # Relationships
    incident: Mapped["Incident"] = relationship("Incident", back_populates="episodes")

    # Other relationships (defined in their respective modules to avoid circular deps if possible,
    # but here we define string-based relationships or back-populates if those models import this)
    # outcomes = relationship("ActionOutcome", back_populates="episode")
    # tool_usages = relationship("ToolUsage", back_populates="episode")
    # policy_decisions = relationship("PolicyDecision", back_populates="episode")

    def __repr__(self) -> str:
        return f"<Episode(id={self.episode_id}, incident={self.incident_id})>"
