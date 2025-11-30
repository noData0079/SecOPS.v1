# backend/src/integrations/github/ingestor.py

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils.config import Settings  # type: ignore[attr-defined]
from integrations.github.client import GitHubClient, get_github_client

logger = logging.getLogger(__name__)


@dataclass
class GitHubOrgMapping:
    """
    Mapping between internal org_id and GitHub organization slug.

    Example settings.GITHUB_ORG_MAP:
        {
          "org-123": "my-github-org",
          "org-xyz": "customer-org",
        }

    If no mapping exists, we assume org_id == GitHub org name.
    """

    internal_id: str
    github_org: str

    @classmethod
    def resolve(cls, settings: Settings, org_id: str) -> "GitHubOrgMapping":
        # 1) Try explicit mapping from settings
        mapping = getattr(settings, "GITHUB_ORG_MAP", None)
        if isinstance(mapping, dict) and org_id in mapping:
            return cls(internal_id=org_id, github_org=str(mapping[org_id]))

        # 2) Optional fallback from env var JSON, e.g. {"org-1": "my-org"}
        raw_env = os.getenv("GITHUB_ORG_MAP_JSON")
        if raw_env:
            import json

            try:
                env_map = json.loads(raw_env)
                if isinstance(env_map, dict) and org_id in env_map:
                    return cls(internal_id=org_id, github_org=str(env_map[org_id]))
            except Exception:
                logger.exception("Failed to parse GITHUB_ORG_MAP_JSON")

        # 3) Default: assume org_id is already the GitHub org slug
        return cls(internal_id=org_id, github_org=org_id)


class GitHubSecurityIngestor:
    """
    Higher-level helper on top of GitHubClient.

    Responsibilities:
    - resolve internal org_id -> GitHub org slug
    - list repos for that org
    - fetch security-related signals (Dependabot & Code Scanning alerts)
    - normalize them into a consistent structure for checks/services

    Used by:
      - security checks (e.g. GitHubSecurityCheck, GitHubDepsCheck)
      - platform / issues services that want a summary view
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: GitHubClient = get_github_client(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect_security_snapshot(
        self,
        *,
        org_id: str,
    ) -> Dict[str, Any]:
        """
        Collect a snapshot of GitHub security signals for the given org.

        Returns a structure like:

        {
          "org": "github-org-slug",
          "repos": [
            {
              "name": "api",
              "full_name": "my-org/api",
              "private": true,
              "default_branch": "main",
              "dependabot_alerts": [
                {
                  "id": "123",
                  "number": 123,
                  "severity": "high",
                  "state": "open",
                  "dependency": "lodash",
                  "ecosystem": "npm",
                  "manifest": "package.json",
                  "summary": "...",
                  "gh_url": "https://github.com/...",
                },
                ...
              ],
              "code_scanning_alerts": [
                {
                  "id": "456",
                  "number": 456,
                  "severity": "medium",
                  "state": "open",
                  "rule_id": "js/xss",
                  "rule_name": "Cross-site scripting",
                  "tool": "CodeQL",
                  "gh_url": "https://github.com/...",
                },
                ...
              ],
            },
            ...
          ],
          "metrics": {
            "repos_count": 5,
            "dependabot_open": 12,
            "code_scanning_open": 7,
          },
        }
        """
        mapping = GitHubOrgMapping.resolve(self.settings, org_id)
        gh_org = mapping.github_org

        logger.info("GitHubSecurityIngestor: collecting signals for org_id=%s gh_org=%s", org_id, gh_org)

        repos_data: List[Dict[str, Any]] = []

        try:
            repos = await self.client.list_org_repos(gh_org)
        except Exception as exc:
            logger.exception("Failed to list GitHub repos for org %s", gh_org)
            return {
                "org": gh_org,
                "repos": [],
                "metrics": {
                    "repos_count": 0,
                    "dependabot_open": 0,
                    "code_scanning_open": 0,
                    "error": f"list_org_repos_failed: {type(exc).__name__}",
                },
            }

        total_dependabot_open = 0
        total_code_scanning_open = 0

        for repo in repos:
            name = repo.get("name")
            full_name = repo.get("full_name") or f"{gh_org}/{name}"
            if not name:
                continue

            try:
                dep_alerts_raw = await self.client.list_dependabot_alerts(
                    gh_org,
                    name,
                    state="open",
                )
            except Exception as exc:
                logger.exception(
                    "Failed to fetch Dependabot alerts for %s/%s", gh_org, name
                )
                dep_alerts_raw = []

            try:
                cs_alerts_raw = await self.client.list_code_scanning_alerts(
                    gh_org,
                    name,
                    state="open",
                )
            except Exception as exc:
                logger.exception(
                    "Failed to fetch code scanning alerts for %s/%s", gh_org, name
                )
                cs_alerts_raw = []

            dep_alerts = [self._normalize_dependabot_alert(a) for a in dep_alerts_raw]
            cs_alerts = [self._normalize_code_scanning_alert(a) for a in cs_alerts_raw]

            total_dependabot_open += len(dep_alerts)
            total_code_scanning_open += len(cs_alerts)

            repos_data.append(
                {
                    "name": name,
                    "full_name": full_name,
                    "private": repo.get("private"),
                    "default_branch": repo.get("default_branch"),
                    "html_url": repo.get("html_url"),
                    "dependabot_alerts": dep_alerts,
                    "code_scanning_alerts": cs_alerts,
                }
            )

        metrics = {
            "repos_count": len(repos_data),
            "dependabot_open": total_dependabot_open,
            "code_scanning_open": total_code_scanning_open,
        }

        return {
            "org": gh_org,
            "repos": repos_data,
            "metrics": metrics,
        }

    # ------------------------------------------------------------------
    # Normalization helpers
    # ------------------------------------------------------------------

    def _normalize_dependabot_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a Dependabot alert into a compact, stable structure.
        """
        number = alert.get("number")
        gh_id = alert.get("id") or number

        security_vuln = alert.get("security_vulnerability") or {}
        security_advisory = alert.get("security_advisory") or {}
        dependency = security_vuln.get("package") or {}

        dependency_name = dependency.get("name")
        ecosystem = dependency.get("ecosystem")
        severity = security_vuln.get("severity") or security_advisory.get("severity")
        summary = security_advisory.get("summary") or alert.get("summary")
        gh_url = alert.get("html_url") or alert.get("url")

        return {
            "id": str(gh_id) if gh_id is not None else None,
            "number": number,
            "severity": severity,
            "state": alert.get("state"),
            "dependency": dependency_name,
            "ecosystem": ecosystem,
            "manifest": alert.get("manifest_path"),
            "summary": summary,
            "fixed_version": security_vuln.get("first_patched_version", {}).get("identifier"),
            "gh_url": gh_url,
            "raw": {
                "created_at": alert.get("created_at"),
                "updated_at": alert.get("updated_at"),
            },
        }

    def _normalize_code_scanning_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a code scanning alert into a compact, stable structure.
        """
        number = alert.get("number")
        gh_id = alert.get("id") or number

        rule = alert.get("rule") or {}
        tool = alert.get("tool") or {}
        most_recent_instance = alert.get("most_recent_instance") or {}

        return {
            "id": str(gh_id) if gh_id is not None else None,
            "number": number,
            "severity": alert.get("severity"),
            "state": alert.get("state"),
            "rule_id": rule.get("id"),
            "rule_name": rule.get("name"),
            "tool": tool.get("name"),
            "gh_url": alert.get("html_url") or alert.get("url"),
            "raw": {
                "created_at": alert.get("created_at"),
                "updated_at": alert.get("updated_at"),
                "most_recent_instance": {
                    "ref": most_recent_instance.get("ref"),
                    "analysis_key": most_recent_instance.get("analysis_key"),
                    "category": most_recent_instance.get("category"),
                    "location": most_recent_instance.get("location"),
                },
            },
        }
