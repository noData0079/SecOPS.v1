# backend/src/api/routes/platform.py

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.schemas.platform import (
    PlatformHealthResponse,
    IssuesListResponse,
    IssueDetailResponse,
    ResolveIssueRequest,
    ResolveIssueResponse,
    ChecksListResponse,
    RunHealthCheckRequest,
    RunHealthCheckResponse,
)
from api.deps import (
    get_current_user,
    get_issues_service,
    get_scheduler_service,
)
from core.issues.service import IssuesService
from core.scheduler.scheduler import CheckScheduler

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/platform",
    tags=["Platform"],
)


# --- Helpers -----------------------------------------------------------------


def _resolve_org_id(
    current_user: dict[str, Any],
    explicit_org_id: Optional[str] = None,
) -> str:
    """
    Decide which org_id to use for platform operations.

    - If explicit_org_id is passed, prefer that (admin use-cases).
    - Otherwise, fall back to current_user["org_id"].

    Routers stay stable; if later you support multi-org admins, you only need
    to adjust `get_current_user` / auth, not these endpoints.
    """
    if explicit_org_id:
        return explicit_org_id

    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context is required.",
        )
    return str(org_id)


# --- Platform health ---------------------------------------------------------


@router.get(
    "/health/summary",
    response_model=PlatformHealthResponse,
    summary="Overall platform health for current org",
    response_description="Aggregated health status and issue counts.",
)
async def get_platform_health_summary(
    current_user: dict[str, Any] = Depends(get_current_user),
    issues_service: IssuesService = Depends(get_issues_service),
    scheduler: CheckScheduler = Depends(get_scheduler_service),
) -> PlatformHealthResponse:
    """
    Aggregated health info for the current organization.

    Combines:
    - issue stats (open by severity, trend)
    - last health check run status
    """
    org_id = _resolve_org_id(current_user)

    try:
        issues_summary = await issues_service.get_health_summary(org_id=org_id)
        last_run = await scheduler.get_last_run_status(org_id=org_id)
    except Exception:
        logger.exception("Failed to compute platform health summary")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute platform health summary.",
        )

    return PlatformHealthResponse(
        org_id=org_id,
        overall_status=issues_summary.get("overall_status", "unknown"),
        open_issues_total=issues_summary.get("open_issues_total", 0),
        open_issues_by_severity=issues_summary.get("open_issues_by_severity", {}),
        last_check_at=last_run.get("last_run_at"),
        last_check_status=last_run.get("status"),
        metadata={
            "checks_run": last_run.get("checks_run", []),
            "failed_checks": last_run.get("failed_checks", []),
        },
    )


# --- Issues listing & detail -------------------------------------------------


@router.get(
    "/issues",
    response_model=IssuesListResponse,
    summary="List issues for current org",
    response_description="Issues with filters for severity, status, and service.",
)
async def list_issues(
    current_user: dict[str, Any] = Depends(get_current_user),
    issues_service: IssuesService = Depends(get_issues_service),
    status_filter: Optional[str] = Query(
        None,
        alias="status",
        description="Filter by status: open, resolved, suppressed, etc.",
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity: critical, high, medium, low.",
    ),
    service: Optional[str] = Query(
        None,
        description="Filter by service/component name.",
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Max number of issues to return.",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Pagination offset.",
    ),
) -> IssuesListResponse:
    """
    Return issues for the current org, with optional filters.

    The IssuesService is responsible for:
    - DB querying,
    - applying filters,
    - sorting by severity / recency.
    """
    org_id = _resolve_org_id(current_user)

    try:
        data = await issues_service.list_issues(
            org_id=org_id,
            status=status_filter,
            severity=severity,
            service=service,
            limit=limit,
            offset=offset,
        )
        # `data` is expected to be a dict that matches IssuesListResponse
        return IssuesListResponse(**data)
    except Exception:
        logger.exception("Failed to list issues")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list issues.",
        )


@router.get(
    "/issues/{issue_id}",
    response_model=IssueDetailResponse,
    summary="Get a single issue by id",
    response_description="Full issue details, including root cause & proposed fix.",
)
async def get_issue_detail(
    issue_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    issues_service: IssuesService = Depends(get_issues_service),
) -> IssueDetailResponse:
    """
    Load a single issue by id.

    The IssuesService enforces org scoping so users cannot access issues
    belonging to other organizations.
    """
    org_id = _resolve_org_id(current_user)

    try:
        data = await issues_service.get_issue(org_id=org_id, issue_id=issue_id)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found.",
            )
        return IssueDetailResponse(**data)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to load issue detail")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load issue.",
        )


@router.post(
    "/issues/{issue_id}/resolve",
    response_model=ResolveIssueResponse,
    summary="Mark an issue as resolved",
)
async def resolve_issue(
    issue_id: str,
    payload: ResolveIssueRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    issues_service: IssuesService = Depends(get_issues_service),
) -> ResolveIssueResponse:
    """
    Mark issue as resolved or suppressed.

    Actual logic (in IssuesService):
    - mark status
    - optionally store resolution note and who resolved it
    - record timestamps / audit trail
    """
    org_id = _resolve_org_id(current_user)

    try:
        result = await issues_service.resolve_issue(
            org_id=org_id,
            issue_id=issue_id,
            resolution_state=payload.resolution_state,
            resolution_note=payload.resolution_note,
            resolved_by=current_user.get("id"),
        )
        return ResolveIssueResponse(**result)
    except ValueError as exc:
        logger.info("Issue resolve failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception:
        logger.exception("Failed to resolve issue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve issue.",
        )


# --- Checks & health runs ----------------------------------------------------


@router.get(
    "/checks",
    response_model=ChecksListResponse,
    summary="List available checks and their status",
    response_description="Configuration and last-run info for each check.",
)
async def list_checks(
    current_user: dict[str, Any] = Depends(get_current_user),
    scheduler: CheckScheduler = Depends(get_scheduler_service),
) -> ChecksListResponse:
    """
    List all checks that can run for this org (and their last run status).

    `CheckScheduler.list_checks_for_org` returns a dict ready to be wrapped
    into `ChecksListResponse`.
    """
    org_id = _resolve_org_id(current_user)

    try:
        data = await scheduler.list_checks_for_org(org_id=org_id)
        return ChecksListResponse(**data)
    except Exception:
        logger.exception("Failed to list checks")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list checks.",
        )


@router.post(
    "/run-health-check",
    response_model=RunHealthCheckResponse,
    summary="Trigger a health check run for current org",
)
async def run_health_check(
    payload: RunHealthCheckRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    scheduler: CheckScheduler = Depends(get_scheduler_service),
) -> RunHealthCheckResponse:
    """
    Trigger a health check run for the current org.

    This is normally asynchronous: we enqueue a job and return immediately.
    The scheduler decides whether to:
    - run all checks,
    - run a subset (by ids),
    - or run a scoped subset (e.g. only security checks).
    """
    org_id = _resolve_org_id(current_user, explicit_org_id=payload.org_id)

    try:
        job_info = await scheduler.enqueue_run(
            org_id=org_id,
            checks=payload.checks,
            scope=payload.scope,
            triggered_by=current_user.get("id"),
        )
        return RunHealthCheckResponse(
            org_id=org_id,
            job_id=job_info.get("job_id"),
            status="scheduled",
            message="Health check run scheduled.",
        )
    except Exception:
        logger.exception("Failed to schedule health check run")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule health check run.",
        )
