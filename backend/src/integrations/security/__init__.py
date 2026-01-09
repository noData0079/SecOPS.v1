"""
Security Integrations Module

Multi-cloud security scanning and compliance checking integrated from Prowler patterns.
"""

from .scanner import (
    SecurityScanner,
    Finding,
    ScanReport,
    CloudProvider,
    Severity,
    FindingStatus,
    ComplianceFramework,
    quick_scan,
)

__all__ = [
    "SecurityScanner",
    "Finding",
    "ScanReport",
    "CloudProvider",
    "Severity",
    "FindingStatus",
    "ComplianceFramework",
    "quick_scan",
]

__version__ = "1.0.0"
