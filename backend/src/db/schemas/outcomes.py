from __future__ import annotations

from typing import Optional
from datetime import datetime

from sqlalchemy import String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin


class ActionOutcome(Base, TimestampMixin):
    """
    Dedicated table for action outcomes.
    """
    __tablename__ = "action_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    episode_id: Mapped[str] = mapped_column(String, ForeignKey("episodes.episode_id"), nullable=False, index=True)

    action_type: Mapped[str] = mapped_column(String, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    failure_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    # episode = relationship("Episode") - implied by FK, can be explicit if needed

    def __repr__(self) -> str:
        return f"<ActionOutcome(id={self.id}, success={self.success}, score={self.score})>"
