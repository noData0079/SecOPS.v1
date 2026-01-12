from __future__ import annotations

from typing import Optional, Dict, Any

from sqlalchemy import String, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base, TimestampMixin, TenantMixin


class UserRole(Base, TimestampMixin, TenantMixin):
    """
    Extends standard auth roles with granular platform permissions.
    """
    __tablename__ = "user_roles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # user_id and tenant_id are provided by TenantMixin

    role_name: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "auditor", "incident_commander"
    permissions: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})

    def __repr__(self) -> str:
        return f"<UserRole(user={self.user_id}, role={self.role_name})>"


class AuditEvent(Base, TimestampMixin, TenantMixin):
    """
    Immutable audit ledger for compliance and forensics.
    """
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    event_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    actor_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    action: Mapped[str] = mapped_column(String, nullable=False)
    outcome: Mapped[str] = mapped_column(String, nullable=False)  # SUCCESS, FAILURE, BLOCKED

    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default={})

    # Hash for integrity verification (optional, but good for "Trust Ledger")
    integrity_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditEvent(event={self.event_type}, actor={self.actor_id})>"
