"""
System Monitoring and Metrics

Unified monitoring for the SecOps platform:
- LLM usage and cost tracking
- Learning system metrics
- Security scanning metrics
- Alert management metrics
- System health monitoring
"""

from __future__ import annotations

import uuid
import logging
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""
    
    COUNTER = "counter"       # Incrementing value
    GAUGE = "gauge"           # Point-in-time value
    HISTOGRAM = "histogram"   # Distribution
    TIMER = "timer"          # Duration tracking


@dataclass
class Metric:
    """A single metric data point."""
    
    name: str
    value: float
    metric_type: MetricType = MetricType.GAUGE
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "labels": self.labels,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HealthCheck:
    """Health check result for a component."""
    
    component: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: float = 0
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    
    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "message": self.message,
            "last_check": self.last_check.isoformat(),
        }


class MetricsCollector:
    """Collects and aggregates metrics."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._labels: Dict[str, Dict[str, str]] = {}
    
    def inc(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter."""
        key = self._make_key(name, labels)
        self._counters[key] += value
        if labels:
            self._labels[key] = labels
    
    def set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self._gauges[key] = value
        if labels:
            self._labels[key] = labels
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a histogram value."""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)
        if labels:
            self._labels[key] = labels
    
    def time(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record a timing."""
        key = self._make_key(name, labels)
        self._timers[key].append(duration_ms)
        if labels:
            self._labels[key] = labels
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for a metric with labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_all(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {k: {"count": len(v), "sum": sum(v), "avg": sum(v)/len(v) if v else 0} for k, v in self._histograms.items()},
            "timers": {k: {"count": len(v), "avg_ms": sum(v)/len(v) if v else 0, "max_ms": max(v) if v else 0} for k, v in self._timers.items()},
        }


class SystemMonitor(BaseModel):
    """
    System monitoring for the SecOps platform.
    
    Provides unified monitoring for:
    - LLM usage and costs
    - Learning system effectiveness
    - Security scanning metrics
    - Alert management stats
    - Overall system health
    
    Attributes:
        name: Monitor identifier
        health_check_interval: Seconds between health checks
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = Field(default="system_monitor")
    health_check_interval: int = Field(default=60)
    
    on_health_change: Optional[Callable[[str, str, str], None]] = Field(default=None)
    on_alert: Optional[Callable[[str, str], None]] = Field(default=None)
    
    _collector: MetricsCollector = None
    _health_checks: Dict[str, HealthCheck] = {}
    _component_status: Dict[str, str] = {}
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._collector = MetricsCollector(self.name)
        self._health_checks = {}
        self._component_status = {}
    
    # =========================================
    # LLM METRICS
    # =========================================
    
    def record_llm_request(
        self,
        provider: str,
        model: str,
        tokens: int,
        cost: float,
        latency_ms: float,
        success: bool,
    ) -> None:
        """Record an LLM request."""
        labels = {"provider": provider, "model": model}
        
        self._collector.inc("llm_requests_total", 1, labels)
        self._collector.inc("llm_tokens_total", tokens, labels)
        self._collector.inc("llm_cost_total", cost, labels)
        self._collector.time("llm_request_latency", latency_ms, labels)
        
        if not success:
            self._collector.inc("llm_errors_total", 1, labels)
    
    def record_llm_savings(self, saved_calls: int, saved_cost: float) -> None:
        """Record LLM calls saved by playbooks."""
        self._collector.inc("llm_calls_saved_total", saved_calls)
        self._collector.inc("llm_cost_saved_total", saved_cost)
    
    # =========================================
    # LEARNING METRICS
    # =========================================
    
    def record_playbook_usage(
        self,
        playbook_id: str,
        finding_type: str,
        success: bool,
    ) -> None:
        """Record playbook usage."""
        labels = {"playbook_id": playbook_id, "finding_type": finding_type}
        
        self._collector.inc("playbook_uses_total", 1, labels)
        if success:
            self._collector.inc("playbook_success_total", 1, labels)
        else:
            self._collector.inc("playbook_failures_total", 1, labels)
    
    def record_learning_event(
        self,
        event_type: str,
        finding_type: str,
    ) -> None:
        """Record a learning event."""
        labels = {"event_type": event_type, "finding_type": finding_type}
        self._collector.inc("learning_events_total", 1, labels)
    
    def set_system_maturity(self, level: str, score: float) -> None:
        """Set the system maturity level."""
        self._collector.set("system_maturity_score", score)
        self._collector.set("system_maturity_level", {"FOUNDATION": 1, "LEARNING": 2, "OPTIMIZED": 3, "AUTONOMOUS": 4}.get(level, 0))
    
    # =========================================
    # SECURITY METRICS
    # =========================================
    
    def record_scan(
        self,
        scan_type: str,
        findings_count: int,
        duration_ms: float,
    ) -> None:
        """Record a security scan."""
        labels = {"scan_type": scan_type}
        
        self._collector.inc("scans_total", 1, labels)
        self._collector.inc("findings_total", findings_count, labels)
        self._collector.time("scan_duration", duration_ms, labels)
    
    def record_fix(
        self,
        finding_type: str,
        fix_source: str,
        success: bool,
        time_to_fix_seconds: float,
    ) -> None:
        """Record a fix attempt."""
        labels = {"finding_type": finding_type, "fix_source": fix_source}
        
        self._collector.inc("fixes_total", 1, labels)
        if success:
            self._collector.inc("fixes_success_total", 1, labels)
        self._collector.observe("fix_time_seconds", time_to_fix_seconds, labels)
    
    # =========================================
    # ALERT METRICS
    # =========================================
    
    def record_alert(
        self,
        severity: str,
        source: str,
        resolved: bool = False,
    ) -> None:
        """Record an alert."""
        labels = {"severity": severity, "source": source}
        
        self._collector.inc("alerts_total", 1, labels)
        if resolved:
            self._collector.inc("alerts_resolved_total", 1, labels)
    
    def set_open_alerts(self, count: int, severity: str = "all") -> None:
        """Set the count of open alerts."""
        self._collector.set("open_alerts", count, {"severity": severity})
    
    # =========================================
    # HEALTH CHECKS
    # =========================================
    
    def register_health_check(
        self,
        component: str,
        check_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        """Register a component for health checking."""
        self._health_checks[component] = HealthCheck(
            component=component,
            status="unknown",
        )
    
    def update_health(
        self,
        component: str,
        status: str,
        latency_ms: float = 0,
        message: str = "",
    ) -> None:
        """Update health status for a component."""
        old_status = self._component_status.get(component, "unknown")
        self._component_status[component] = status
        
        self._health_checks[component] = HealthCheck(
            component=component,
            status=status,
            latency_ms=latency_ms,
            message=message,
        )
        
        if old_status != status and self.on_health_change:
            self.on_health_change(component, old_status, status)
        
        # Record metric
        self._collector.set(
            "component_health",
            1 if status == "healthy" else 0,
            {"component": component}
        )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary."""
        checks = list(self._health_checks.values())
        
        healthy = sum(1 for c in checks if c.status == "healthy")
        degraded = sum(1 for c in checks if c.status == "degraded")
        unhealthy = sum(1 for c in checks if c.status == "unhealthy")
        
        overall = "healthy"
        if unhealthy > 0:
            overall = "unhealthy"
        elif degraded > 0:
            overall = "degraded"
        
        return {
            "overall": overall,
            "components": {
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
                "total": len(checks),
            },
            "checks": [c.to_dict() for c in checks],
        }
    
    # =========================================
    # DASHBOARD DATA
    # =========================================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        metrics = self._collector.get_all()
        health = self.get_health_summary()
        
        return {
            "generated_at": datetime.now().isoformat(),
            "health": health,
            "metrics": {
                "llm": {
                    "total_requests": metrics["counters"].get("llm_requests_total", 0),
                    "total_tokens": metrics["counters"].get("llm_tokens_total", 0),
                    "total_cost": metrics["counters"].get("llm_cost_total", 0),
                    "calls_saved": metrics["counters"].get("llm_calls_saved_total", 0),
                    "cost_saved": metrics["counters"].get("llm_cost_saved_total", 0),
                },
                "learning": {
                    "playbook_uses": metrics["counters"].get("playbook_uses_total", 0),
                    "learning_events": metrics["counters"].get("learning_events_total", 0),
                    "maturity_score": metrics["gauges"].get("system_maturity_score", 0),
                },
                "security": {
                    "total_scans": metrics["counters"].get("scans_total", 0),
                    "total_findings": metrics["counters"].get("findings_total", 0),
                    "total_fixes": metrics["counters"].get("fixes_total", 0),
                },
                "alerts": {
                    "total_alerts": metrics["counters"].get("alerts_total", 0),
                    "resolved_alerts": metrics["counters"].get("alerts_resolved_total", 0),
                    "open_alerts": metrics["gauges"].get("open_alerts", 0),
                },
            },
        }
    
    def export_metrics(self, format: str = "json") -> str:
        """Export all metrics."""
        data = self.get_dashboard_data()
        
        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "prometheus":
            lines = []
            for name, value in self._collector._counters.items():
                lines.append(f"secops_{name} {value}")
            for name, value in self._collector._gauges.items():
                lines.append(f"secops_{name} {value}")
            return "\n".join(lines)
        
        raise ValueError(f"Unknown format: {format}")


# Create global monitor instance
_global_monitor: Optional[SystemMonitor] = None

def get_monitor() -> SystemMonitor:
    """Get or create the global system monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = SystemMonitor()
    return _global_monitor


def record_llm_request(**kwargs) -> None:
    """Convenience function to record LLM request."""
    get_monitor().record_llm_request(**kwargs)


def record_fix(**kwargs) -> None:
    """Convenience function to record fix."""
    get_monitor().record_fix(**kwargs)


def get_dashboard() -> Dict[str, Any]:
    """Get dashboard data."""
    return get_monitor().get_dashboard_data()
