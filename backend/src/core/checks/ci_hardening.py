# backend/src/core/checks/ci_hardening.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueLocation,
)
from integrations.ci.github_actions import GitHubActionsCollector  # to be implemented
from .base import (
    BaseCheck,
    CheckContext,
    CheckRunResult,
    LoggerLike,
)


class CIHardeningCheck(BaseCheck):
    """
    CI / pipeline hardening check.

    Focuses on common GitHub Actions security pitfalls:
    - workflows triggered by untrusted pull requests without safeguards
    - unpinned third-party actions (supply chain risk)
    - overly permissive GITHUB_TOKEN or missing permissions restrictions

    Uses GitHubActionsCollector to fetch workflows and metadata.
    """

    id = "ci_hardening"
    name = "CI Pipeline Hardening"
    description = "Detects insecure or weakly hardened CI pipelines."
    category = "security"

    def __init__(self) -> None:
        super().__init__(default_severity=IssueSeverity.medium)
        self._collector: Optional[GitHubActionsCollector] = None

    def _get_collector(self, settings: Any) -> GitHubActionsCollector:
        if self._collector is None:
            self._collector = GitHubActionsCollector(settings=settings)
        return self._collector

    async def run(
        self,
        context: CheckContext,
        logger: LoggerLike,
    ) -> CheckRunResult:
        """
        Run the CI hardening check.

        Steps:
        - Check if GitHub integration is enabled
        - Fetch workflow metadata from GitHubActionsCollector
        - Analyze for common misconfigurations and build issues
        """
        org_id = context.org_id
        settings = context.settings

        issues = []
        errors: List[str] = []
        metrics: Dict[str, Any] = {
            "org_id": org_id,
            "repos_scanned": 0,
            "workflows_scanned": 0,
            "issues_by_type": {},
        }

        github_enabled = context.get_extra("github_enabled", True)
        if not github_enabled:
            logger.info(
                "CIHardeningCheck skipped: GitHub integration disabled for org %s",
                org_id,
            )
            metrics["skipped"] = True
            metrics["reason"] = "github_integration_disabled"
            return CheckRunResult(issues=[], metrics=metrics, errors=[])

        collector = self._get_collector(settings)

        try:
            # Expected structure from GitHubActionsCollector (we'll implement to match):
            #
            # workflows = await collector.list_workflows(org_id)
            #
            # Each workflow dict:
            # {
            #   "repo": "owner/repo",
            #   "file": ".github/workflows/ci.yml",
            #   "name": "CI",
            #   "triggers": {
            #       "push": True/False,
            #       "pull_request": True/False,
            #       "pull_request_from_forks": True/False,
            #   },
            #   "uses_unpinned_actions": bool,
            #   "uses_untrusted_actions": bool,
            #   "github_token_permissions_restricted": bool,
            #   "raw": {...},  # optional raw workflow info
            # }
            workflows = await collector.list_workflows(org_id=org_id)
        except Exception as exc:
            logger.exception("CIHardeningCheck failed to fetch workflows from GitHub")
            errors.append(f"collector_error: {type(exc).__name__}: {exc}")
            metrics["failed"] = True
            return CheckRunResult(issues=[], metrics=metrics, errors=errors)

        metrics["workflows_scanned"] = len(workflows)
        metrics["repos_scanned"] = len({wf.get("repo") for wf in workflows})

        for wf in workflows:
            try:
                new_issues = self._analyze_workflow(org_id, wf)
                for issue in new_issues:
                    issues.append(issue)
                    key = issue.category or "ci_hardening"
                    metrics["issues_by_type"][key] = metrics["issues_by_type"].get(key, 0) + 1
            except Exception as exc:
                logger.exception(
                    "Failed to analyze workflow for CI hardening: %s",
                    wf.get("file"),
                )
                errors.append(f"workflow_analysis_error: {type(exc).__name__}: {exc}")

        return CheckRunResult(
            issues=issues,
            metrics=metrics,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _analyze_workflow(
        self,
        org_id: str,
        wf: Dict[str, Any],
    ):
        issues = []

        repo = wf.get("repo", "unknown-repo")
        file_path = wf.get("file", ".github/workflows/unknown.yml")
        name = wf.get("name") or file_path

        triggers = wf.get("triggers") or {}
        uses_unpinned_actions = bool(wf.get("uses_unpinned_actions"))
        uses_untrusted_actions = bool(wf.get("uses_untrusted_actions"))
        token_restricted = bool(wf.get("github_token_permissions_restricted"))

        # 1) Pull request from forks without safeguards
        if triggers.get("pull_request_from_forks") and not token_restricted:
            issues.append(
                self._build_pr_forks_issue(
                    org_id=org_id,
                    repo=repo,
                    file_path=file_path,
                    workflow_name=name,
                )
            )

        # 2) Unpinned actions
        if uses_unpinned_actions:
            issues.append(
                self._build_unpinned_actions_issue(
                    org_id=org_id,
                    repo=repo,
                    file_path=file_path,
                    workflow_name=name,
                )
            )

        # 3) Untrusted third-party actions (optional flag from collector)
        if uses_untrusted_actions:
            issues.append(
                self._build_untrusted_actions_issue(
                    org_id=org_id,
                    repo=repo,
                    file_path=file_path,
                    workflow_name=name,
                )
            )

        # 4) Token not restricted at all (even for push workflows)
        if triggers.get("push") and not token_restricted:
            issues.append(
                self._build_token_permissions_issue(
                    org_id=org_id,
                    repo=repo,
                    file_path=file_path,
                    workflow_name=name,
                )
            )

        return issues

    def _build_location(
        self,
        *,
        repo: str,
        file_path: str,
    ) -> IssueLocation:
        return IssueLocation(
            kind="code",
            repo=repo,
            file_path=file_path,
            line=None,
            cluster=None,
            namespace=None,
            resource_kind="Workflow",
            resource_name=file_path,
            environment=None,
            metadata={},
        )

    def _build_pr_forks_issue(
        self,
        *,
        org_id: str,
        repo: str,
        file_path: str,
        workflow_name: str,
    ):
        title = f"[{repo}] Workflow '{workflow_name}' runs pull_request from forks with broad token"

        location = self._build_location(repo=repo, file_path=file_path)

        short_description = (
            f"Workflow '{workflow_name}' in {repo} is triggered by pull requests from "
            "forks and uses a non-restricted GITHUB_TOKEN."
        )

        description = (
            "This workflow runs on pull requests from forked repositories while using "
            "a GITHUB_TOKEN with broad permissions. An attacker can modify the workflow "
            "in a fork and potentially exfiltrate secrets or modify project state."
        )

        impact = (
            "Compromised forks can lead to supply chain attacks, secret exfiltration, "
            "or unauthorized changes through CI."
        )

        proposed_fix = (
            "Limit the scope of GITHUB_TOKEN for pull_request events, avoid secrets "
            "exposure in these jobs, and consider using restricted workflows or "
            "separate checks that run without sensitive permissions."
        )

        issue_id = f"{org_id}:{repo}:{file_path}:ci_pr_forks_unsafe"

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.high,
            status=IssueStatus.open,
            service=repo,
            category="ci_pr_forks",
            tags=[
                "ci",
                "github_actions",
                "pull_request",
                "security",
            ],
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause=(
                "Workflow is configured to run for pull_request events from forks "
                "with a broadly scoped GITHUB_TOKEN."
            ),
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "After tightening permissions, verify that required jobs still run "
                "and that no critical functionality was accidentally removed."
            ),
            references=[
                "https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions",
            ],
            extra={
                "repo": repo,
                "workflow_file": file_path,
                "workflow_name": workflow_name,
            },
        )

    def _build_unpinned_actions_issue(
        self,
        *,
        org_id: str,
        repo: str,
        file_path: str,
        workflow_name: str,
    ):
        title = f"[{repo}] Workflow '{workflow_name}' uses unpinned actions"

        location = self._build_location(repo=repo, file_path=file_path)

        short_description = (
            f"Workflow '{workflow_name}' in {repo} uses third-party actions without pinning "
            "to a specific commit SHA."
        )

        description = (
            "When actions are referenced by a floating tag (e.g., '@v3') instead of a "
            "specific commit SHA, a malicious or compromised maintainer can push a "
            "backdoored version that your pipeline will automatically consume."
        )

        impact = (
            "Unpinned actions increase supply chain risk; an attacker can gain control "
            "over your CI execution environment and potentially exfiltrate secrets or "
            "inject malicious behavior into deployments."
        )

        proposed_fix = (
            "Pin all third-party actions to a specific commit SHA. Optionally use tools "
            "to periodically audit and update pinned SHAs to newer trusted versions."
        )

        issue_id = f"{org_id}:{repo}:{file_path}:ci_unpinned_actions"

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.medium,
            status=IssueStatus.open,
            service=repo,
            category="ci_unpinned_actions",
            tags=[
                "ci",
                "github_actions",
                "supply_chain",
            ],
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause="Workflow references third-party actions using tags instead of commit SHAs.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Verify the integrity and authenticity of actions before pinning; "
                "keep an internal record of approved SHAs."
            ),
            references=[
                "https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions",
            ],
            extra={
                "repo": repo,
                "workflow_file": file_path,
                "workflow_name": workflow_name,
            },
        )

    def _build_untrusted_actions_issue(
        self,
        *,
        org_id: str,
        repo: str,
        file_path: str,
        workflow_name: str,
    ):
        title = f"[{repo}] Workflow '{workflow_name}' uses untrusted third-party actions"

        location = self._build_location(repo=repo, file_path=file_path)

        short_description = (
            f"Workflow '{workflow_name}' in {repo} uses actions from untrusted or unknown "
            "publishers."
        )

        description = (
            "This workflow relies on third-party actions from publishers that are not "
            "on your approved list. If one of these actions is compromised, your CI "
            "environment may be at risk."
        )

        impact = (
            "Malicious or compromised third-party actions can exfiltrate secrets, alter "
            "build artifacts, or otherwise compromise your software supply chain."
        )

        proposed_fix = (
            "Review and approve trusted actions, restrict usage to a curated set, and "
            "consider mirroring or vendoring critical actions."
        )

        issue_id = f"{org_id}:{repo}:{file_path}:ci_untrusted_actions"

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.medium,
            status=IssueStatus.open,
            service=repo,
            category="ci_untrusted_actions",
            tags=[
                "ci",
                "github_actions",
                "supply_chain",
                "third_party",
            ],
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause="Workflow uses actions from untrusted or unknown publishers.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Maintain an allowlist of approved publishers and actions; periodically "
                "audit their activity and security posture."
            ),
            references=[
                "https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions",
            ],
            extra={
                "repo": repo,
                "workflow_file": file_path,
                "workflow_name": workflow_name,
            },
        )

    def _build_token_permissions_issue(
        self,
        *,
        org_id: str,
        repo: str,
        file_path: str,
        workflow_name: str,
    ):
        title = f"[{repo}] Workflow '{workflow_name}' does not restrict GITHUB_TOKEN permissions"

        location = self._build_location(repo=repo, file_path=file_path)

        short_description = (
            f"Workflow '{workflow_name}' in {repo} uses the default broad GITHUB_TOKEN "
            "permissions."
        )

        description = (
            "This workflow uses the default permissions for GITHUB_TOKEN, which often "
            "grant write access to many resources. If the workflow is compromised, an "
            "attacker may be able to push code, open PRs, or modify issues."
        )

        impact = (
            "Compromised workflows with broad token permissions can cause significant "
            "damage to repositories and infrastructure."
        )

        proposed_fix = (
            "Explicitly set the `permissions` key in the workflow to the minimum "
            "required for each job, following the principle of least privilege."
        )

        issue_id = f"{org_id}:{repo}:{file_path}:ci_token_permissions"

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.medium,
            status=IssueStatus.open,
            service=repo,
            category="ci_token_permissions",
            tags=[
                "ci",
                "github_actions",
                "permissions",
                "security",
            ],
            location=location,
            source="github",
            short_description=short_description,
            description=description,
            root_cause="Workflow relies on default broad GITHUB_TOKEN permissions.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "After restricting permissions, validate that the workflow still "
                "has enough access to perform required actions."
            ),
            references=[
                "https://docs.github.com/en/actions/security-guides/automatic-token-authentication#modifying-the-permissions-for-the-github_token",
            ],
            extra={
                "repo": repo,
                "workflow_file": file_path,
                "workflow_name": workflow_name,
            },
        )
