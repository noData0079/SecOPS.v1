# backend/src/core/issues/repository.py

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.schemas.issues import IssueResolutionState
from .models import Issue


class IssuesRepository:
    """
    Thin data-access layer for Issue entities.

    It does not contain business logic (no health summaries, no AI). It only:
    - builds queries
    - executes them against the database
    - returns ORM entities

    Higher-level logic is implemented in `IssuesService`.
    """

    # ------------------------------------------------------------------
    # Listing / counting
    # ------------------------------------------------------------------

    async def list_issues(
        self,
        session: AsyncSession,
        *,
        org_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Issue]:
        """
        Return a page of issues for the given org, with optional filters.

        Sorting strategy:
        - primary: severity (critical → low)
        - secondary: last_seen_at desc
        """
        stmt: Select = select(Issue).where(Issue.org_id == org_id)

        if status:
            stmt = stmt.where(Issue.status == status)
        if severity:
            stmt = stmt.where(Issue.severity == severity)
        if service:
            stmt = stmt.where(Issue.service == service)

        # Severity ordering: critical > high > medium > low > info
        severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }

        # We can't easily use a Python dict in SQL; ordering by severity name
        # is good enough for now, and the service layer can re-sort if needed.
        stmt = (
            stmt.order_by(
                Issue.severity.asc(),  # alphabetical, but stable
                Issue.last_seen_at.desc().nullslast(),
                Issue.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_issues(
        self,
        session: AsyncSession,
        *,
        org_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service: Optional[str] = None,
    ) -> int:
        """
        Return total count of issues matching the filters.
        """
        stmt = select(func.count(Issue.id)).where(Issue.org_id == org_id)

        if status:
            stmt = stmt.where(Issue.status == status)
        if severity:
            stmt = stmt.where(Issue.severity == severity)
        if service:
            stmt = stmt.where(Issue.service == service)

        result = await session.execute(stmt)
        return int(result.scalar() or 0)

    # ------------------------------------------------------------------
    # Single issue
    # ------------------------------------------------------------------

    async def get_issue(
        self,
        session: AsyncSession,
        *,
        org_id: str,
        issue_id: str,
    ) -> Optional[Issue]:
        """
        Load a single issue by id, scoped to the given org.
        """
        stmt = (
            select(Issue)
            .where(Issue.org_id == org_id, Issue.id == issue_id)
            .options(selectinload("*"))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    # ------------------------------------------------------------------
    # Create / update
    # ------------------------------------------------------------------

    async def create_issue(
        self,
        session: AsyncSession,
        issue_data: dict[str, Any],
    ) -> Issue:
        """
        Create a new issue from a dict of fields.

        The caller is responsible for:
        - generating `id`
        - setting `org_id`
        - setting `severity`, `status`, etc.
        """
        issue = Issue(**issue_data)
        session.add(issue)
        await session.flush()
        return issue

    async def update_issue(
        self,
        session: AsyncSession,
        issue: Issue,
        updates: dict[str, Any],
    ) -> Issue:
        """
        Apply updates to an existing issue ORM instance.

        The caller is responsible for committing the transaction.
        """
        for key, value in updates.items():
            if hasattr(issue, key):
                setattr(issue, key, value)
        issue.updated_at = datetime.utcnow()
        await session.flush()
        return issue

    async def update_issue_resolution(
        self,
        session: AsyncSession,
        *,
        org_id: str,
        issue_id: str,
        resolution_state: IssueResolutionState,
        resolution_note: Optional[str],
        resolved_by: Optional[str],
    ) -> Optional[Issue]:
        """
        Update resolution-related fields for an issue.

        Returns the updated Issue or None if not found.
        """
        issue = await self.get_issue(
            session=session,
            org_id=org_id,
            issue_id=issue_id,
        )
        if issue is None:
            return None

        now = datetime.utcnow()

        issue.status = (
            "resolved" if resolution_state == IssueResolutionState.resolved else "suppressed"
        )
        issue.resolution_state = resolution_state
        issue.resolution_note = resolution_note
        issue.resolved_by = resolved_by
        issue.resolved_at = now
        issue.updated_at = now

        await session.flush()
        return issue

    # ------------------------------------------------------------------
    # Bulk upsert (for check runs)
    # ------------------------------------------------------------------

    async def upsert_many(
        self,
        session: AsyncSession,
        issues_data: List[dict[str, Any]],
    ) -> Tuple[int, int]:
        """
        Bulk upsert issues based on their primary key (id).

        For each issue dict:
        - if id exists for the same org_id → update selected fields
        - otherwise → create new issue

        Returns (created_count, updated_count).
        """
        created = 0
        updated = 0
        now = datetime.utcnow()

        # In a real high-volume system, you'd want a more efficient bulk
        # strategy (e.g. database-specific upsert). For now, this is simple
        # and explicit.
        for data in issues_data:
            issue_id = data.get("id")
            org_id = data.get("org_id")
            if not issue_id or not org_id:
                # Skip invalid records silently; caller can log if needed
                continue

            existing = await self.get_issue(
                session=session,
                org_id=org_id,
                issue_id=issue_id,
            )

            if existing is None:
                data.setdefault("created_at", now)
                issue = Issue(**data)
                session.add(issue)
                created += 1
            else:
                # Update a subset of fields while preserving identifiers
                mutable_fields = [
                    "title",
                    "severity",
                    "status",
                    "service",
                    "category",
                    "tags",
                    "location",
                    "source",
                    "short_description",
                    "description",
                    "root_cause",
                    "impact",
                    "proposed_fix",
                    "precautions",
                    "references",
                    "extra",
                    "first_seen_at",
                    "last_seen_at",
                ]
                for field in mutable_fields:
                    if field in data:
                        setattr(existing, field, data[field])

                existing.updated_at = now
                updated += 1

        await session.flush()
        return created, updated
