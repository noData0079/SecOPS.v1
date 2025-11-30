# backend/src/core/checks/github_deps.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueLocation,
)
from integrations.github.ingestor import GitHubDepsIngestor  # to be implemented
from .base import (
    BaseCheck,
    CheckContext,
    CheckRunResult,
    LoggerLike,
)


_SEVERITY_MAP: Dict[str, IssueSeverity] = {
    "critical": IssueSeverity.critical,
    "high": IssueSeverity.high,
    "moderate": IssueSeverity.medium,
    "medium": IssueSeverity.medium,
    "low": IssueSeverity.low,
    "info": IssueSeverity.info,
}


class GitHubDepsCheck(BaseCheck):
    """
    Check GitHub repositories for outdated / vulnerable dependencies.

    This check relies on the GitHub integration and the GitHubDepsIngestor, which
    is responsible for calling the GitHub API (Dependabot / security advisories /
    manifest analysis) and returning normalized dependency issues.

    Each returned alert is converted into a CheckIssuePayload which is then
    upserted into the Issues system by the scheduler / IssuesService.
    """

    id = "github_deps"
    name = "GitHub Dependencies"
    description = "Outdated or vulnerable dependencies in GitHub repositories."
    category = "security"

    def __init__(self) -> None:
        super().__init__(default_severity=IssueSeverity.medium)
        self._ingestor: Optional[GitHubDepsIngestor] = None

    def _get_ingestor(self, settings: Any) -> GitHubDepsIngestor:
        if self._ingestor is None:
            self._ingestor = GitHubDepsIngestor(settings=settings)
        return self._ingestor

    async def run(
        self,
        context: CheckContext,
        logger: LoggerLike,
    ) -> CheckRunResult:
        """
        Run the GitHub dependency check for the given org.

        Steps:
        - Ensure GitHub integration is available (lightweight check via extras)
        - Ask GitHubDepsIngestor for dependency issues for this org
        - Map each issue to a CheckIssuePayload
        - Return issues + metrics + non-fatal errors
        """
        org_id = context.org_id
        settings = context.settings

        issues: List[Any] = []
        errors: List[str] = []
        metrics: Dict[str, Any] = {
            "org_id": org_id,
            "alerts_total": 0,
            "alerts_by_severity": {},
            "repos_scanned": 0,
        }

        # Optional shortcut: if integrations layer knows GH is disabled,
        # it can mark this in context.extras so we skip work.
        github_enabled = context.get_extra("github_enabled", True)
        if not github_enabled:
            logger.info("GitHubDepsCheck skipped: GitHub integration disabled for org %s", org_id)
            metrics["skipped"] = True
            metrics["reason"] = "github_integration_disabled"
            return CheckRunResult(issues=[], metrics=metrics, errors=[])

        ingestor = self._get_ingestor(settings)

        try:
            # Expected: list of dicts with normalized dependency alerts.
            #
            # Each alert dict should have (we will implement the ingestor to match this):
            # {
            #   "id": str,
            #   "org_id": str,
            #   "repo": str,
            #   "package_name": str,
            #   "ecosystem": str,
            #   "current_version": str,
            #   "fixed_version": Optional[str],
            #   "severity": str,  # critical/high/medium/low/moderate
            #   "manifest_path": Optional[str],
            #   "summary": Optional[str],
            #   "description": Optional[str],
            #   "ghsa_id": Optional[str],
            #   "cve_ids": List[str],
            #   "vulnerable_range": Optional[str],
            #   "reference_url": Optional[str],
            # }
            alerts = await ingestor.list_dependency_issues(org_id=org_id)
        except Exception as exc:
            logger.exception("GitHubDepsCheck failed to fetch dependency issues")
            errors.append(f"ingestor_error: {type(exc).__name__}: {exc}")
            metrics["failed"] = True
            return CheckRunResult(issues=[], metrics=metrics, errors=errors)

        metrics["alerts_total"] = len(alerts)

        alerts_by_severity: Dict[str, int] = {}

        for alert in alerts:
            try:
                issue = self._build_issue_from_alert(org_id, alert)
                issues.append(issue)

                sev = str(issue.severity.value)
                alerts_by_severity[sev] = alerts_by_severity.get(sev, 0) + 1
            except Exception as exc:
                logger.exception("Failed to convert GitHub dependency alert to issue payload")
                errors.append(f"alert_conversion_error: {type(exc).__name__}: {exc}")
                # continue with other alerts

        metrics["alerts_by_severity"] = alerts_by_severity
        metrics["repos_scanned"] = context.get_extra("github_repos_scanned", 0)

        return CheckRunResult(
            issues=issues,
            metrics=metrics,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_issue_from_alert(self, org_id: str, alert: Dict[str, Any]):
        """
        Map a single ingestor alert into a CheckIssuePayload.
        """
        # Fallbacks and defaults
        repo = alert.get("repo", "unknown-repo")
        package_name = alert.get("package_name", "unknown-package")
        current_version = alert.get("current_version", "?")
        fixed_version = alert.get("fixed_version")
        severity_str = str(alert.get("severity", "medium")).lower()

        severity = _SEVERITY_MAP.get(severity_str, IssueSeverity.medium)

        manifest_path = alert.get("manifest_path")
        summary = alert.get("summary") or f"{package_name} has known vulnerabilities."
        description = alert.get("description") or summary

        # Title: concise but informative
        title = f"[{repo}] {package_name} {current_version} vulnerable ({severity.value.upper()})"

        # Issue ID: stable if ingestor gives one, otherwise deterministic-ish
        issue_id = alert.get("id") or f"{org_id}:{repo}:{package_name}:{current_version}:{severity.value}"

        # Build location
        location = IssueLocation(
            kind="code",
            repo=repo,
            file_path=manifest_path,
            line=None,
            cluster=None,
            namespace=None,
            resource_kind=None,
            resource_name=None,
            environment="prod",  # default assumption; can be refined later
            metadata={
                "manifest_path": manifest_path,
            },
        )

        references: List[str] = []
        reference_url = alert.get("reference_url")
        if reference_url:
            references.append(reference_url)

        ghsa_id = alert.get("ghsa_id")
        cve_ids = alert.get("cve_ids") or []
        vulnerable_range = alert.get("vulnerable_range")

        extra: Dict[str, Any] = {
            "ecosystem": alert.get("ecosystem"),
            "package_name": package_name,
            "current_version": current_version,
            "fixed_version": fixed_version,
            "ghsa_id": ghsa_id,
            "cve_ids": cve_ids,
            "vulnerable_range": vulnerable_range,
            "raw": alert,
        }

        short_description = f"{package_name} ({current_version}) in {repo} has a {severity.value} vulnerability."

        # Build CheckIssuePayload using BaseCheck helper
        issue_payload = self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=severity,
            status=IssueStatus.open,
            service=repo,
            category="dependency",
            tags=[
                "github",
                "dependencies",
                "supply_chain",
                severity.value,
            ],
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause="Outdated or vulnerable dependency identified by GitHub security analysis.",
            impact="This dependency version is known to have security vulnerabilities which may be exploitable.",
            proposed_fix=self._build_proposed_fix_text(package_name, current_version, fixed_version),
            precautions="Verify that upgrading does not introduce breaking changes; run your test suite and canary releases.",
            references=references,
            extra=extra,
        )

        return issue_payload

    def _build_proposed_fix_text(
        self,
        package_name: str,
        current_version: str,
        fixed_version: Optional[str],
    ) -> str:
        if fixed_version:
            return (
                f"Upgrade {package_name} from {current_version} to at least {fixed_version}, "
                "or a later patched version recommended by the advisory."
            )
        return (
            f"Upgrade {package_name} from {current_version} to the latest stable version "
            "recommended by the project or advisory."
        )
