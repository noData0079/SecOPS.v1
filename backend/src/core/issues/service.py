# backend/src/core/issues/service.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.issues import (
    IssueDetail,
    IssueResolutionState,
    IssueSeverity,
    IssueStatus,
)
from db.session import async_session_factory  # to be defined in db/session.py
from .models import Issue
from .repository import IssuesRepository


class IssuesService:
    """
    High-level business logic for issues.

    Responsibilities:
    - orchestrate DB operations via IssuesRepository
    - shape data into API-compatible dicts
    - compute simple health summaries
    """

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self._repo = IssuesRepository()
        self._session_factory = async_session_factory

    # ------------------------------------------------------------------
    # Internal helper: session context manager
    # ------------------------------------------------------------------

    async def _with_session(self) -> AsyncSession:
        """
        Helper to get a new AsyncSession.

        Note: The public methods open/commit/rollback sessions explicitly
        to keep control and avoid nested context managers everywhere.
        """
        return self._session_factory()

    # ------------------------------------------------------------------
    # Public API: list issues
    # ------------------------------------------------------------------

    async def list_issues(
        self,
        *,
        org_id: str,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        service: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List issues for an org with filters and pagination.

        Returns a dict compatible with `IssuesListResponse`:
        {
          "issues": List[IssueSummary],
          "total": int,
          "limit": int,
          "offset": int,
        }
        """
        async_session = await self._with_session()
        async with async_session as session:  # type: AsyncSession
            try:
                issues = await self._repo.list_issues(
                    session=session,
                    org_id=org_id,
                    status=status,
                    severity=severity,
                    service=service,
                    limit=limit,
                    offset=offset,
                )
                total = await self._repo.count_issues(
                    session=session,
                    org_id=org_id,
                    status=status,
                    severity=severity,
                    service=service,
                )

                issue_summaries = [issue.to_summary() for issue in issues]

                return {
                    "issues": issue_summaries,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            finally:
                # session context manager handles commit/rollback
                ...

    # ------------------------------------------------------------------
    # Public API: get single issue
    # ------------------------------------------------------------------

    async def get_issue(
        self,
        *,
        org_id: str,
        issue_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load a single issue by id, scoped to an org.

        Returns a dict compatible with `IssueDetailResponse`:
        {
          "issue": IssueDetail
        }

        or None if not found.
        """
        async_session = await self._with_session()
        async with async_session as session:
            issue = await self._repo.get_issue(
                session=session,
                org_id=org_id,
                issue_id=issue_id,
            )
            if issue is None:
                return None

            return {"issue": issue.to_detail()}

    # ------------------------------------------------------------------
    # Public API: resolve / suppress issue
    # ------------------------------------------------------------------

    async def resolve_issue(
        self,
        *,
        org_id: str,
        issue_id: str,
        resolution_state: IssueResolutionState,
        resolution_note: Optional[str],
        resolved_by: Optional[str],
    ) -> Dict[str, Any]:
        """
        Resolve or suppress an issue.

        Returns a dict compatible with `ResolveIssueResponse`:
        {
          "success": bool,
          "message": str,
          "issue": IssueDetail
        }
        """
        async_session = await self._with_session()
        async with async_session as session:
            try:
                updated_issue = await self._repo.update_issue_resolution(
                    session=session,
                    org_id=org_id,
                    issue_id=issue_id,
                    resolution_state=resolution_state,
                    resolution_note=resolution_note,
                    resolved_by=resolved_by,
                )
                if updated_issue is None:
                    return {
                        "success": False,
                        "message": "Issue not found.",
                        "issue": None,
                    }

                await session.commit()

                return {
                    "success": True,
                    "message": "Issue updated successfully.",
                    "issue": updated_issue.to_detail(),
                }
            except Exception:
                await session.rollback()
                raise

    # ------------------------------------------------------------------
    # Public API: health summary
    # ------------------------------------------------------------------

    async def get_health_summary(
        self,
        *,
        org_id: str,
    ) -> Dict[str, Any]:
        """
        Compute a simple health summary for the org.

        Returns a dict used by PlatformHealthResponse:

        {
          "overall_status": str,
          "open_issues_total": int,
          "open_issues_by_severity": {severity: count, ...},
        }
        """
        async_session = await self._with_session()
        async with async_session as session:
            # Count open issues grouped by severity
            stmt = (
                select(Issue.severity, func.count(Issue.id))
                .where(
                    Issue.org_id == org_id,
                    Issue.status == IssueStatus.open,
                )
                .group_by(Issue.severity)
            )
            result = await session.execute(stmt)
            rows = result.all()

            open_by_severity: Dict[str, int] = {}
            for severity, count in rows:
                open_by_severity[str(severity.value)] = int(count)

            open_total = sum(open_by_severity.values())

            overall_status = self._derive_overall_status(open_by_severity, open_total)

            return {
                "overall_status": overall_status,
                "open_issues_total": open_total,
                "open_issues_by_severity": open_by_severity,
            }

    def _derive_overall_status(
        self,
        open_by_severity: Dict[str, int],
        open_total: int,
    ) -> str:
        """
        Basic heuristic to convert open issues → high-level status.

        - 0 open → "healthy"
        - any critical → "critical"
        - any high → "degraded"
        - else if open > 0 → "warning"
        """
        if open_total == 0:
            return "healthy"

        if open_by_severity.get(IssueSeverity.critical.value, 0) > 0:
            return "critical"

        if open_by_severity.get(IssueSeverity.high.value, 0) > 0:
            return "degraded"

        return "warning"

    # ------------------------------------------------------------------
    # Public API: create / ingest (for checks / scanners)
    # ------------------------------------------------------------------

    async def create_issue_record(
        self,
        issue_data: Dict[str, Any],
    ) -> IssueDetail:
        """
        Create a single issue programmatically (e.g., from a check).

        Returns IssueDetail.
        """
        async_session = await self._with_session()
        async with async_session as session:
            try:
                issue = await self._repo.create_issue(session=session, issue_data=issue_data)
                await session.commit()
                return issue.to_detail()
            except Exception:
                await session.rollback()
                raise

    async def upsert_issues_from_check_run(
        self,
        *,
        issues_data: List[Dict[str, Any]],
    ) -> Tuple[int, int]:
        """
        Bulk upsert issues from a check run.

        Returns (created_count, updated_count).
        """
        if not issues_data:
            return 0, 0

        async_session = await self._with_session()
        async with async_session as session:
            try:
                created, updated = await self._repo.upsert_many(
                    session=session,
                    issues_data=issues_data,
                )
                await session.commit()
                return created, updated
            except Exception:
                await session.rollback()
                raise
