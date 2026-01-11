from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import String, Float, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from backend.src.db.base import Base, TimestampMixin


class SemanticFact(Base, TimestampMixin):
    """
    Semantic Memory - Abstracted facts.
    """
    __tablename__ = "semantic_facts"

    fact_id: Mapped[str] = mapped_column(String, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)

    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    evidence_count: Mapped[int] = mapped_column(Integer, default=1)

    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default={})

    def __repr__(self) -> str:
        return f"<SemanticFact(id={self.fact_id}, category={self.category})>"


class ToolPattern(Base, TimestampMixin):
    """
    Semantic Memory - Tool effectiveness patterns.
    """
    __tablename__ = "tool_patterns"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    tool: Mapped[str] = mapped_column(String, nullable=False, index=True)
    context: Mapped[str] = mapped_column(String, nullable=False)

    effectiveness: Mapped[float] = mapped_column(Float, default=0.5)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now)

    def __repr__(self) -> str:
        return f"<ToolPattern(tool={self.tool}, context={self.context}, effectiveness={self.effectiveness})>"
