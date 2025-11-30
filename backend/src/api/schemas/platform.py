# backend/src/api/schemas/platform.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from api.schemas.issues import (
    IssueSummary,
    IssueDetail,
    IssueResolutionState,
)


# ---------------------------------------------------------------------------
# Platform health
# ---------------------------------------------------------------------------


class PlatformHealthResponse(BaseModel):
    """
    Aggregated platform health for a given organization.

    Used by the SecOps console overview page.
    """

    org_id: str = Field(..., description="Organization identifier.")
    overall_status: str = Field(
        ...,
        description="High-level status: healthy, degraded, critical, unknown.",
    )
    open_issues_total: int = Field(
        0,
        ge=0,
        description="Total number of open issues for the org.",
    )
    open_issues_by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of severity → count of open issues.",
    )
    last_check_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last health check run, if any.",
    )
    last_check_status: Optional[str] = Field(
        default=None,
        description="Status of last health check: success, failed, partial, etc.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details (e.g. checks_run, failed_checks).",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# Issues listing & detail
# ---------------------------------------------------------------------------


class IssuesListResponse(BaseModel):
    """
    Response for listing issues with filters and pagination.

    `IssuesService.list_issues` should return a dict compatible with this shape.
    """

    issues: List[IssueSummary] = Field(
        default_factory=list,
        description="List of issues matching the filters.",
    )
    total: int = Field(
        0,
        ge=0,
        description="Total number of issues matching the filters (unpaginated).",
    )
    limit: int = Field(
        20,
        ge=1,
        description="Max number of issues returned in this page.",
    )
    offset: int = Field(
        0,
        ge=0,
        description="Pagination offset.",
    )

    class Config:
        extra = "ignore"


class IssueDetailResponse(BaseModel):
    """
    Response for a single issue detail.

    `IssuesService.get_issue` should return a dict compatible with this shape.
    """

    issue: IssueDetail = Field(
        ...,
        description="Full issue detail, including root cause and fix.",
    )

    class Config:
        extra = "ignore"


class ResolveIssueRequest(BaseModel):
    """
    Payload for resolving or suppressing an issue.
    """

    resolution_state: IssueResolutionState = Field(
        ...,
        description="How the issue is being resolved: resolved or suppressed.",
    )
    resolution_note: Optional[str] = Field(
        default=None,
        description="Optional human note explaining the resolution decision.",
    )

    class Config:
        extra = "ignore"


class ResolveIssueResponse(BaseModel):
    """
    Response after resolving/suppressing an issue.

    `IssuesService.resolve_issue` should return a dict compatible with this shape.
    """

    success: bool = Field(
        ...,
        description="Whether the resolution operation succeeded.",
    )
    message: str = Field(
        ...,
        description="Human-readable status message.",
    )
    issue: IssueDetail = Field(
        ...,
        description="Updated issue after resolution.",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# Checks & scheduler
# ---------------------------------------------------------------------------


class CheckInfo(BaseModel):
    """
    Metadata and last-run status for a single check.

    Represents an 'AI check' like github_deps, k8s_misconfig, ci_hardening, etc.
    """

    id: str = Field(..., description="Unique identifier for the check.")
    name: str = Field(..., description="Human-readable name for the check.")
    description: Optional[str] = Field(
        default=None,
        description="Short description of what this check validates.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Category: security, reliability, perf, ops, hygiene, etc.",
    )
    enabled: bool = Field(
        True,
        description="Whether this check is currently enabled for the org.",
    )

    # Last run info (if any)
    last_run_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last run for this check.",
    )
    last_run_status: Optional[str] = Field(
        default=None,
        description="Result of last run: success, failed, partial, etc.",
    )
    last_run_issues: Optional[int] = Field(
        default=None,
        ge=0,
        description="How many issues this check produced in its last run.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider- or engine-specific data.",
    )

    class Config:
        extra = "ignore"


class ChecksListResponse(BaseModel):
    """
    List of checks available for an org, plus their last run status.

    `CheckScheduler.list_checks_for_org` should return a dict compatible with this.
    """

    org_id: str = Field(..., description="Organization identifier.")
    checks: List[CheckInfo] = Field(
        default_factory=list,
        description="List of known checks and their status.",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# Run health check
# ---------------------------------------------------------------------------


class RunHealthCheckRequest(BaseModel):
    """
    Payload to trigger a health check run.

    - org_id: optional override; when not provided, we use the current user's org.
    - checks: optional subset of checks to run (by id).
    - scope: optional logical scope (e.g. 'security', 'perf', 'all').
    """

    org_id: Optional[str] = Field(
        default=None,
        description="Organization identifier; defaults to current user's org.",
    )
    checks: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific check ids to run.",
    )
    scope: Optional[str] = Field(
        default=None,
        description="Optional logical scope: security, reliability, all, etc.",
    )

    class Config:
        extra = "ignore"


class RunHealthCheckResponse(BaseModel):
    """
    Response after scheduling a health check run.

    The actual execution may be asynchronous; `job_id` can be used to track
    progress via a future jobs API if you add one.
    """

    org_id: str = Field(..., description="Organization identifier.")
    job_id: Optional[str] = Field(
        default=None,
        description="Identifier of the scheduled job, if available.",
    )
    status: str = Field(
        ...,
        description="Scheduling status: scheduled, failed, etc.",
    )
    message: str = Field(
        ...,
        description="Human-readable status message.",
    )

    class Config:
        extra = "ignore"
