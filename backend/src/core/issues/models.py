# backend/src/core/issues/models.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Column,
    String,
    Enum as SAEnum,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.models import Base  # Global SQLAlchemy Base (to be defined in db/models.py)

from api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueResolutionState,
    IssueLocation,
    IssueSummary,
    IssueDetail,
)


class Issue(Base):
    """
    Persistent representation of an issue in the database.

    This model is intentionally generic enough to cover:
    - security findings
    - reliability / performance issues
    - configuration / hygiene problems

    It maps directly to the Pydantic models in api.schemas.issues via
    the helper methods `to_summary()` and `to_detail()`.
    """

    __tablename__ = "issues"

    # Core identifiers
    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
        doc="Issue identifier.",
    )
    org_id: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False,
        doc="Organization identifier.",
    )

    check_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Name of the check that produced this issue.",
    )

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
        doc="Short issue title / summary.",
    )

    severity: Mapped[IssueSeverity] = mapped_column(
        SAEnum(IssueSeverity),
        nullable=False,
        doc="Severity of the issue.",
    )

    status: Mapped[IssueStatus] = mapped_column(
        SAEnum(IssueStatus),
        nullable=False,
        default=IssueStatus.open,
        doc="Lifecycle status of the issue.",
    )

    service: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Logical service / component this issue belongs to.",
    )

    category: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Category: security, reliability, perf, ops, hygiene, etc.",
    )

    # Tags as JSON list of strings
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        doc="Free-form tags for filtering and grouping.",
    )

    # Location stored as JSON, mapped to IssueLocation in schemas
    location: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Serialized IssueLocation object.",
    )

    source: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="Source of the issue: github, k8s, ci, scanner, etc.",
    )

    # Timestamps
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="First time this issue was observed.",
    )
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Most recent time this issue was observed.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        doc="When this issue record was created.",
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When this issue record was last updated.",
    )

    # Summary / detail fields
    short_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Short description suitable for list views.",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed human-readable description of the issue.",
    )
    root_cause: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Explanation of why this issue occurs.",
    )
    impact: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Potential or observed impact of this issue.",
    )
    proposed_fix: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="AI-generated or rule-based fix recommendation.",
    )
    precautions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Precautions to avoid regressions when fixing this issue.",
    )

    references: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
        doc="Links to external docs, CVEs, best practices, etc.",
    )

    extra: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
        doc="Arbitrary structured data (e.g., raw scanner output).",
    )

    # Resolution info
    resolved_by: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        doc="User id who resolved/suppressed the issue, if any.",
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the issue was resolved/suppressed, if applicable.",
    )
    resolution_state: Mapped[Optional[IssueResolutionState]] = mapped_column(
        SAEnum(IssueResolutionState),
        nullable=True,
        doc="How the issue was resolved: resolved or suppressed.",
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional note describing the resolution decision.",
    )

    # ------------------------------------------------------------------
    # Conversion helpers: ORM → Pydantic
    # ------------------------------------------------------------------

    def _location_to_pydantic(self) -> Optional[IssueLocation]:
        if not self.location:
            return None
        try:
            return IssueLocation(**self.location)
        except Exception:
            # If the stored JSON doesn't perfectly match, we fall back
            # to None instead of breaking the API.
            return None

    def to_summary(self) -> IssueSummary:
        """
        Convert this ORM object into an IssueSummary Pydantic model.
        """
        return IssueSummary(
            id=self.id,
            org_id=self.org_id,
            check_name=self.check_name,
            title=self.title,
            severity=self.severity,
            status=self.status,
            service=self.service,
            category=self.category,
            tags=self.tags or [],
            location=self._location_to_pydantic(),
            source=self.source,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            short_description=self.short_description,
        )

    def to_detail(self) -> IssueDetail:
        """
        Convert this ORM object into an IssueDetail Pydantic model.
        """
        return IssueDetail(
            id=self.id,
            org_id=self.org_id,
            check_name=self.check_name,
            title=self.title,
            severity=self.severity,
            status=self.status,
            service=self.service,
            category=self.category,
            tags=self.tags or [],
            location=self._location_to_pydantic(),
            source=self.source,
            first_seen_at=self.first_seen_at,
            last_seen_at=self.last_seen_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            short_description=self.short_description,
            description=self.description,
            root_cause=self.root_cause,
            impact=self.impact,
            proposed_fix=self.proposed_fix,
            precautions=self.precautions,
            references=self.references or [],
            extra=self.extra or {},
            resolved_by=self.resolved_by,
            resolved_at=self.resolved_at,
            resolution_state=self.resolution_state,
            resolution_note=self.resolution_note,
        )
