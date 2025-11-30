# backend/src/integrations/github/client.py

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


@dataclass
class GitHubAuthConfig:
    """
    Minimal auth/configuration for talking to GitHub.

    Supports:
    - GitHub.com (default)
    - GitHub Enterprise via custom base URL
    - PATs or GitHub App tokens (as plain bearer tokens)
    """

    token: Optional[str]
    base_url: str = "https://api.github.com"
    user_agent: str = "secops-ai/1.0"

    @classmethod
    def from_settings(cls, settings: Settings) -> "GitHubAuthConfig":
        token = (
            getattr(settings, "GITHUB_TOKEN", None)
            or os.getenv("GITHUB_TOKEN")
        )
        base_url = (
            getattr(settings, "GITHUB_API_BASE_URL", None)
            or os.getenv("GITHUB_API_BASE_URL")
            or "https://api.github.com"
        )
        user_agent = (
            getattr(settings, "GITHUB_USER_AGENT", None)
            or os.getenv("GITHUB_USER_AGENT")
            or "secops-ai/1.0"
        )
        return cls(token=token, base_url=base_url, user_agent=user_agent)


class GitHubClient:
    """
    Thin async wrapper around the GitHub REST API.

    This client is intentionally minimal and composable. Higher-level
    helpers like GitHubSecurityIngestor and GitHubActionsCollector
    should be built on top of this.

    Key responsibilities:
    - Authentication & headers
    - Basic GET/POST with error handling
    - A few focused helper methods for repos, security alerts, and workflows
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.auth = GitHubAuthConfig.from_settings(settings)
        self._base_url = self.auth.base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

        if not self.auth.token:
            logger.warning(
                "GitHubClient initialized without a token. "
                "GitHub API calls will likely fail with 401/403."
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "User-Agent": self.auth.user_agent,
            }
            if self.auth.token:
                headers["Authorization"] = f"Bearer {self.auth.token}"

            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # Low-level HTTP helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        client = await self._get_client()
        try:
            resp = await client.request(method, url, params=params, json=json)
        except Exception as exc:
            logger.exception("GitHubClient: HTTP error %s %s", method, url)
            raise RuntimeError(f"GitHub request failed: {type(exc).__name__}: {exc}") from exc

        if resp.status_code >= 400:
            body_preview = resp.text[:500]
            logger.warning(
                "GitHubClient: %s %s -> %s, body: %s",
                method,
                url,
                resp.status_code,
                body_preview,
            )
        return resp

    async def _get_json(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        resp = await self._request("GET", url, params=params)
        if resp.status_code == 204:
            return None
        try:
            return resp.json()
        except ValueError:
            logger.error("GitHubClient: failed to parse JSON from %s", url)
            raise RuntimeError("GitHub response is not valid JSON")

    # ------------------------------------------------------------------
    # Public helper methods (used by ingestors/collectors)
    # ------------------------------------------------------------------

    async def list_org_repos(
        self,
        org: str,
        *,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List repositories for an organization.

        Uses simple pagination; for very large orgs you may want to
        implement a hard limit or cursors in higher-level code.
        """
        repos: List[Dict[str, Any]] = []
        page = 1

        while True:
            data = await self._get_json(
                f"/orgs/{org}/repos",
                params={"per_page": per_page, "page": page},
            )
            if not isinstance(data, list) or not data:
                break

            repos.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return repos

    # ---------------------- Security / dependabot ----------------------

    async def list_dependabot_alerts(
        self,
        org: str,
        repo: str,
        *,
        state: str = "open",
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List Dependabot alerts for a given repo.

        This is used by GitHubDepsCheck / GitHubSecurityIngestor to
        reason about outdated or vulnerable dependencies.
        """
        alerts: List[Dict[str, Any]] = []
        page = 1

        while True:
            path = f"/repos/{org}/{repo}/dependabot/alerts"
            params = {
                "state": state,
                "per_page": per_page,
                "page": page,
            }
            data = await self._get_json(path, params=params)

            if not isinstance(data, list) or not data:
                break

            alerts.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return alerts

    async def list_code_scanning_alerts(
        self,
        org: str,
        repo: str,
        *,
        state: str = "open",
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        List code scanning alerts for a given repo.

        Used by GitHubSecurityIngestor to surface code scanning results
        (e.g. CodeQL) as issues.
        """
        alerts: List[Dict[str, Any]] = []
        page = 1

        while True:
            path = f"/repos/{org}/{repo}/code-scanning/alerts"
            params = {
                "state": state,
                "per_page": per_page,
                "page": page,
            }
            data = await self._get_json(path, params=params)

            if not isinstance(data, list) or not data:
                break

            alerts.extend(data)
            if len(data) < per_page:
                break
            page += 1

        return alerts

    # ---------------------- Workflows / CI ------------------------------

    async def list_workflows(
        self,
        org: str,
        repo: str,
    ) -> List[Dict[str, Any]]:
        """
        List GitHub Actions workflows for a repo.

        Used by GitHubActionsCollector to reason about CI hardening.
        """
        data = await self._get_json(f"/repos/{org}/{repo}/actions/workflows")
        if not isinstance(data, dict):
            return []

        workflows = data.get("workflows") or []
        if not isinstance(workflows, list):
            return []
        return workflows

    async def get_workflow_file(
        self,
        org: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[str]:
        """
        Fetch the raw YAML content of a workflow file from the repo.

        This uses the GitHub Contents API and base64-decodes the content.
        """
        params: Dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        data = await self._get_json(
            f"/repos/{org}/{repo}/contents/{path}",
            params=params or None,
        )

        if not isinstance(data, dict):
            return None

        if data.get("encoding") == "base64":
            import base64

            try:
                raw = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
                return raw
            except Exception:
                logger.exception("GitHubClient: failed to decode base64 content for %s", path)
                return None

        # Sometimes GitHub returns plain content
        return data.get("content")

    # ---------------------- Generic helpers -----------------------------

    async def get_repo(
        self,
        org: str,
        repo: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch basic metadata for a single repo.
        """
        data = await self._get_json(f"/repos/{org}/{repo}")
        if not isinstance(data, dict):
            return None
        return data

    async def get_file(
        self,
        org: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generic wrapper around the contents API for arbitrary files.

        Returns the raw JSON from GitHub; caller can interpret as needed.
        """
        params: Dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        data = await self._get_json(
            f"/repos/{org}/{repo}/contents/{path}",
            params=params or None,
        )
        if not isinstance(data, dict):
            return None
        return data


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------


def get_github_client(settings: Settings) -> GitHubClient:
    """
    Singleton/factory helper if you ever want a DI-style pattern.

    For now this just creates a new client; in the future you can cache
    per-settings or add connection pooling if needed.
    """
    return GitHubClient(settings=settings)
