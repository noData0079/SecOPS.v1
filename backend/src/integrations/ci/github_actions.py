# backend/src/integrations/ci/github_actions.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from utils.config import Settings  # type: ignore[attr-defined]
from integrations.github.client import get_github_client, GitHubClient
from integrations.github.ingestor import GitHubOrgMapping

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


@dataclass
class CIWorkflowSummary:
    """
    Summary of a single GitHub Actions workflow.

    Fields:
      - id: GitHub workflow id
      - name: workflow name
      - path: .github/workflows/...yml path in the repo
      - state: 'active' or 'disabled'
      - html_url: GitHub UI URL
      - uses_concurrency: True if the workflow defines 'concurrency:'
      - uses_permissions: True if the workflow defines 'permissions:'
      - raw_metadata: raw workflow JSON from GitHub
    """

    id: int
    name: str
    path: str
    state: str

    html_url: Optional[str] = None

    uses_concurrency: bool = False
    uses_permissions: bool = False

    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CIWorkflowSnapshot:
    """
    Snapshot of CI configuration for a single repository.

    Fields:
      - gh_org: GitHub organization slug
      - repo: repository name
      - workflows: list of CIWorkflowSummary
      - metrics: precomputed metrics for hardening checks
    """

    gh_org: str
    repo: str

    workflows: List[CIWorkflowSummary] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gh_org": self.gh_org,
            "repo": self.repo,
            "workflows": [w.to_dict() for w in self.workflows],
            "metrics": dict(self.metrics),
        }


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------


class GitHubActionsCollector:
    """
    Collects high-level GitHub Actions configuration for a repo.

    Responsibilities:
      - Resolve internal org_id -> GitHub org slug.
      - List workflows for a repo using GitHubClient.list_workflows.
      - Optionally fetch workflow YAML contents to detect:
          * 'concurrency:' usage
          * 'permissions:' usage
      - Compute simple metrics for CI hardening checks.

    NOTE: This collector focuses on static workflow configuration.
          It does NOT fetch per-run logs; that would require additional
          GitHubClient methods and is intentionally out-of-scope for now.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: GitHubClient = get_github_client(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect_repo_workflows(
        self,
        *,
        org_id: str,
        repo: str,
    ) -> CIWorkflowSnapshot:
        """
        Collect workflow configuration for a given repo.

        Returns a CIWorkflowSnapshot that ci_hardening checks can consume.
        """
        mapping = GitHubOrgMapping.resolve(self.settings, org_id)
        gh_org = mapping.github_org

        logger.info(
            "GitHubActionsCollector: collecting workflows for org_id=%s gh_org=%s repo=%s",
            org_id,
            gh_org,
            repo,
        )

        try:
            workflows_raw = await self.client.list_workflows(gh_org, repo)
        except Exception as exc:
            logger.exception(
                "GitHubActionsCollector: failed to list workflows for %s/%s: %s",
                gh_org,
                repo,
                exc,
            )
            return CIWorkflowSnapshot(gh_org=gh_org, repo=repo, workflows=[], metrics={
                "total_workflows": 0,
                "disabled_workflows": 0,
                "workflows_without_concurrency": 0,
                "workflows_without_permissions": 0,
                "error": f"list_workflows_failed: {type(exc).__name__}",
            })

        workflows: List[CIWorkflowSummary] = []

        for wf in workflows_raw:
            summary = await self._build_workflow_summary(
                gh_org=gh_org,
                repo=repo,
                wf=wf,
            )
            workflows.append(summary)

        metrics = self._compute_metrics(workflows)

        return CIWorkflowSnapshot(
            gh_org=gh_org,
            repo=repo,
            workflows=workflows,
            metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _build_workflow_summary(
        self,
        *,
        gh_org: str,
        repo: str,
        wf: Dict[str, Any],
    ) -> CIWorkflowSummary:
        """
        Build CIWorkflowSummary from a single GitHub workflow JSON object.

        Attempts to fetch the YAML file and detect whether it uses:
          - 'concurrency:'
          - 'permissions:'
        """
        wf_id = wf.get("id")
        name = wf.get("name") or f"workflow-{wf_id}"
        path = wf.get("path") or ""
        state = wf.get("state") or "active"
        html_url = wf.get("html_url")

        uses_concurrency = False
        uses_permissions = False

        # Best-effort analysis of workflow YAML
        yaml_text: Optional[str] = None
        if path:
            try:
                yaml_text = await self.client.get_workflow_file(
                    gh_org,
                    repo,
                    path=path,
                    ref=wf.get("head_branch") or wf.get("default_branch") or None,
                )
            except Exception:
                logger.exception(
                    "GitHubActionsCollector: failed to fetch workflow file %s for %s/%s",
                    path,
                    gh_org,
                    repo,
                )
                yaml_text = None

        if yaml_text:
            # Very basic scanning; we don't try to fully parse YAML here.
            lowered = yaml_text.lower()
            if "concurrency:" in lowered:
                uses_concurrency = True
            if "permissions:" in lowered:
                uses_permissions = True

        return CIWorkflowSummary(
            id=wf_id,
            name=name,
            path=path,
            state=state,
            html_url=html_url,
            uses_concurrency=uses_concurrency,
            uses_permissions=uses_permissions,
            raw_metadata={
                "id": wf_id,
                "name": name,
                "path": path,
                "state": state,
                "html_url": html_url,
                "created_at": wf.get("created_at"),
                "updated_at": wf.get("updated_at"),
            },
        )

    def _compute_metrics(self, workflows: List[CIWorkflowSummary]) -> Dict[str, Any]:
        """
        Derive small, useful metrics for CI hardening checks.

        Metrics:
          - total_workflows
          - disabled_workflows
          - workflows_without_concurrency
          - workflows_without_permissions
        """
        total = len(workflows)
        disabled = sum(1 for w in workflows if w.state != "active")
        without_concurrency = sum(1 for w in workflows if not w.uses_concurrency)
        without_permissions = sum(1 for w in workflows if not w.uses_permissions)

        return {
            "total_workflows": total,
            "disabled_workflows": disabled,
            "workflows_without_concurrency": without_concurrency,
            "workflows_without_permissions": without_permissions,
        }


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------


def get_github_actions_collector(settings: Settings) -> GitHubActionsCollector:
    """
    Factory helper for dependency injection.

    Typical usage inside ci_hardening check:

        from integrations.ci.github_actions import get_github_actions_collector
        from utils.config import settings

        collector = get_github_actions_collector(settings)
        snapshot = await collector.collect_repo_workflows(org_id=context.org_id, repo="api")

        # snapshot.workflows -> list of CIWorkflowSummary
        # snapshot.metrics   -> dict for quick thresholds
    """
    return GitHubActionsCollector(settings=settings)
