# backend/src/db/models.py
"""
Central SQLAlchemy ORM base and model registration.

This module defines the global Declarative Base class that all ORM models
inherit from, and serves as the single place where Alembic and the rest of
the application discover metadata for migrations.

Usage:
    from db.models import Base
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import MetaData, String, Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime

# ---------------------------------------------------------------------------
# Naming convention for constraints / indexes
# ---------------------------------------------------------------------------

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix__%(table_name)s__%(column_0_N_name)s",
    "uq": "uq__%(table_name)s__%(column_0_N_name)s",
    "ck": "ck__%(table_name)s__%(constraint_name)s",
    "fk": "fk__%(table_name)s__%(column_0_N_name)s__%(referred_table_name)s",
    "pk": "pk__%(table_name)s",
}

metadata_obj = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    """
    Global SQLAlchemy Declarative Base for all ORM models.
    """

    metadata = metadata_obj

    @declared_attr.directive
    def __tablename__(cls) -> str:  # type: ignore[override]
        # CamelCase → snake_case by default if not explicitly set.
        name = cls.__name__
        snake: list[str] = []
        for i, ch in enumerate(name):
            if ch.isupper() and i != 0:
                snake.append("_")
            snake.append(ch.lower())
        return "".join(snake)


# ---------------------------------------------------------------------------
# Core Models (Stubbed for Expansion)
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, index=True)

class ApiToken(Base):
    __tablename__ = "api_tokens"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    token: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# ---------------------------------------------------------------------------
# Model registration
# ---------------------------------------------------------------------------

try:
    from src.core.issues.models import Issue  # noqa: F401
    from src.core.audit.models import AuditLog  # noqa: F401
except Exception:
    pass

__all__ = ["Base", "metadata_obj", "User", "Organization", "ApiToken"]
