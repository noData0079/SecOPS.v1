# backend/src/integrations/k8s/client.py

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import anyio

from utils.config import Settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

# We avoid importing kubernetes at module-import time to allow running
# without the dependency in environments that don't need k8s.
_k8s_import_error_logged = False


def _ensure_k8s_imported():
    """
    Lazily import the Kubernetes client modules.

    This allows the rest of the backend to run even if kubernetes is not
    installed, as long as no k8s functionality is used.
    """
    global _k8s_import_error_logged

    try:
        # These imports are intentionally inside the function.
        from kubernetes import client, config  # type: ignore  # noqa: F401
    except Exception as exc:  # pragma: no cover - env-dependent
        if not _k8s_import_error_logged:
            logger.warning(
                "Kubernetes client is not available: %s. "
                "Install 'kubernetes' package to enable k8s integrations.",
                exc,
            )
            _k8s_import_error_logged = True
        raise


@dataclass
class K8sConfig:
    """
    Resolves how to connect to Kubernetes.

    Config sources (in priority order):
      1) Explicit settings:
         - settings.K8S_MODE = "incluster" | "kubeconfig"
         - settings.K8S_KUBECONFIG_PATH
      2) Environment variables:
         - K8S_MODE
         - KUBECONFIG
      3) Fallbacks:
         - if running in cluster: use in-cluster
         - else: default kubeconfig (~/.kube/config)
    """

    mode: str  # "incluster" or "kubeconfig"
    kubeconfig_path: Optional[str] = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "K8sConfig":
        mode = (
            getattr(settings, "K8S_MODE", None)
            or os.getenv("K8S_MODE")
            or "auto"
        ).lower()

        kubeconfig_path = (
            getattr(settings, "K8S_KUBECONFIG_PATH", None)
            or os.getenv("K8S_KUBECONFIG")
        )

        if mode == "incluster":
            return cls(mode="incluster", kubeconfig_path=None)

        if mode == "kubeconfig":
            return cls(mode="kubeconfig", kubeconfig_path=kubeconfig_path)

        # mode == "auto"
        # Heuristic: if we see service account files, assume incluster
        if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount/token"):
            return cls(mode="incluster", kubeconfig_path=None)

        return cls(mode="kubeconfig", kubeconfig_path=kubeconfig_path)


class K8sClient:
    """
    Async-friendly wrapper around the Kubernetes Python client.

    Responsibilities:
      - Load config (in-cluster or kubeconfig).
      - Provide a small set of helpers for:
          * listing deployments by namespace
          * listing ingresses by namespace
          * listing pods (optionally by label selector)
          * basic cluster info

    All public methods are async and use anyio.to_thread.run_sync
    to avoid blocking the event loop.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.config = K8sConfig.from_settings(settings)

        self._initialized = False
        self._apps_v1 = None
        self._networking_v1 = None
        self._core_v1 = None

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _init_sync(self) -> None:
        """
        Synchronous initialization of the underlying Kubernetes clients.
        Called lazily from async methods via to_thread.run_sync.
        """
        if self._initialized:
            return

        _ensure_k8s_imported()
        from kubernetes import client, config  # type: ignore

        try:
            if self.config.mode == "incluster":
                logger.info("K8sClient: loading in-cluster configuration")
                config.load_incluster_config()
            else:
                path = self.config.kubeconfig_path
                if path:
                    logger.info("K8sClient: loading kubeconfig from %s", path)
                    config.load_kube_config(config_file=path)
                else:
                    logger.info("K8sClient: loading default kubeconfig")
                    config.load_kube_config()
        except Exception as exc:  # pragma: no cover - env-dependent
            logger.exception("K8sClient: failed to load Kubernetes configuration")
            raise RuntimeError(f"Failed to load Kubernetes configuration: {exc}") from exc

        self._apps_v1 = client.AppsV1Api()
        self._networking_v1 = client.NetworkingV1Api()
        self._core_v1 = client.CoreV1Api()
        self._initialized = True

    async def _ensure_initialized(self) -> None:
        if not self._initialized:
            await anyio.to_thread.run_sync(self._init_sync)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_deployments(
        self,
        *,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List deployments in the given namespace (or all namespaces if None).

        Returns a list of dicts with a normalized shape:
          {
            "name": str,
            "namespace": str,
            "replicas": int,
            "ready_replicas": int,
            "available_replicas": int,
            "labels": dict,
            "containers": [
              {
                "name": str,
                "image": str,
                "resources": {
                  "requests": {...},
                  "limits": {...},
                },
              },
              ...
            ],
          }
        """
        await self._ensure_initialized()
        from kubernetes.client import ApiException  # type: ignore

        async def _list() -> List[Dict[str, Any]]:
            assert self._apps_v1 is not None
            try:
                if namespace:
                    resp = self._apps_v1.list_namespaced_deployment(
                        namespace=namespace,
                        label_selector=label_selector,
                    )
                else:
                    resp = self._apps_v1.list_deployment_for_all_namespaces(
                        label_selector=label_selector,
                    )
            except ApiException as exc:  # pragma: no cover - env-dependent
                logger.warning(
                    "K8sClient: failed to list deployments (ns=%s, selector=%s): %s",
                    namespace,
                    label_selector,
                    exc,
                )
                return []

            items = []
            for d in resp.items:
                spec = d.spec
                status = d.status or {}
                template = getattr(spec, "template", None)
                pod_spec = getattr(template, "spec", None)
                containers_info = []

                if pod_spec and getattr(pod_spec, "containers", None):
                    for c in pod_spec.containers:
                        resources = getattr(c, "resources", None) or {}
                        containers_info.append(
                            {
                                "name": c.name,
                                "image": c.image,
                                "resources": {
                                    "requests": getattr(resources, "requests", None),
                                    "limits": getattr(resources, "limits", None),
                                },
                            }
                        )

                items.append(
                    {
                        "name": d.metadata.name,
                        "namespace": d.metadata.namespace,
                        "replicas": getattr(spec, "replicas", None),
                        "ready_replicas": getattr(status, "ready_replicas", None),
                        "available_replicas": getattr(status, "available_replicas", None),
                        "labels": d.metadata.labels or {},
                        "containers": containers_info,
                    }
                )
            return items

        return await anyio.to_thread.run_sync(_list)

    async def list_ingresses(
        self,
        *,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List ingresses in the given namespace (or all namespaces).

        Returns a list of dicts with:
          {
            "name": str,
            "namespace": str,
            "hosts": [str],
            "tls": bool,
            "labels": dict,
          }
        """
        await self._ensure_initialized()
        from kubernetes.client import ApiException  # type: ignore

        async def _list() -> List[Dict[str, Any]]:
            assert self._networking_v1 is not None
            try:
                if namespace:
                    resp = self._networking_v1.list_namespaced_ingress(
                        namespace=namespace,
                        label_selector=label_selector,
                    )
                else:
                    resp = self._networking_v1.list_ingress_for_all_namespaces(
                        label_selector=label_selector,
                    )
            except ApiException as exc:  # pragma: no cover - env-dependent
                logger.warning(
                    "K8sClient: failed to list ingresses (ns=%s, selector=%s): %s",
                    namespace,
                    label_selector,
                    exc,
                )
                return []

            items = []
            for ing in resp.items:
                spec = ing.spec
                hosts: List[str] = []
                tls_enabled = False

                if spec and getattr(spec, "rules", None):
                    for rule in spec.rules:
                        if rule.host:
                            hosts.append(rule.host)

                if spec and getattr(spec, "tls", None):
                    tls_enabled = True if spec.tls else False

                items.append(
                    {
                        "name": ing.metadata.name,
                        "namespace": ing.metadata.namespace,
                        "hosts": hosts,
                        "tls": tls_enabled,
                        "labels": ing.metadata.labels or {},
                    }
                )
            return items

        return await anyio.to_thread.run_sync(_list)

    async def list_pods(
        self,
        *,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List pods in the given namespace (or all namespaces).

        Returns a list of dicts with:
          {
            "name": str,
            "namespace": str,
            "phase": str,
            "node_name": str | None,
            "labels": dict,
            "containers": [
                {
                    "name": str,
                    "image": str,
                    "ready": bool,
                    "restart_count": int,
                },
                ...
            ],
          }
        """
        await self._ensure_initialized()
        from kubernetes.client import ApiException  # type: ignore

        async def _list() -> List[Dict[str, Any]]:
            assert self._core_v1 is not None
            try:
                if namespace:
                    resp = self._core_v1.list_namespaced_pod(
                        namespace=namespace,
                        label_selector=label_selector,
                    )
                else:
                    resp = self._core_v1.list_pod_for_all_namespaces(
                        label_selector=label_selector,
                    )
            except ApiException as exc:  # pragma: no cover - env-dependent
                logger.warning(
                    "K8sClient: failed to list pods (ns=%s, selector=%s): %s",
                    namespace,
                    label_selector,
                    exc,
                )
                return []

            items = []
            for p in resp.items:
                status = p.status or {}
                spec = p.spec or {}
                container_statuses = getattr(status, "container_statuses", None) or []
                cs_map = {cs.name: cs for cs in container_statuses}

                containers_info = []
                for c in getattr(spec, "containers", None) or []:
                    cs = cs_map.get(c.name)
                    ready = getattr(cs, "ready", False) if cs else False
                    restart_count = getattr(cs, "restart_count", 0) if cs else 0

                    containers_info.append(
                        {
                            "name": c.name,
                            "image": c.image,
                            "ready": ready,
                            "restart_count": restart_count,
                        }
                    )

                items.append(
                    {
                        "name": p.metadata.name,
                        "namespace": p.metadata.namespace,
                        "phase": getattr(status, "phase", None),
                        "node_name": getattr(spec, "node_name", None),
                        "labels": p.metadata.labels or {},
                        "containers": containers_info,
                    }
                )
            return items

        return await anyio.to_thread.run_sync(_list)

    async def get_cluster_version(self) -> Optional[str]:
        """
        Return the Kubernetes cluster version (e.g. 'v1.29.2') if available.
        """
        await self._ensure_initialized()
        from kubernetes.client import ApiException, VersionApi  # type: ignore

        async def _version() -> Optional[str]:
            try:
                v = VersionApi().get_code()
            except ApiException as exc:  # pragma: no cover - env-dependent
                logger.warning("K8sClient: failed to fetch cluster version: %s", exc)
                return None
            return getattr(v, "git_version", None)

        return await anyio.to_thread.run_sync(_version)


# ----------------------------------------------------------------------
# Factory helper
# ----------------------------------------------------------------------


def get_k8s_client(settings: Settings) -> K8sClient:
    """
    Factory helper for dependency injection.

    Use this from checks / services:

        from integrations.k8s.client import get_k8s_client
        k8s = get_k8s_client(settings)
        deployments = await k8s.list_deployments(namespace="default")
    """
    return K8sClient(settings=settings)
