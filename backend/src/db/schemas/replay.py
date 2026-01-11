from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin


class ReplayEvent(Base, TimestampMixin):
    """
    Events produced during offline replay.
    These never affect live state but update memory/confidence stores.
    """
    __tablename__ = "replay_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    episode_id: Mapped[str] = mapped_column(String, ForeignKey("episodes.episode_id"), nullable=False, index=True)

    # UUID for the replay run session
    replay_run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Event Type: OUTCOME_REEVALUATION | POLICY_DECAY | TOOL_CONFIDENCE_UPDATE
    event_type: Mapped[str] = mapped_column(String, nullable=False)

    before_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})
    after_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})

    delta_summary: Mapped[str] = mapped_column(String, default="")

    def __repr__(self) -> str:
        return f"<ReplayEvent(id={self.id}, type={self.event_type})>"
