from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from sqlalchemy import DateTime, String, ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.sql import func

# Naming convention for constraints / indexes
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
    Base class for new memory schemas.
    """
    metadata = metadata_obj

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # CamelCase -> snake_case
        name = cls.__name__
        snake: list[str] = []
        for i, ch in enumerate(name):
            if ch.isupper() and i != 0:
                snake.append("_")
            snake.append(ch.lower())
        return "".join(snake)


class TimestampMixin:
    """Mixin to add created_at and updated_at columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    """
    Mixin to add tenant_id and user_id columns.
    Assumes Tenant and User tables exist elsewhere (string-based FKs).
    """

    @declared_attr
    def tenant_id(cls) -> Mapped[str]:
        # Using string-based ForeignKey to avoid circular imports or missing table definitions
        return mapped_column(String, ForeignKey("tenants.id"), nullable=False, index=True)

    @declared_attr
    def user_id(cls) -> Mapped[Optional[str]]:
        return mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)


__all__ = ["Base", "TimestampMixin", "TenantMixin"]
