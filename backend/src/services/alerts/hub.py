"""
Alert Management Module

Centralized alert management with correlation, enrichment, and workflow automation.
Integrated from Keep patterns.

Features:
- Multi-source alert ingestion
- Alert correlation and deduplication
- Severity-based prioritization
- Automated workflow triggers
- Alert enrichment with context
- Notification routing

Source: Keep (https://github.com/keephq/keep)
"""

from __future__ import annotations

import uuid
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    WARNING = "warning"
    LOW = "low"
    INFO = "info"
    
    @property
    def priority(self) -> int:
        """Get numeric priority (higher = more severe)."""
        priorities = {
            "critical": 5,
            "high": 4,
            "warning": 3,
            "low": 2,
            "info": 1,
        }
        return priorities.get(self.value, 0)


class AlertStatus(str, Enum):
    """Alert status."""
    
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertSource(str, Enum):
    """Alert sources."""
    
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    DATADOG = "datadog"
    PAGERDUTY = "pagerduty"
    CLOUDWATCH = "cloudwatch"
    AZURE_MONITOR = "azure_monitor"
    GCP_MONITORING = "gcp_monitoring"
    SENTRY = "sentry"
    CUSTOM = "custom"
    SECOPS_SCANNER = "secops_scanner"


@dataclass
class Alert:
    """
    Represents a security or operational alert.
    
    Attributes:
        id: Unique alert identifier
        name: Alert name
        description: Detailed description
        severity: Alert severity
        status: Current status
        source: Alert source
        fingerprint: Unique fingerprint for deduplication
        labels: Alert labels/tags
        annotations: Additional annotations
        starts_at: When the alert started
        ends_at: When the alert ended (if resolved)
        generator_url: URL to the alert source
        acknowledged_by: Who acknowledged the alert
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    severity: AlertSeverity = AlertSeverity.WARNING
    status: AlertStatus = AlertStatus.FIRING
    source: AlertSource = AlertSource.CUSTOM
    fingerprint: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, Any] = field(default_factory=dict)
    starts_at: datetime = field(default_factory=datetime.now)
    ends_at: Optional[datetime] = None
    generator_url: str = ""
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    enrichments: Dict[str, Any] = field(default_factory=dict)
    related_alerts: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate fingerprint if not provided."""
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()
    
    def _generate_fingerprint(self) -> str:
        """Generate a fingerprint for deduplication."""
        import hashlib
        data = f"{self.name}|{self.source.value}|{json.dumps(self.labels, sort_keys=True)}"
        return hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get alert duration."""
        if self.ends_at:
            return self.ends_at - self.starts_at
        return datetime.now() - self.starts_at
    
    def acknowledge(self, user: str) -> None:
        """Acknowledge the alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()
    
    def resolve(self) -> None:
        """Resolve the alert."""
        self.status = AlertStatus.RESOLVED
        self.ends_at = datetime.now()
    
    def suppress(self, duration: Optional[timedelta] = None) -> None:
        """Suppress the alert."""
        self.status = AlertStatus.SUPPRESSED
        self.annotations["suppressed_until"] = (
            (datetime.now() + duration).isoformat() if duration else None
        )
    
    def enrich(self, key: str, value: Any) -> None:
        """Add enrichment data to the alert."""
        self.enrichments[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "status": self.status.value,
            "source": self.source.value,
            "fingerprint": self.fingerprint,
            "labels": self.labels,
            "annotations": self.annotations,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at.isoformat() if self.ends_at else None,
            "enrichments": self.enrichments,
            "related_alerts": self.related_alerts,
        }


@dataclass
class AlertGroup:
    """
    Group of related alerts.
    
    Attributes:
        id: Group identifier
        name: Group name
        alerts: Alerts in this group
        correlation_key: Key used for grouping
        severity: Highest severity in the group
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    alerts: List[Alert] = field(default_factory=list)
    correlation_key: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def severity(self) -> AlertSeverity:
        """Get highest severity in the group."""
        if not self.alerts:
            return AlertSeverity.INFO
        return max(self.alerts, key=lambda a: a.severity.priority).severity
    
    @property
    def count(self) -> int:
        """Get number of alerts in the group."""
        return len(self.alerts)
    
    def add_alert(self, alert: Alert) -> None:
        """Add an alert to the group."""
        self.alerts.append(alert)
        alert.related_alerts = [a.id for a in self.alerts if a.id != alert.id]


class AlertCorrelator:
    """
    Correlates related alerts into groups.
    
    Uses multiple strategies to identify related alerts:
    - Same resource
    - Time-based proximity
    - Label matching
    - Causal relationships
    """
    
    def __init__(
        self,
        time_window: timedelta = timedelta(minutes=5),
        label_keys: Optional[List[str]] = None,
    ):
        self.time_window = time_window
        self.label_keys = label_keys or ["service", "environment", "host", "namespace"]
        self.groups: Dict[str, AlertGroup] = {}
    
    def correlate(self, alert: Alert) -> Optional[AlertGroup]:
        """
        Find or create a correlation group for an alert.
        
        Args:
            alert: The alert to correlate
            
        Returns:
            The AlertGroup the alert was added to
        """
        correlation_key = self._get_correlation_key(alert)
        
        if correlation_key in self.groups:
            group = self.groups[correlation_key]
            # Check if still within time window
            if datetime.now() - group.created_at < self.time_window:
                group.add_alert(alert)
                return group
        
        # Create new group
        group = AlertGroup(
            name=f"Alert Group: {alert.name}",
            correlation_key=correlation_key,
        )
        group.add_alert(alert)
        self.groups[correlation_key] = group
        
        return group
    
    def _get_correlation_key(self, alert: Alert) -> str:
        """Generate a correlation key for an alert."""
        key_parts = [alert.name]
        
        for label_key in self.label_keys:
            if label_key in alert.labels:
                key_parts.append(f"{label_key}={alert.labels[label_key]}")
        
        return "|".join(key_parts)
    
    def get_groups(self) -> List[AlertGroup]:
        """Get all alert groups."""
        return list(self.groups.values())
    
    def get_group_by_id(self, group_id: str) -> Optional[AlertGroup]:
        """Get a specific group by ID."""
        for group in self.groups.values():
            if group.id == group_id:
                return group
        return None


class AlertEnricher:
    """
    Enriches alerts with additional context.
    
    Pulls data from various sources to add context to alerts.
    """
    
    def __init__(self):
        self.enrichment_functions: Dict[str, Callable[[Alert], Dict[str, Any]]] = {}
    
    def register(self, name: str, func: Callable[[Alert], Dict[str, Any]]) -> None:
        """Register an enrichment function."""
        self.enrichment_functions[name] = func
    
    def enrich(self, alert: Alert) -> Alert:
        """
        Enrich an alert with all registered enrichments.
        
        Args:
            alert: The alert to enrich
            
        Returns:
            The enriched alert
        """
        for name, func in self.enrichment_functions.items():
            try:
                enrichment = func(alert)
                alert.enrich(name, enrichment)
            except Exception as e:
                logger.warning(f"Enrichment '{name}' failed: {e}")
        
        return alert


class AlertWorkflow:
    """
    Automated workflow triggered by alerts.
    
    Workflows can perform actions like:
    - Send notifications
    - Create tickets
    - Execute remediation
    - Escalate to on-call
    """
    
    def __init__(
        self,
        name: str,
        conditions: List[Callable[[Alert], bool]],
        actions: List[Callable[[Alert], None]],
    ):
        self.name = name
        self.conditions = conditions
        self.actions = actions
        self.enabled = True
    
    def matches(self, alert: Alert) -> bool:
        """Check if alert matches workflow conditions."""
        if not self.enabled:
            return False
        return all(condition(alert) for condition in self.conditions)
    
    def execute(self, alert: Alert) -> None:
        """Execute workflow actions."""
        logger.info(f"Executing workflow '{self.name}' for alert: {alert.name}")
        
        for action in self.actions:
            try:
                action(alert)
            except Exception as e:
                logger.error(f"Workflow action failed: {e}")


class AlertHub(BaseModel):
    """
    Central hub for alert management.
    
    Provides:
    - Alert ingestion from multiple sources
    - Deduplication
    - Correlation
    - Enrichment
    - Workflow automation
    - Notification routing
    
    Attributes:
        name: Hub identifier
        alerts: All alerts
        workflows: Automated workflows
        correlation_enabled: Enable alert correlation
        enrichment_enabled: Enable alert enrichment
    """
    
    model_config = {"arbitrary_types_allowed": True}
    
    name: str = Field(default="default")
    correlation_enabled: bool = Field(default=True)
    enrichment_enabled: bool = Field(default=True)
    deduplication_window: int = Field(default=300)  # seconds
    
    # Callbacks
    on_alert: Optional[Callable[[Alert], None]] = Field(default=None)
    on_resolved: Optional[Callable[[Alert], None]] = Field(default=None)
    
    # Private state
    _alerts: Dict[str, Alert] = {}
    _fingerprint_cache: Dict[str, datetime] = {}
    _correlator: Optional[AlertCorrelator] = None
    _enricher: Optional[AlertEnricher] = None
    _workflows: List[AlertWorkflow] = []
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self._alerts = {}
        self._fingerprint_cache = {}
        self._correlator = AlertCorrelator() if self.correlation_enabled else None
        self._enricher = AlertEnricher() if self.enrichment_enabled else None
        self._workflows = []
    
    def ingest(self, alert: Alert) -> Alert:
        """
        Ingest a new alert.
        
        Args:
            alert: Alert to ingest
            
        Returns:
            The processed alert
        """
        # Check for duplicate
        if self._is_duplicate(alert):
            logger.debug(f"Duplicate alert ignored: {alert.fingerprint}")
            return self._alerts.get(alert.fingerprint, alert)
        
        # Enrich
        if self._enricher:
            alert = self._enricher.enrich(alert)
        
        # Correlate
        if self._correlator:
            self._correlator.correlate(alert)
        
        # Store
        self._alerts[alert.id] = alert
        self._fingerprint_cache[alert.fingerprint] = datetime.now()
        
        # Execute workflows
        for workflow in self._workflows:
            if workflow.matches(alert):
                workflow.execute(alert)
        
        # Callback
        if self.on_alert:
            self.on_alert(alert)
        
        logger.info(f"Alert ingested: {alert.name} ({alert.severity.value})")
        
        return alert
    
    def ingest_batch(self, alerts: List[Alert]) -> List[Alert]:
        """Ingest multiple alerts."""
        return [self.ingest(alert) for alert in alerts]
    
    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is a duplicate within the deduplication window."""
        if alert.fingerprint in self._fingerprint_cache:
            last_seen = self._fingerprint_cache[alert.fingerprint]
            if datetime.now() - last_seen < timedelta(seconds=self.deduplication_window):
                return True
        return False
    
    def acknowledge(self, alert_id: str, user: str) -> Optional[Alert]:
        """Acknowledge an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.acknowledge(user)
            return alert
        return None
    
    def resolve(self, alert_id: str) -> Optional[Alert]:
        """Resolve an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.resolve()
            
            if self.on_resolved:
                self.on_resolved(alert)
            
            return alert
        return None
    
    def suppress(
        self,
        alert_id: str,
        duration: Optional[timedelta] = None,
    ) -> Optional[Alert]:
        """Suppress an alert."""
        if alert_id in self._alerts:
            alert = self._alerts[alert_id]
            alert.suppress(duration)
            return alert
        return None
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        source: Optional[AlertSource] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """
        Get alerts with optional filtering.
        
        Args:
            status: Filter by status
            severity: Filter by severity
            source: Filter by source
            limit: Maximum number of alerts to return
            
        Returns:
            List of matching alerts
        """
        alerts = list(self._alerts.values())
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if source:
            alerts = [a for a in alerts if a.source == source]
        
        # Sort by severity and time
        alerts.sort(key=lambda a: (-a.severity.priority, a.starts_at), reverse=True)
        
        return alerts[:limit]
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get a specific alert by ID."""
        return self._alerts.get(alert_id)
    
    def get_groups(self) -> List[AlertGroup]:
        """Get all alert groups."""
        if self._correlator:
            return self._correlator.get_groups()
        return []
    
    def add_workflow(self, workflow: AlertWorkflow) -> None:
        """Add an automated workflow."""
        self._workflows.append(workflow)
    
    def add_enrichment(
        self,
        name: str,
        func: Callable[[Alert], Dict[str, Any]],
    ) -> None:
        """Add an enrichment function."""
        if self._enricher:
            self._enricher.register(name, func)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        alerts = list(self._alerts.values())
        
        by_severity = defaultdict(int)
        by_status = defaultdict(int)
        by_source = defaultdict(int)
        
        for alert in alerts:
            by_severity[alert.severity.value] += 1
            by_status[alert.status.value] += 1
            by_source[alert.source.value] += 1
        
        return {
            "total": len(alerts),
            "firing": by_status.get("firing", 0),
            "acknowledged": by_status.get("acknowledged", 0),
            "resolved": by_status.get("resolved", 0),
            "by_severity": dict(by_severity),
            "by_status": dict(by_status),
            "by_source": dict(by_source),
            "groups": len(self.get_groups()),
        }


# Pre-built workflows
def create_critical_alert_workflow(
    notify_func: Callable[[Alert], None],
) -> AlertWorkflow:
    """Create a workflow for critical alerts."""
    return AlertWorkflow(
        name="Critical Alert Notification",
        conditions=[
            lambda a: a.severity == AlertSeverity.CRITICAL,
            lambda a: a.status == AlertStatus.FIRING,
        ],
        actions=[notify_func],
    )


def create_security_alert_workflow(
    escalate_func: Callable[[Alert], None],
) -> AlertWorkflow:
    """Create a workflow for security alerts."""
    return AlertWorkflow(
        name="Security Alert Escalation",
        conditions=[
            lambda a: "security" in a.name.lower() or a.source == AlertSource.SECOPS_SCANNER,
            lambda a: a.severity.priority >= AlertSeverity.WARNING.priority,
        ],
        actions=[escalate_func],
    )
