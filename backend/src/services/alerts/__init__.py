"""
Alert Services Module

Centralized alert management with correlation and automation.
"""

from .hub import (
    AlertHub,
    Alert,
    AlertGroup,
    AlertSeverity,
    AlertStatus,
    AlertSource,
    AlertCorrelator,
    AlertEnricher,
    AlertWorkflow,
    create_critical_alert_workflow,
    create_security_alert_workflow,
)

__all__ = [
    "AlertHub",
    "Alert",
    "AlertGroup",
    "AlertSeverity",
    "AlertStatus",
    "AlertSource",
    "AlertCorrelator",
    "AlertEnricher",
    "AlertWorkflow",
    "create_critical_alert_workflow",
    "create_security_alert_workflow",
]

__version__ = "1.0.0"
