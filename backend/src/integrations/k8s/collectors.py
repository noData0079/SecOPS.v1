# backend/src/integrations/k8s/collectors.py

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from utils.config import Settings  # type: ignore[attr-defined]
from integrations.k8s.client import K8sClient, get_k8s_client

logger = logging.getLogger(__name__)


@dataclass
class K8sClusterSnapshot:
    """
    High-level view of a Kubernetes cluster (or namespace subset).

    This is what checks like K8sMisconfigCheck can consume.

    Fields:
      - version: cluster version string (if available)
      - deployments: normalized deployments list
      - ingresses: normalized ingresses list
      - pods: normalized pods list
      - metrics: precomputed metrics useful for checks / dashboards
    """

    version: Optional[str]
    deployments: List[Dict[str, Any]] = field(default_factory=list)
    ingresses: List[Dict[str, Any]] = field(default_factory=list)
    pods: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class K8sClusterCollector:
    """
    Orchestrates collection of basic cluster resources for analysis.

    Thin wrapper around K8sClient with:
      - one-shot 'collect_snapshot' API
      - derived metrics that K8sMisconfigCheck can use directly
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: K8sClient = get_k8s_client(settings)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def collect_snapshot(
        self,
        *,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
    ) -> K8sClusterSnapshot:
        """
        Collect deployments, ingresses, pods & cluster version.

        Optional:
          - namespace: if provided, only resources from that namespace
          - label_selector: restricts deployments/ingresses/pods by label
        """
        version: Optional[str] = None
        deployments: List[Dict[str, Any]] = []
        ingresses: List[Dict[str, Any]] = []
        pods: List[Dict[str, Any]] = []

        # Version
        try:
            version = await self.client.get_cluster_version()
        except Exception as exc:
            logger.exception("K8sClusterCollector: failed to fetch cluster version: %s", exc)

        # Deployments
        try:
            deployments = await self.client.list_deployments(
                namespace=namespace,
                label_selector=label_selector,
            )
        except Exception as exc:
            logger.exception("K8sClusterCollector: failed to list deployments: %s", exc)
            deployments = []

        # Ingresses
        try:
            ingresses = await self.client.list_ingresses(
                namespace=namespace,
                label_selector=label_selector,
            )
        except Exception as exc:
            logger.exception("K8sClusterCollector: failed to list ingresses: %s", exc)
            ingresses = []

        # Pods
        try:
            pods = await self.client.list_pods(
                namespace=namespace,
                label_selector=label_selector,
            )
        except Exception as exc:
            logger.exception("K8sClusterCollector: failed to list pods: %s", exc)
            pods = []

        metrics = self._compute_metrics(
            deployments=deployments,
            ingresses=ingresses,
            pods=pods,
        )

        return K8sClusterSnapshot(
            version=version,
            deployments=deployments,
            ingresses=ingresses,
            pods=pods,
            metrics=metrics,
        )

    # ------------------------------------------------------------------
    # Metrics / analysis helpers
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        *,
        deployments: List[Dict[str, Any]],
        ingresses: List[Dict[str, Any]],
        pods: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Precompute some useful metrics for misconfiguration checks.

        Metrics include:
          - total_deployments
          - deployments_without_limits
          - total_ingresses
          - ingresses_without_tls
          - total_pods
          - pods_not_running
        """
        total_deployments = len(deployments)
        total_ingresses = len(ingresses)
        total_pods = len(pods)

        deployments_without_limits = 0
        for d in deployments:
            containers = d.get("containers") or []
            if not containers:
                continue

            has_limits = False
            for c in containers:
                resources = c.get("resources") or {}
                limits = resources.get("limits") or {}
                if limits:
                    has_limits = True
                    break

            if not has_limits:
                deployments_without_limits += 1

        ingresses_without_tls = sum(
            1 for ing in ingresses if not ing.get("tls")
        )

        pods_not_running = sum(
            1
            for p in pods
            if (p.get("phase") or "").upper() not in {"RUNNING", "SUCCEEDED"}
        )

        return {
            "total_deployments": total_deployments,
            "deployments_without_limits": deployments_without_limits,
            "total_ingresses": total_ingresses,
            "ingresses_without_tls": ingresses_without_tls,
            "total_pods": total_pods,
            "pods_not_running": pods_not_running,
        }


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------


def get_k8s_cluster_collector(settings: Settings) -> K8sClusterCollector:
    """
    Factory helper for dependency injection.

    Typical usage inside a check:

        from integrations.k8s.collectors import get_k8s_cluster_collector
        from utils.config import settings

        collector = get_k8s_cluster_collector(settings)
        snapshot = await collector.collect_snapshot()

        # then use snapshot.deployments / snapshot.ingresses / snapshot.metrics
    """
    return K8sClusterCollector(settings=settings)
