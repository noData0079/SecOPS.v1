from __future__ import annotations

from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.checks.base import CheckContext
from src.core.checks.ci_hardening import CIHardeningCheck
from src.core.issues.service import create_issue
from .mappers import check_result_to_issue_payload


async def run_github_checks_for_repo(db: AsyncSession, repo_full_name: str) -> List[str]:
    """
    Run GitHub-specific checks (CI hardening) and create issues.

    Returns list of issue IDs created.
    """
    ctx = CheckContext(extra={"github_repo": repo_full_name})
    check = CIHardeningCheck()
    results = await check.run(ctx)
    ids: List[str] = []
    for r in results:
        payload_dict = check_result_to_issue_payload(r)
        issue = await create_issue(db, payload_dict)  # type: ignore[arg-type]
        ids.append(issue.id)
    return ids


class GitHubDepsIngestor:
    """Stub for GitHubDepsIngestor."""
    def __init__(self, settings: Any):
        self.settings = settings

    async def list_dependency_issues(self, org_id: str) -> List[Dict[str, Any]]:
        return []


class GitHubSecurityIngestor:
    """Stub for GitHubSecurityIngestor."""
    def __init__(self, settings: Any):
        self.settings = settings

    async def list_security_alerts(self, org_id: str) -> List[Dict[str, Any]]:
        return []
