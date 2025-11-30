# backend/src/core/checks/k8s_misconfig.py

from __future__ import annotations

from typing import Any, Dict, List, Optional

from api.schemas.issues import (
    IssueSeverity,
    IssueStatus,
    IssueLocation,
)
from integrations.k8s.collectors import KubernetesCollectors  # to be implemented
from .base import (
    BaseCheck,
    CheckContext,
    CheckRunResult,
    LoggerLike,
)


class K8sMisconfigCheck(BaseCheck):
    """
    Kubernetes misconfiguration & hygiene check.

    Focus areas:
    - missing CPU/memory limits on workloads
    - privileged or overly permissive securityContext
    - public ingresses without TLS

    Uses KubernetesCollectors to fetch deployments, pods, and ingresses
    for the org's clusters.
    """

    id = "k8s_misconfig"
    name = "Kubernetes Misconfigurations"
    description = "Detects basic Kubernetes misconfigurations and unsafe defaults."
    category = "reliability"

    def __init__(self) -> None:
        super().__init__(default_severity=IssueSeverity.medium)
        self._collectors: Optional[KubernetesCollectors] = None

    def _get_collectors(self, settings: Any) -> KubernetesCollectors:
        if self._collectors is None:
            self._collectors = KubernetesCollectors(settings=settings)
        return self._collectors

    async def run(
        self,
        context: CheckContext,
        logger: LoggerLike,
    ) -> CheckRunResult:
        """
        Run the Kubernetes misconfiguration check.

        Steps:
        - Check if Kubernetes integration is enabled for this org
        - Fetch basic workload + ingress metadata from KubernetesCollectors
        - Generate issues for common misconfigs
        """
        org_id = context.org_id
        settings = context.settings

        issues = []
        errors: List[str] = []
        metrics: Dict[str, Any] = {
            "org_id": org_id,
            "clusters_scanned": 0,
            "deployments_scanned": 0,
            "ingresses_scanned": 0,
            "issues_by_type": {},
        }

        k8s_enabled = context.get_extra("k8s_enabled", True)
        if not k8s_enabled:
            logger.info(
                "K8sMisconfigCheck skipped: Kubernetes integration disabled for org %s",
                org_id,
            )
            metrics["skipped"] = True
            metrics["reason"] = "k8s_integration_disabled"
            return CheckRunResult(issues=[], metrics=metrics, errors=[])

        collectors = self._get_collectors(settings)

        try:
            # Expected structure from KubernetesCollectors (we will implement it to match):
            #
            # clusters = await collectors.list_clusters(org_id)
            # deployments = await collectors.list_deployments(org_id)
            # ingresses = await collectors.list_ingresses(org_id)
            #
            # Each deployment example:
            # {
            #   "cluster": "cluster-1",
            #   "namespace": "default",
            #   "name": "api",
            #   "containers": [
            #       {
            #         "name": "api",
            #         "requests": {"cpu": "100m", "memory": "128Mi"} | {},
            #         "limits": {"cpu": "500m", "memory": "512Mi"} | {},
            #         "security_context": {
            #             "privileged": bool | None,
            #             "run_as_root": bool | None,
            #             "allow_priv_escalation": bool | None,
            #         },
            #       },
            #   ],
            # }
            #
            # Each ingress example:
            # {
            #   "cluster": "cluster-1",
            #   "namespace": "default",
            #   "name": "web-ingress",
            #   "hosts": ["app.example.com"],
            #   "tls": bool,
            #   "annotations": {...},
            # }
            clusters = await collectors.list_clusters(org_id=org_id)
            deployments = await collectors.list_deployments(org_id=org_id)
            ingresses = await collectors.list_ingresses(org_id=org_id)
        except Exception as exc:
            logger.exception("K8sMisconfigCheck failed to fetch Kubernetes resources")
            errors.append(f"collectors_error: {type(exc).__name__}: {exc}")
            metrics["failed"] = True
            return CheckRunResult(issues=[], metrics=metrics, errors=errors)

        metrics["clusters_scanned"] = len(clusters)
        metrics["deployments_scanned"] = len(deployments)
        metrics["ingresses_scanned"] = len(ingresses)

        # Analyze deployments for resource limit & security context issues
        for dep in deployments:
            try:
                new_issues = self._analyze_deployment(org_id, dep)
                for issue in new_issues:
                    issues.append(issue)
                    key = issue.category or "deployment"
                    metrics["issues_by_type"][key] = metrics["issues_by_type"].get(key, 0) + 1
            except Exception as exc:
                logger.exception(
                    "Failed to analyze deployment for misconfig: %s",
                    dep.get("name"),
                )
                errors.append(f"deployment_analysis_error: {type(exc).__name__}: {exc}")

        # Analyze ingresses for TLS / public exposure issues
        for ing in ingresses:
            try:
                new_issues = self._analyze_ingress(org_id, ing)
                for issue in new_issues:
                    issues.append(issue)
                    key = issue.category or "ingress"
                    metrics["issues_by_type"][key] = metrics["issues_by_type"].get(key, 0) + 1
            except Exception as exc:
                logger.exception(
                    "Failed to analyze ingress for misconfig: %s",
                    ing.get("name"),
                )
                errors.append(f"ingress_analysis_error: {type(exc).__name__}: {exc}")

        return CheckRunResult(
            issues=issues,
            metrics=metrics,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers – deployments
    # ------------------------------------------------------------------

    def _analyze_deployment(
        self,
        org_id: str,
        dep: Dict[str, Any],
    ):
        """
        Build issues for a single deployment's misconfigurations.
        """
        issues = []

        cluster = dep.get("cluster", "unknown-cluster")
        namespace = dep.get("namespace", "default")
        name = dep.get("name", "unknown-deployment")
        containers = dep.get("containers") or []

        # Missing resource limits
        for c in containers:
            if not self._has_limits(c):
                issues.append(
                    self._build_missing_limits_issue(
                        org_id=org_id,
                        cluster=cluster,
                        namespace=namespace,
                        deployment=name,
                        container=c,
                    )
                )

        # Dangerous security context
        for c in containers:
            sc = c.get("security_context") or {}
            if self._is_dangerous_security_context(sc):
                issues.append(
                    self._build_security_context_issue(
                        org_id=org_id,
                        cluster=cluster,
                        namespace=namespace,
                        deployment=name,
                        container=c,
                        security_context=sc,
                    )
                )

        return issues

    def _has_limits(self, container: Dict[str, Any]) -> bool:
        limits = container.get("limits") or {}
        # We only care that limits exist for cpu & memory; values are not deeply validated here.
        return bool(limits.get("cpu") and limits.get("memory"))

    def _is_dangerous_security_context(self, sc: Dict[str, Any]) -> bool:
        privileged = sc.get("privileged")
        run_as_root = sc.get("run_as_root")
        allow_priv_escalation = sc.get("allow_priv_escalation")
        return bool(
            privileged is True
            or run_as_root is True
            or allow_priv_escalation is True
        )

    def _build_missing_limits_issue(
        self,
        *,
        org_id: str,
        cluster: str,
        namespace: str,
        deployment: str,
        container: Dict[str, Any],
    ):
        container_name = container.get("name", "unknown-container")

        title = (
            f"[{cluster}/{namespace}] {deployment}/{container_name} "
            "has no CPU/memory limits"
        )

        location = IssueLocation(
            kind="k8s",
            repo=None,
            file_path=None,
            line=None,
            cluster=cluster,
            namespace=namespace,
            resource_kind="Deployment",
            resource_name=deployment,
            environment="prod",
            metadata={
                "container": container_name,
            },
        )

        short_description = (
            f"Container {container_name} in deployment {deployment} has no "
            "resource limits configured."
        )

        description = (
            "This container is running without CPU/memory limits. Without limits, "
            "a single runaway container can starve other workloads or cause "
            "node instability."
        )

        impact = (
            "Nodes may become unstable or unresponsive under load if containers "
            "are allowed to consume unbounded resources."
        )

        proposed_fix = (
            "Set appropriate CPU and memory limits/requests for this container. "
            "Start with conservative values based on current usage and adjust "
            "using metrics and load tests."
        )

        issue_id = (
            f"{org_id}:{cluster}:{namespace}:{deployment}:{container_name}:missing_limits"
        )

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.medium,
            status=IssueStatus.open,
            service=f"{cluster}:{namespace}",
            category="k8s_resource_limits",
            tags=[
                "k8s",
                "resource_limits",
                "reliability",
            ],
            location=location,
            source="k8s",
            short_description=short_description,
            description=description,
            root_cause="Resource limits were not defined for this container.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Monitor resource usage after applying limits to avoid "
                "starving the workload; adjust limits iteratively."
            ),
            references=[
                "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
            ],
            extra={
                "cluster": cluster,
                "namespace": namespace,
                "deployment": deployment,
                "container": container_name,
            },
        )

    def _build_security_context_issue(
        self,
        *,
        org_id: str,
        cluster: str,
        namespace: str,
        deployment: str,
        container: Dict[str, Any],
        security_context: Dict[str, Any],
    ):
        container_name = container.get("name", "unknown-container")

        title = (
            f"[{cluster}/{namespace}] {deployment}/{container_name} "
            "has dangerous securityContext"
        )

        location = IssueLocation(
            kind="k8s",
            repo=None,
            file_path=None,
            line=None,
            cluster=cluster,
            namespace=namespace,
            resource_kind="Deployment",
            resource_name=deployment,
            environment="prod",
            metadata={
                "container": container_name,
            },
        )

        short_description = (
            f"Container {container_name} in deployment {deployment} "
            "is running with overly permissive securityContext."
        )

        description = (
            "This container is using a securityContext that may allow it to run "
            "privileged, as root, or with privilege escalation. This increases "
            "the blast radius of a compromise."
        )

        impact = (
            "If this container is compromised, an attacker may be able to break "
            "out of the container or gain elevated privileges on the node."
        )

        proposed_fix = (
            "Tighten the securityContext for this container. Avoid running "
            "privileged or as root, disable privilege escalation, and apply "
            "pod security standards appropriate for your environment."
        )

        issue_id = (
            f"{org_id}:{cluster}:{namespace}:{deployment}:{container_name}:dangerous_sc"
        )

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.high,
            status=IssueStatus.open,
            service=f"{cluster}:{namespace}",
            category="k8s_security_context",
            tags=[
                "k8s",
                "security",
                "security_context",
            ],
            location=location,
            source="k8s",
            short_description=short_description,
            description=description,
            root_cause="Container configured with privileged / root / privilege escalation in securityContext.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Ensure applications can run correctly under restricted "
                "security policies before enforcing them in production."
            ),
            references=[
                "https://kubernetes.io/docs/concepts/security/pod-security-standards/",
            ],
            extra={
                "cluster": cluster,
                "namespace": namespace,
                "deployment": deployment,
                "container": container_name,
                "security_context": security_context,
            },
        )

    # ------------------------------------------------------------------
    # Internal helpers – ingresses
    # ------------------------------------------------------------------

    def _analyze_ingress(
        self,
        org_id: str,
        ing: Dict[str, Any],
    ):
        """
        Build issues for a single ingress's misconfigurations.
        """
        issues = []

        cluster = ing.get("cluster", "unknown-cluster")
        namespace = ing.get("namespace", "default")
        name = ing.get("name", "unknown-ingress")
        hosts = ing.get("hosts") or []
        tls_enabled = bool(ing.get("tls"))
        annotations = ing.get("annotations") or {}

        # Public ingress without TLS
        if hosts and not tls_enabled:
            issues.append(
                self._build_ingress_tls_issue(
                    org_id=org_id,
                    cluster=cluster,
                    namespace=namespace,
                    name=name,
                    hosts=hosts,
                    annotations=annotations,
                )
            )

        return issues

    def _build_ingress_tls_issue(
        self,
        *,
        org_id: str,
        cluster: str,
        namespace: str,
        name: str,
        hosts: List[str],
        annotations: Dict[str, Any],
    ):
        title = f"[{cluster}/{namespace}] Ingress {name} exposes HTTP without TLS"

        location = IssueLocation(
            kind="k8s",
            repo=None,
            file_path=None,
            line=None,
            cluster=cluster,
            namespace=namespace,
            resource_kind="Ingress",
            resource_name=name,
            environment="prod",
            metadata={
                "hosts": hosts,
            },
        )

        hosts_str = ", ".join(hosts)

        short_description = (
            f"Ingress {name} in namespace {namespace} accepts plain HTTP "
            f"traffic for hosts: {hosts_str}."
        )

        description = (
            "This ingress is configured without TLS termination. Traffic to this "
            "endpoint may be unencrypted, exposing sensitive data in transit and "
            "making it easier to perform man-in-the-middle attacks."
        )

        impact = (
            "Clients connecting over HTTP may send secrets (cookies, tokens, "
            "credentials) in clear text, which can be intercepted by attackers "
            "on the network path."
        )

        proposed_fix = (
            "Configure TLS for this ingress by adding a tls section with a valid "
            "certificate, and ensure clients use HTTPS. Consider using cert-manager "
            "to automate certificate provisioning and renewal."
        )

        issue_id = f"{org_id}:{cluster}:{namespace}:{name}:ingress_no_tls"

        return self.build_issue(
            id=issue_id,
            org_id=org_id,
            title=title,
            severity=IssueSeverity.high,
            status=IssueStatus.open,
            service=f"{cluster}:{namespace}",
            category="k8s_ingress_tls",
            tags=[
                "k8s",
                "ingress",
                "tls",
                "security",
            ],
            location=location,
            source="k8s",
            short_description=short_description,
            description=description,
            root_cause="Ingress defined without TLS termination.",
            impact=impact,
            proposed_fix=proposed_fix,
            precautions=(
                "Ensure certificates are valid and trusted; plan a controlled "
                "migration from HTTP to HTTPS to avoid breaking clients."
            ),
            references=[
                "https://kubernetes.io/docs/concepts/services-networking/ingress/",
            ],
            extra={
                "cluster": cluster,
                "namespace": namespace,
                "ingress": name,
                "hosts": hosts,
                "annotations": annotations,
            },
        )
