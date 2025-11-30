# backend/src/integrations/github/mappers.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal GitHub → domain models
# ---------------------------------------------------------------------------


@dataclass
class GitHubRepoRef:
    """
    Minimal reference to a GitHub repository in our internal model.
    """

    org: str
    name: str
    full_name: str
    private: bool = False
    default_branch: Optional[str] = None
    html_url: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubSecurityFinding:
    """
    Unified representation of a GitHub security-related signal.

    This flattens both Dependabot and Code Scanning alerts into a single
    type so that checks / services can handle them uniformly.

    Fields:
      - kind: "dependabot" | "code_scanning"
      - org_id: internal org id (if caller passes one)
      - gh_org: GitHub organization slug
      - repo: repository reference
      - id: provider id (string)
      - number: provider numeric id (if any)
      - severity: "low" | "medium" | "high" | "critical" | None
      - state: "open" | "fixed" | "dismissed" | ...
      - title: short title / summary
      - description: longer description (if available)
      - url: HTML URL to view the alert in GitHub
      - metadata: provider-specific extra fields
    """

    kind: str  # "dependabot" or "code_scanning"

    gh_org: str
    repo: GitHubRepoRef

    # Optional link back to the internal tenant/org
    org_id: Optional[str] = None

    id: Optional[str] = None
    number: Optional[int] = None

    severity: Optional[str] = None
    state: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def repo_from_snapshot_entry(
    *,
    gh_org: str,
    repo_entry: Dict[str, Any],
) -> GitHubRepoRef:
    """
    Convert a single repo entry from GitHubSecurityIngestor snapshot into
    a GitHubRepoRef.
    """
    name = repo_entry.get("name") or ""
    full_name = repo_entry.get("full_name") or f"{gh_org}/{name}"

    return GitHubRepoRef(
        org=gh_org,
        name=name,
        full_name=full_name,
        private=bool(repo_entry.get("private")),
        default_branch=repo_entry.get("default_branch"),
        html_url=repo_entry.get("html_url"),
        metadata={k: v for k, v in repo_entry.items() if k not in {
            "name",
            "full_name",
            "private",
            "default_branch",
            "html_url",
            "dependabot_alerts",
            "code_scanning_alerts",
        }},
    )


def flatten_security_snapshot(
    *,
    snapshot: Dict[str, Any],
    org_id: Optional[str] = None,
) -> List[GitHubSecurityFinding]:
    """
    Flatten the structure returned by GitHubSecurityIngestor.collect_security_snapshot
    into a list of GitHubSecurityFinding objects.

    Expected snapshot structure (from ingestor.collect_security_snapshot):

        {
          "org": "github-org-slug",
          "repos": [
            {
              "name": "api",
              "full_name": "my-org/api",
              "private": true,
              "default_branch": "main",
              "html_url": "https://github.com/...",
              "dependabot_alerts": [ ... ],
              "code_scanning_alerts": [ ... ],
            },
            ...
          ],
          "metrics": {...},
        }

    Returns:
        List[GitHubSecurityFinding]
    """
    findings: List[GitHubSecurityFinding] = []

    gh_org = snapshot.get("org") or ""
    repos = snapshot.get("repos") or []

    if not isinstance(repos, list):
        logger.warning("flatten_security_snapshot: snapshot.repos is not a list")
        return findings

    for repo_entry in repos:
        if not isinstance(repo_entry, dict):
            continue

        repo_ref = repo_from_snapshot_entry(gh_org=gh_org, repo_entry=repo_entry)

        # Dependabot alerts (already normalized by ingestor)
        dep_alerts = repo_entry.get("dependabot_alerts") or []
        if isinstance(dep_alerts, list):
            for alert in dep_alerts:
                if not isinstance(alert, dict):
                    continue
                findings.append(_map_dependabot_alert_to_finding(
                    org_id=org_id,
                    gh_org=gh_org,
                    repo=repo_ref,
                    alert=alert,
                ))

        # Code scanning alerts (already normalized by ingestor)
        cs_alerts = repo_entry.get("code_scanning_alerts") or []
        if isinstance(cs_alerts, list):
            for alert in cs_alerts:
                if not isinstance(alert, dict):
                    continue
                findings.append(_map_code_scanning_alert_to_finding(
                    org_id=org_id,
                    gh_org=gh_org,
                    repo=repo_ref,
                    alert=alert,
                ))

    return findings


# ---------------------------------------------------------------------------
# Internal mapping for each alert kind
# ---------------------------------------------------------------------------


def _map_dependabot_alert_to_finding(
    *,
    org_id: Optional[str],
    gh_org: str,
    repo: GitHubRepoRef,
    alert: Dict[str, Any],
) -> GitHubSecurityFinding:
    """
    Turn a normalized Dependabot alert (from ingestor._normalize_dependabot_alert)
    into a GitHubSecurityFinding.
    """
    # Alert structure from ingestor._normalize_dependabot_alert:
    #
    # {
    #   "id": "123",
    #   "number": 123,
    #   "severity": "high",
    #   "state": "open",
    #   "dependency": "lodash",
    #   "ecosystem": "npm",
    #   "manifest": "package.json",
    #   "summary": "...",
    #   "fixed_version": "...",
    #   "gh_url": "https://github.com/...",
    #   "raw": {...},
    # }
    dep = alert.get("dependency")
    eco = alert.get("ecosystem")
    manifest = alert.get("manifest")
    title = alert.get("summary") or f"{dep} vulnerability" if dep else "Dependabot alert"

    description = alert.get("summary")
    url = alert.get("gh_url")

    metadata = {
        "kind": "dependabot",
        "dependency": dep,
        "ecosystem": eco,
        "manifest": manifest,
        "fixed_version": alert.get("fixed_version"),
        "raw": alert.get("raw"),
    }

    return GitHubSecurityFinding(
        kind="dependabot",
        org_id=org_id,
        gh_org=gh_org,
        repo=repo,
        id=alert.get("id"),
        number=alert.get("number"),
        severity=alert.get("severity"),
        state=alert.get("state"),
        title=title,
        description=description,
        url=url,
        metadata=metadata,
    )


def _map_code_scanning_alert_to_finding(
    *,
    org_id: Optional[str],
    gh_org: str,
    repo: GitHubRepoRef,
    alert: Dict[str, Any],
) -> GitHubSecurityFinding:
    """
    Turn a normalized Code Scanning alert (from ingestor._normalize_code_scanning_alert)
    into a GitHubSecurityFinding.
    """
    # Alert structure from ingestor._normalize_code_scanning_alert:
    #
    # {
    #   "id": "456",
    #   "number": 456,
    #   "severity": "medium",
    #   "state": "open",
    #   "rule_id": "js/xss",
    #   "rule_name": "Cross-site scripting",
    #   "tool": "CodeQL",
    #   "gh_url": "https://github.com/...",
    #   "raw": {...},
    # }
    rule_id = alert.get("rule_id")
    rule_name = alert.get("rule_name")
    tool = alert.get("tool")

    title_parts: List[str] = []
    if rule_name:
        title_parts.append(rule_name)
    if tool:
        title_parts.append(f"({tool})")
    if not title_parts:
        title_parts.append("Code scanning alert")

    title = " ".join(title_parts)
    description = None  # can be filled in later if we fetch more detail
    url = alert.get("gh_url")

    metadata = {
        "kind": "code_scanning",
        "rule_id": rule_id,
        "rule_name": rule_name,
        "tool": tool,
        "raw": alert.get("raw"),
    }

    return GitHubSecurityFinding(
        kind="code_scanning",
        org_id=org_id,
        gh_org=gh_org,
        repo=repo,
        id=alert.get("id"),
        number=alert.get("number"),
        severity=alert.get("severity"),
        state=alert.get("state"),
        title=title,
        description=description,
        url=url,
        metadata=metadata,
    )
