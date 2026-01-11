# backend/src/core/checks/github_security.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueLocation,
)
from src.integrations.github.ingestor import GitHubSecurityIngestor  # to be implemented
from .base import (
    BaseCheck,
    CheckContext,
    CheckRunResult,
    LoggerLike,
)


_SEVERITY_MAP: Dict[str, IssueSeverity] = {
    "critical": IssueSeverity.critical,
    "high": IssueSeverity.high,
    "medium": IssueSeverity.medium,
    "moderate": IssueSeverity.medium,
    "low": IssueSeverity.low,
    "info": IssueSeverity.info,
}


class GitHubSecurityCheck(BaseCheck):
    """
    Check GitHub repositories for security alerts (code scanning, secret leaks,
    dependency alerts that are not purely version-based, etc.).

    This uses the GitHubSecurityIngestor which is responsible for:
    - calling GitHub code scanning / security alert APIs
    - normalizing alerts into a simple list of dicts

    Each alert is turned into a CheckIssuePayload and then upserted into the
    issues system by the scheduler + IssuesService.
    """

    id = "github_security"
    name = "GitHub Security Alerts"
    description = "Security alerts from GitHub (code scanning, secrets, etc.)."
    category = "security"

    def __init__(self) -> None:
        super().__init__(default_severity=IssueSeverity.high)
        self._ingestor: Optional[GitHubSecurityIngestor] = None

    def _get_ingestor(self, settings: Any) -> GitHubSecurityIngestor:
        if self._ingestor is None:
            self._ingestor = GitHubSecurityIngestor(settings=settings)
        return self._ingestor

    async def run(
        self,
        context: CheckContext,
        logger: LoggerLike,
    ) -> CheckRunResult:
        """
        Run the GitHub security alerts check for the given org.

        Steps:
        - Check if GitHub integration is enabled (via extras)
        - Fetch security alerts via GitHubSecurityIngestor
        - Convert each alert into a CheckIssuePayload
        - Return issues + metrics + non-fatal errors
        """
        org_id = context.org_id
        settings = context.settings

        issues = []
        errors: List[str] = []
        metrics: Dict[str, Any] = {
            "org_id": org_id,
            "alerts_total": 0,
            "alerts_by_severity": {},
            "repos_scanned": 0,
        }

        github_enabled = context.get_extra("github_enabled", True)
        if not github_enabled:
            logger.info(
                "GitHubSecurityCheck skipped: GitHub integration disabled for org %s",
                org_id,
            )
            metrics["skipped"] = True
            metrics["reason"] = "github_integration_disabled"
            return CheckRunResult(issues=[], metrics=metrics, errors=[])

        ingestor = self._get_ingestor(settings)

        try:
            # Expected normalized alert structure from GitHubSecurityIngestor:
            # {
            #   "id": str,
            #   "org_id": str,
            #   "repo": str,
            #   "alert_type": str,      # 'code_scanning', 'secret_scanning', etc.
            #   "rule_id": str | None,
            #   "rule_name": str | None,
            #   "severity": str,        # critical/high/medium/low/info
            #   "state": str,           # 'open', 'fixed', 'dismissed', etc.
            #   "file_path": str | None,
            #   "start_line": int | None,
            #   "end_line": int | None,
            #   "summary": str | None,
            #   "description": str | None,
            #   "reference_url": str | None,
            #   "tags": list[str],
            # }
            alerts = await ingestor.list_security_alerts(org_id=org_id)
        except Exception as exc:
            logger.exception("GitHubSecurityCheck failed to fetch security alerts")
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
                logger.exception(
                    "Failed to convert GitHub security alert to issue payload",
                )
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
        Map a single security alert dict into a CheckIssuePayload.
        """
        repo = alert.get("repo", "unknown-repo")
        alert_type = alert.get("alert_type", "security_alert")
        rule_name = alert.get("rule_name") or alert.get("rule_id") or alert_type
        severity_str = str(alert.get("severity", "high")).lower()
        severity = _SEVERITY_MAP.get(severity_str, IssueSeverity.high)

        state = str(alert.get("state", "open")).lower()
        status = IssueStatus.open
        if state in {"fixed", "resolved"}:
            status = IssueStatus.resolved
        elif state in {"dismissed", "ignored"}:
            status = IssueStatus.suppressed

        file_path = alert.get("file_path")
        start_line = alert.get("start_line")
        end_line = alert.get("end_line")

        summary = alert.get("summary") or f"{alert_type} in {repo}"
        description = alert.get("description") or summary

        title = f"[{repo}] {rule_name} ({severity.value.upper()})"

        # Use ingestor id if provided, otherwise derive something stable-ish
        issue_id = alert.get("id") or f"{org_id}:{repo}:{alert_type}:{rule_name}:{severity.value}"

        location = IssueLocation(
            kind="code",
            repo=repo,
            file_path=file_path,
            line=start_line,
            cluster=None,
            namespace=None,
            resource_kind=None,
            resource_name=None,
            environment="prod",
            metadata={
                "start_line": start_line,
                "end_line": end_line,
            },
        )

        references: List[str] = []
        ref_url = alert.get("reference_url")
        if ref_url:
            references.append(ref_url)

        tags: List[str] = alert.get("tags") or []
        # Ensure some standard tags
        tags = list(set(tags + ["github", "security", alert_type, severity.value]))

        extra: Dict[str, Any] = {
            "alert_type": alert_type,
            "rule_id": alert.get("rule_id"),
            "rule_name": rule_name,
            "state": state,
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "raw": alert,
        }

        short_description = (
            f"{alert_type.replace('_', ' ').title()} finding in {repo}: {rule_name} "
            f"({severity.value} severity)."
        )

        impact = (
            "Potential security vulnerability or misconfiguration detected in code. "
            "If exploited, this may allow unauthorized access, data exposure, or "
            "other security impact depending on context."
        )

        root_cause = (
            "GitHub code scanning or security analysis detected a pattern or behavior "
            "matching a known vulnerability or risky practice."
        )

        proposed_fix = self._build_proposed_fix_text(rule_name, alert_type)

        issue_payload = self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=severity,
            status=status,
            service=repo,
            category="security",
            tags=tags,
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause=root_cause,
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Review the suggested code changes carefully. "
                "Ensure tests cover the affected paths and run them before deploying."
            ),
            references=references,
            extra=extra,
        )

        return issue_payload

    def _build_proposed_fix_text(
        self,
        rule_name: str,
        alert_type: str,
    ) -> str:
        base = f"Address the '{rule_name}' finding reported by GitHub ({alert_type}). "
        return (
            base
            + "Follow GitHub's remediation guidance or security advisory, "
              "update the affected code or configuration, and verify that the "
              "vulnerability is no longer reported after re-running scans."
        )
