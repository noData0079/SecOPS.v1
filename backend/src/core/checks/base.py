# backend/src/core/checks/base.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from abc import ABC, abstractmethod

from api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueLocation,
)


# ---------------------------------------------------------------------------
# Context passed into each check
# ---------------------------------------------------------------------------


@dataclass
class CheckContext:
    """
    Execution context for a single check run.

    - org_id: which organization we are checking
    - settings: global config object (utils.config.settings)
    - extras: optional extra data (cached integrations, pre-fetched metadata, etc.)

    The scheduler is free to extend `extras` with any useful precomputed data
    (e.g. list of repos, cluster info) to avoid repeated API calls across checks.
    """

    org_id: str
    settings: Any
    extras: Dict[str, Any] | None = None

    def get_extra(self, key: str, default: Any = None) -> Any:
        if not self.extras:
            return default
        return self.extras.get(key, default)


# ---------------------------------------------------------------------------
# Normalized issue payload for check outputs
# ---------------------------------------------------------------------------


@dataclass
class CheckIssuePayload:
    """
    Normalized issue structure produced by checks.

    This is intentionally close to `core.issues.models.Issue` but kept as a
    dataclass. It is used by checks to build issues and then converted to
    plain dicts for `IssuesService.upsert_issues_from_check_run`.
    """

    id: str
    org_id: str
    check_name: str
    title: str
    severity: IssueSeverity
    status: IssueStatus = IssueStatus.open

    service: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = None  # will be normalized to []

    location: Optional[IssueLocation] = None
    source: Optional[str] = None

    short_description: Optional[str] = None
    description: Optional[str] = None
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    proposed_fix: Optional[str] = None
    precautions: Optional[str] = None
    references: List[str] = None  # will be normalized to []
    extra: Dict[str, Any] = None  # will be normalized to {}

    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_issue_dict(self) -> Dict[str, Any]:
        """
        Convert to a dict compatible with Issue ORM constructor
        and IssuesRepository.upsert_many.

        - Pydantic IssueLocation → plain dict
        - tags / references / extra normalized to list/dict
        - timestamps defaulted if missing
        """
        data = asdict(self)

        # Normalize tags / references / extra
        data["tags"] = self.tags or []
        data["references"] = self.references or []
        data["extra"] = self.extra or {}

        # Convert IssueLocation to plain dict if present
        if self.location is not None:
            try:
                data["location"] = self.location.dict()
            except Exception:
                # If conversion fails, we still don't want to crash the check
                data["location"] = None

        now = datetime.utcnow()
        data["created_at"] = self.created_at or now
        data["updated_at"] = self.updated_at or now

        return data


# ---------------------------------------------------------------------------
# Result structure returned by checks
# ---------------------------------------------------------------------------


@dataclass
class CheckRunResult:
    """
    Result of a single check run.

    - issues: list of issue payloads produced by this check
    - metrics: structured metrics / counters (e.g. items scanned)
    - errors: non-fatal errors encountered during the run
    """

    issues: List[CheckIssuePayload]
    metrics: Dict[str, Any]
    errors: List[str]

    def to_issue_dicts(self) -> List[Dict[str, Any]]:
        """
        Convert all CheckIssuePayloads into dicts for the IssuesService.
        """
        return [issue.to_issue_dict() for issue in self.issues]


# ---------------------------------------------------------------------------
# Logger protocol (so checks can accept any logger with .info/.warning/.error)
# ---------------------------------------------------------------------------


class LoggerLike(Protocol):
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


# ---------------------------------------------------------------------------
# BaseCheck
# ---------------------------------------------------------------------------


class BaseCheck(ABC):
    """
    Abstract base class for all checks.

    Concrete checks (github_deps, github_security, k8s_misconfig, ci_hardening)
    must implement:

    - id: stable identifier for the check (e.g. 'github_deps')
    - name: human-readable name
    - description: short description of what the check validates
    - category: e.g. 'security', 'reliability', 'perf', 'ops'
    - run(context, logger): async method that returns CheckRunResult
    """

    id: str
    name: str
    description: str
    category: str

    def __init__(self, *, default_severity: IssueSeverity = IssueSeverity.medium):
        self.default_severity = default_severity

    @abstractmethod
    async def run(
        self,
        context: CheckContext,
        logger: LoggerLike,
    ) -> CheckRunResult:
        """
        Run the check for the given org and return its result.

        This method must NOT raise for recoverable issues. Instead, it should:
        - capture non-fatal errors into result.errors
        - only raise on truly fatal problems that make the check impossible
          (e.g., invalid configuration).

        The scheduler will catch unexpected exceptions and record them.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Helper for subclasses
    # ------------------------------------------------------------------

    def build_issue(
        self,
        *,
        id: str,
        org_id: str,
        title: str,
        severity: Optional[IssueSeverity] = None,
        status: IssueStatus = IssueStatus.open,
        service: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        location: Optional[IssueLocation] = None,
        source: Optional[str] = None,
        short_description: Optional[str] = None,
        description: Optional[str] = None,
        root_cause: Optional[str] = None,
        impact: Optional[str] = None,
        proposed_fix: Optional[str] = None,
        precautions: Optional[str] = None,
        references: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
        first_seen_at: Optional[datetime] = None,
        last_seen_at: Optional[datetime] = None,
    ) -> CheckIssuePayload:
        """
        Convenience builder for issue payloads.

        Uses the check's `id` as `check_name` automatically.
        """
        return CheckIssuePayload(
            id=id,
            org_id=org_id,
            check_name=self.id,
            title=title,
            severity=severity or self.default_severity,
            status=status,
            service=service,
            category=category or self.category,
            tags=tags or [],
            location=location,
            source=source,
            short_description=short_description,
            description=description,
            root_cause=root_cause,
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=precautions,
            references=references or [],
            extra=extra or {},
            first_seen_at=first_seen_at,
            last_seen_at=last_seen_at,
        )
