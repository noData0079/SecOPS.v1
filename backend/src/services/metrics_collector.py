# backend/src/services/metrics_collector.py

from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from typing import Dict, Iterator, Optional

from utils.config import Settings, settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
    )

    _PROM_AVAILABLE = True
except Exception:  # pragma: no cover - only when prometheus_client missing
    _PROM_AVAILABLE = False


class MetricsCollector:
    """
    Thin wrapper around Prometheus metrics with safe fallbacks.

    Usage:

        from services.metrics_collector import metrics

        metrics.inc_request("rag_query", status="200")
        with metrics.measure_latency("rag_query"):
            ... do work ...

        metrics.observe_rag_tokens("rag_answer", input_tokens=512, output_tokens=128)

    If prometheus_client is not installed OR METRICS_ENABLED is false,
    all methods become no-ops and will never raise.
    """

    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg
        self.enabled: bool = self._is_enabled(cfg)

        if not (_PROM_AVAILABLE and self.enabled):
            self.registry = None
            logger.info("MetricsCollector: metrics disabled or prometheus_client missing")
            return

        namespace = (
            getattr(cfg, "METRICS_NAMESPACE", None)
            or os.getenv("METRICS_NAMESPACE")
            or "secops_ai"
        )

        self.registry = CollectorRegistry(auto_describe=True)

        # General HTTP / API metrics
        self.request_counter = Counter(
            "http_requests_total",
            "Total HTTP/API requests",
            ["endpoint", "method", "status"],
            namespace=namespace,
            registry=self.registry,
        )
        self.request_latency = Histogram(
            "http_request_latency_seconds",
            "HTTP/API request latency in seconds",
            ["endpoint", "method"],
            namespace=namespace,
            registry=self.registry,
        )

        # RAG / LLM metrics
        self.rag_queries_total = Counter(
            "rag_queries_total",
            "Total RAG queries",
            ["route", "status"],
            namespace=namespace,
            registry=self.registry,
        )
        self.rag_latency = Histogram(
            "rag_query_latency_seconds",
            "RAG pipeline latency in seconds",
            ["route"],
            namespace=namespace,
            registry=self.registry,
        )
        self.rag_tokens = Histogram(
            "rag_tokens_total",
            "Input/output tokens used per RAG query",
            ["route", "direction"],  # input | output
            namespace=namespace,
            registry=self.registry,
        )

        # Check / scheduler metrics
        self.check_runs_total = Counter(
            "check_runs_total",
            "Number of check runs executed",
            ["kind", "status"],
            namespace=namespace,
            registry=self.registry,
        )
        self.check_run_latency = Histogram(
            "check_run_latency_seconds",
            "Duration of check runs in seconds",
            ["kind"],
            namespace=namespace,
            registry=self.registry,
        )
        self.open_issues_gauge = Gauge(
            "issues_open_total",
            "Number of open issues per org",
            ["org_id", "severity"],
            namespace=namespace,
            registry=self.registry,
        )

        logger.info("MetricsCollector initialized (namespace=%s)", namespace)

    @staticmethod
    def _is_enabled(cfg: Settings) -> bool:
        """Determine if metrics should be enabled."""
        env_val = os.getenv("METRICS_ENABLED")
        if env_val is not None:
            return env_val.lower() in {"1", "true", "yes", "on"}

        return bool(getattr(cfg, "METRICS_ENABLED", True))

    # ------------------------------------------------------------------ #
    # HTTP / API metrics
    # ------------------------------------------------------------------ #

    def inc_request(self, endpoint: str, method: str = "GET", status: str = "200") -> None:
        if not (self.enabled and self.registry):
            return
        try:
            self.request_counter.labels(endpoint=endpoint, method=method, status=status).inc()
        except Exception:
            logger.exception("MetricsCollector.inc_request failed")

    @contextmanager
    def measure_request_latency(self, endpoint: str, method: str = "GET") -> Iterator[None]:
        """
        Context manager to measure HTTP/API latency.

        Example:

            with metrics.measure_request_latency("/api/rag/query", "POST"):
                ... handle request ...
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            if not (self.enabled and self.registry):
                return
            try:
                elapsed = time.perf_counter() - start
                self.request_latency.labels(endpoint=endpoint, method=method).observe(elapsed)
            except Exception:
                logger.exception("MetricsCollector.measure_request_latency failed")

    # ------------------------------------------------------------------ #
    # RAG / LLM metrics
    # ------------------------------------------------------------------ #

    def inc_rag_query(self, route: str, status: str = "ok") -> None:
        if not (self.enabled and self.registry):
            return
        try:
            self.rag_queries_total.labels(route=route, status=status).inc()
        except Exception:
            logger.exception("MetricsCollector.inc_rag_query failed")

    @contextmanager
    def measure_rag_latency(self, route: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            if not (self.enabled and self.registry):
                return
            try:
                elapsed = time.perf_counter() - start
                self.rag_latency.labels(route=route).observe(elapsed)
            except Exception:
                logger.exception("MetricsCollector.measure_rag_latency failed")

    def observe_rag_tokens(
        self,
        route: str,
        *,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> None:
        if not (self.enabled and self.registry):
            return
        try:
            if input_tokens is not None:
                self.rag_tokens.labels(route=route, direction="input").observe(
                    float(input_tokens)
                )
            if output_tokens is not None:
                self.rag_tokens.labels(route=route, direction="output").observe(
                    float(output_tokens)
                )
        except Exception:
            logger.exception("MetricsCollector.observe_rag_tokens failed")

    # ------------------------------------------------------------------ #
    # Checks / scheduler metrics
    # ------------------------------------------------------------------ #

    def inc_check_run(self, kind: str, status: str = "success") -> None:
        if not (self.enabled and self.registry):
            return
        try:
            self.check_runs_total.labels(kind=kind, status=status).inc()
        except Exception:
            logger.exception("MetricsCollector.inc_check_run failed")

    @contextmanager
    def measure_check_run(self, kind: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            if not (self.enabled and self.registry):
                return
            try:
                elapsed = time.perf_counter() - start
                self.check_run_latency.labels(kind=kind).observe(elapsed)
            except Exception:
                logger.exception("MetricsCollector.measure_check_run failed")

    def set_open_issues(
        self,
        org_id: str,
        severity_counts: Dict[str, int],
    ) -> None:
        """
        Update gauge of open issues per org and severity.

        Example:

            metrics.set_open_issues("org-123", {"low": 5, "high": 2})
        """
        if not (self.enabled and self.registry):
            return
        try:
            for severity, count in severity_counts.items():
                self.open_issues_gauge.labels(
                    org_id=str(org_id),
                    severity=severity,
                ).set(float(count))
        except Exception:
            logger.exception("MetricsCollector.set_open_issues failed")

    # ------------------------------------------------------------------ #
    # Export
    # ------------------------------------------------------------------ #

    def export_prometheus(self) -> bytes:
        """
        Return Prometheus exposition format for /metrics endpoint.

        If metrics are disabled, returns an empty byte string.
        """
        if not (self.enabled and self.registry and _PROM_AVAILABLE):
            return b""
        try:
            return generate_latest(self.registry)
        except Exception:
            logger.exception("MetricsCollector.export_prometheus failed")
            return b""


# Global singleton used throughout the app
metrics = MetricsCollector(settings)  # type: ignore[arg-type]
