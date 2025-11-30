# backend/src/api/schemas/issues.py

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class IssueSeverity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class IssueStatus(str, Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"
    suppressed = "suppressed"
    ignored = "ignored"


class IssueResolutionState(str, Enum):
    """
    Resolution action a user can take on an issue.

    - resolved: fixed / remediated
    - suppressed: intentionally ignored (e.g. false positive, accepted risk)
    """

    resolved = "resolved"
    suppressed = "suppressed"


# ---------------------------------------------------------------------------
# Core issue models
# ---------------------------------------------------------------------------


class IssueLocation(BaseModel):
    """
    Describes WHERE an issue lives in the user's stack.

    Flexible structure that works for:
    - code (repo, file, line)
    - CI (workflow, job, step)
    - k8s (cluster, namespace, resource)
    - cloud resources, etc.
    """

    kind: Optional[str] = Field(
        default=None,
        description="Location kind: code, k8s, ci, cloud, db, etc.",
    )
    repo: Optional[str] = Field(
        default=None,
        description="Repository name or slug, if applicable.",
    )
    file_path: Optional[str] = Field(
        default=None,
        description="File path for code/config issues.",
    )
    line: Optional[int] = Field(
        default=None,
        ge=1,
        description="Line number in file, if applicable.",
    )
    cluster: Optional[str] = Field(
        default=None,
        description="Kubernetes cluster identifier.",
    )
    namespace: Optional[str] = Field(
        default=None,
        description="Kubernetes namespace.",
    )
    resource_kind: Optional[str] = Field(
        default=None,
        description="Kubernetes resource kind: Deployment, Ingress, etc.",
    )
    resource_name: Optional[str] = Field(
        default=None,
        description="Name of the resource in the target system.",
    )
    environment: Optional[str] = Field(
        default=None,
        description="Environment: prod, staging, dev, etc.",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional provider-specific location details.",
    )

    class Config:
        extra = "ignore"


class IssueBase(BaseModel):
    """
    Base fields for an issue.

    This is intentionally generic so it can be used across DB, API, and
    internal services without reshaping.
    """

    id: str = Field(..., description="Issue identifier.")
    org_id: str = Field(..., description="Organization identifier.")
    check_name: str = Field(
        ...,
        description="Name of the check that produced this issue.",
    )
    title: str = Field(..., description="Short issue title / summary.")
    severity: IssueSeverity = Field(
        ...,
        description="Severity of the issue.",
    )
    status: IssueStatus = Field(
        IssueStatus.open,
        description="Lifecycle status of the issue.",
    )
    service: Optional[str] = Field(
        default=None,
        description="Logical service / component this issue belongs to.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Category: security, reliability, perf, ops, hygiene, etc.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Free-form tags for filtering and grouping.",
    )
    location: Optional[IssueLocation] = Field(
        default=None,
        description="Where this issue is located in the system.",
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the issue: github, k8s, ci, scanner, etc.",
    )
    first_seen_at: Optional[datetime] = Field(
        default=None,
        description="First time this issue was observed.",
    )
    last_seen_at: Optional[datetime] = Field(
        default=None,
        description="Most recent time this issue was observed.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this issue record was created.",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="When this issue record was last updated.",
    )

    class Config:
        extra = "ignore"


class IssueSummary(IssueBase):
    """
    Issue representation suitable for listings.

    Extends IssueBase with a short_description.
    """

    short_description: Optional[str] = Field(
        default=None,
        description="Short description suitable for list views.",
    )

    class Config:
        extra = "ignore"


class IssueDetail(IssueBase):
    """
    Full issue detail, including root cause and recommended fix.

    This is what the issue detail page and SecOps console will use.
    """

    description: Optional[str] = Field(
        default=None,
        description="Detailed human-readable description of the issue.",
    )
    root_cause: Optional[str] = Field(
        default=None,
        description="Explanation of why this issue occurs.",
    )
    impact: Optional[str] = Field(
        default=None,
        description="Potential or observed impact of this issue.",
    )
    proposed_fix: Optional[str] = Field(
        default=None,
        description="AI-generated or rule-based fix recommendation.",
    )
    precautions: Optional[str] = Field(
        default=None,
        description="Precautions to avoid regressions when fixing this issue.",
    )
    references: List[str] = Field(
        default_factory=list,
        description="Links to external docs, CVEs, best practices, etc.",
    )
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary structured data (e.g., raw scanner output).",
    )

    resolved_by: Optional[str] = Field(
        default=None,
        description="User id who resolved/suppressed the issue, if any.",
    )
    resolved_at: Optional[datetime] = Field(
        default=None,
        description="When the issue was resolved/suppressed, if applicable.",
    )
    resolution_state: Optional[IssueResolutionState] = Field(
        default=None,
        description="How the issue was resolved: resolved or suppressed.",
    )
    resolution_note: Optional[str] = Field(
        default=None,
        description="Optional note describing the resolution decision.",
    )

    class Config:
        extra = "ignore"
