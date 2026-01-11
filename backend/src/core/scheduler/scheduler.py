# backend/src/core/scheduler/scheduler.py

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.api.schemas.platform import CheckInfo
from src.core.checks.base import (
    BaseCheck,
    CheckContext,
    CheckRunResult,
    LoggerLike,
)
from src.core.checks.github_deps import GitHubDepsCheck
from src.core.checks.github_security import GitHubSecurityCheck
from src.core.checks.k8s_misconfig import K8sMisconfigCheck
from src.core.checks.ci_hardening import CIHardeningCheck
from src.core.issues.service import IssuesService
from src.integrations.service import IntegrationsService  # to be implemented
from src.utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


class _SchedulerLoggerAdapter(logging.LoggerAdapter, LoggerLike):
    """
    Adapts the standard logging.Logger to the LoggerLike protocol used by checks.

    Adds `check_id` to log records for easier correlation.
    """

    def process(self, msg, kwargs):
        check_id = self.extra.get("check_id")
        return f"[check={check_id}] {msg}", kwargs


class CheckScheduler:
    """
    Orchestrator for running checks and feeding results into IssuesService.

    Responsibilities:
    - know which checks exist and their metadata
    - list checks for an org (for the UI)
    - run checks on demand (triggered via /platform/run-health-check)
    - store last run status in memory (sufficient for MVP)

    This class is intentionally stateless w.r.t. persistent job queues;
    for production, you could plug in Celery/Redis/Cloud Tasks etc.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Instantiate services locally to avoid circular imports with api.deps
        self._issues_service = IssuesService(settings=settings)
        self._integrations_service = IntegrationsService(settings=settings)

        # Registry of all available checks
        self._checks: Dict[str, BaseCheck] = {
            "github_deps": GitHubDepsCheck(),
            "github_security": GitHubSecurityCheck(),
            "k8s_misconfig": K8sMisconfigCheck(),
            "ci_hardening": CIHardeningCheck(),
        }

        # In-memory store for last run status keyed by org_id
        self._last_runs: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API: list checks for an org
    # ------------------------------------------------------------------

    async def list_checks_for_org(self, org_id: str) -> Dict[str, Any]:
        """
        Return metadata about all checks, plus last-run status for each check
        for the given org.

        Shape is compatible with ChecksListResponse:
        {
          "org_id": str,
          "checks": List[CheckInfo],
        }
        """
        last_run = self._last_runs.get(org_id, {})
        per_check_last = last_run.get("checks", {})

        checks_info: List[CheckInfo] = []
        for check_id, check in self._checks.items():
            lr = per_check_last.get(check_id, {})

            info = CheckInfo(
                id=check_id,
                name=getattr(check, "name", check_id),
                description=getattr(check, "description", ""),
                category=getattr(check, "category", "general"),
                enabled=True,  # for now, all checks enabled if integration exists
                last_run_at=lr.get("last_run_at"),
                last_run_status=lr.get("status"),
                last_run_issues=lr.get("issues_count"),
                metadata={
                    "last_duration_ms": lr.get("duration_ms"),
                },
            )
            checks_info.append(info)

        return {
            "org_id": org_id,
            "checks": checks_info,
        }

    # ------------------------------------------------------------------
    # Public API: last run status for platform health
    # ------------------------------------------------------------------

    async def get_last_run_status(self, org_id: str) -> Dict[str, Any]:
        """
        Return last check run status for the org.

        Used to enrich PlatformHealthResponse (last_check_at, last_check_status).
        """
        last_run = self._last_runs.get(org_id)
        if not last_run:
            return {
                "last_check_at": None,
                "last_check_status": "never",
                "checks": {},
            }

        return {
            "last_check_at": last_run.get("last_run_at"),
            "last_check_status": last_run.get("status", "unknown"),
            "checks": last_run.get("checks", {}),
        }

    # ------------------------------------------------------------------
    # Public API: enqueue / run health checks
    # ------------------------------------------------------------------

    async def enqueue_run(
        self,
        org_id: str,
        checks: Optional[List[str]] = None,
        scope: Optional[str] = None,
        triggered_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Schedule (and in this MVP, synchronously execute) a health check run.

        - org_id: which organization to run checks for
        - checks: optional list of check ids; if None, run all relevant checks
        - scope: optional logical scope (security, reliability, all, etc.)
        - triggered_by: user id or system identifier

        Returns a dict compatible with RunHealthCheckResponse:
        {
          "org_id": str,
          "job_id": str | None,
          "status": "scheduled" | "failed",
          "message": str,
        }
        """
        # Determine which check ids to run
        check_ids = self._select_checks_to_run(checks=checks, scope=scope)

        if not check_ids:
            return {
                "org_id": org_id,
                "job_id": None,
                "status": "failed",
                "message": "No checks to run for the requested scope.",
            }

        # For now, run synchronously; job_id is a synthetic identifier
        job_id = f"{org_id}:{int(datetime.utcnow().timestamp())}"

        try:
            await self._run_checks_now(
                org_id=org_id,
                check_ids=check_ids,
                triggered_by=triggered_by,
                job_id=job_id,
            )
            status = "scheduled"
            message = f"Checks executed: {', '.join(check_ids)}"
        except Exception as exc:
            logger.exception("Failed to run checks for org %s", org_id)
            status = "failed"
            message = f"Failed to run checks: {type(exc).__name__}: {exc}"

        return {
            "org_id": org_id,
            "job_id": job_id,
            "status": status,
            "message": message,
        }

    # ------------------------------------------------------------------
    # Internal: which checks to run
    # ------------------------------------------------------------------

    def _select_checks_to_run(
        self,
        checks: Optional[List[str]],
        scope: Optional[str],
    ) -> List[str]:
        """
        Decide which check ids should run based on explicit list + scope.
        """
        if checks:
            # Only run known checks; ignore unknown ids silently
            return [cid for cid in checks if cid in self._checks]

        # Scope-based selection when explicit list is not provided
        scope = (scope or "all").lower()

        if scope == "security":
            return [
                cid
                for cid, c in self._checks.items()
                if getattr(c, "category", "") == "security"
            ]
        if scope == "reliability":
            return [
                cid
                for cid, c in self._checks.items()
                if getattr(c, "category", "") == "reliability"
            ]

        # Default: run everything
        return list(self._checks.keys())

    # ------------------------------------------------------------------
    # Internal: run checks synchronously (MVP)
    # ------------------------------------------------------------------

    async def _run_checks_now(
        self,
        *,
        org_id: str,
        check_ids: List[str],
        triggered_by: Optional[str],
        job_id: str,
    ) -> None:
        """
        Execute checks immediately and push results into IssuesService.

        - builds CheckContext with extras (integration availability
          and any precomputed info)
        - runs each check and aggregates results
        - upserts issues into IssuesService
        - updates in-memory last-run status
        """
        # Determine integration availability from IntegrationsService
        extras = await self._build_context_extras(org_id=org_id)

        context = CheckContext(
            org_id=org_id,
            settings=self.settings,
            extras=extras,
        )

        all_issue_dicts: List[Dict[str, Any]] = []
        per_check_results: Dict[str, Dict[str, Any]] = {}

        run_started_at = datetime.utcnow()

        for check_id in check_ids:
            check = self._checks.get(check_id)
            if not check:
                logger.warning("Unknown check id '%s' requested, skipping", check_id)
                continue

            adapter = _SchedulerLoggerAdapter(logger, {"check_id": check_id})
            adapter.info("Running check for org %s", org_id)

            started_at = datetime.utcnow()
            try:
                result: CheckRunResult = await check.run(context=context, logger=adapter)
            except Exception as exc:
                adapter.exception("Check failed with unexpected error")
                # Failed checks still contribute to last run status
                per_check_results[check_id] = {
                    "status": "failed",
                    "last_run_at": datetime.utcnow(),
                    "duration_ms": (datetime.utcnow() - started_at).total_seconds() * 1000.0,
                    "issues_count": 0,
                    "metrics": {},
                    "errors": [f"{type(exc).__name__}: {exc}"],
                }
                continue

            duration_ms = (datetime.utcnow() - started_at).total_seconds() * 1000.0

            issue_dicts = result.to_issue_dicts()
            all_issue_dicts.extend(issue_dicts)

            per_check_results[check_id] = {
                "status": "success" if not result.errors else "partial",
                "last_run_at": datetime.utcnow(),
                "duration_ms": duration_ms,
                "issues_count": len(issue_dicts),
                "metrics": result.metrics,
                "errors": result.errors,
            }

        # Upsert all collected issues into the issues store
        if all_issue_dicts:
            await self._issues_service.upsert_issues_from_check_run(
                issues_data=all_issue_dicts,
            )

        run_finished_at = datetime.utcnow()
        any_failed = any(
            cdata.get("status") in {"failed", "partial"} for cdata in per_check_results.values()
        )

        overall_status = "success"
        if any_failed:
            overall_status = "partial" if all_issue_dicts else "failed"

        self._last_runs[org_id] = {
            "job_id": job_id,
            "last_run_at": run_finished_at,
            "status": overall_status,
            "checks": per_check_results,
            "duration_ms": (run_finished_at - run_started_at).total_seconds() * 1000.0,
            "triggered_by": triggered_by,
        }

    # ------------------------------------------------------------------
    # Internal: build context extras using integrations service
    # ------------------------------------------------------------------

    async def _build_context_extras(self, org_id: str) -> Dict[str, Any]:
        """
        Ask IntegrationsService about providers so checks can cheaply know
        what is enabled / disabled and reuse any precomputed info.

        This is deliberately simple for MVP; you can later extend it to
        include lists of repos, clusters, etc.
        """
        extras: Dict[str, Any] = {}

        try:
            status = await self._integrations_service.get_status(org_id=org_id, provider="github")
            extras["github_enabled"] = bool(status.get("enabled", False))
            extras["github_repos_scanned"] = status.get("repos_count", 0)
        except Exception:
            logger.exception("Failed to get GitHub integration status for org %s", org_id)
            extras["github_enabled"] = False

        try:
            k8s_status = await self._integrations_service.get_status(org_id=org_id, provider="k8s")
            extras["k8s_enabled"] = bool(k8s_status.get("enabled", False))
        except Exception:
            logger.exception("Failed to get Kubernetes integration status for org %s", org_id)
            extras["k8s_enabled"] = False

        # You can add more providers here later (e.g. scanners, cloud, etc.)
        return extras
