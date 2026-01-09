# backend/src/core/detection/detection_engine.py

"""
Detection Engine - Layer 3

Runs security scanners, compliance rules, drift detection.
Outputs FINDINGS ONLY - no fixes, no reasoning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from utils.data_loader import classify_threat

logger = logging.getLogger(__name__)


class FindingSeverity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    """Categories of findings."""
    SECURITY = "security"
    COMPLIANCE = "compliance"
    RELIABILITY = "reliability"
    DRIFT = "drift"
    MISCONFIGURATION = "misconfiguration"


@dataclass
class Finding:
    """A detected issue - output of detection engine."""
    
    id: str
    detector_id: str
    title: str
    description: str
    severity: FindingSeverity
    category: FindingCategory
    resource_type: str
    resource_id: str
    evidence: Dict[str, Any]
    detected_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    org_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        detector_id: str,
        title: str,
        description: str,
        severity: FindingSeverity,
        category: FindingCategory,
        resource_type: str,
        resource_id: str,
        evidence: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> "Finding":
        """Factory to create a new finding."""
        return cls(
            id=str(uuid4()),
            detector_id=detector_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            resource_type=resource_type,
            resource_id=resource_id,
            evidence=evidence,
            detected_at=datetime.utcnow(),
            org_id=org_id,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "detector_id": self.detector_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity.value,
            "category": self.category.value,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "evidence": self.evidence,
            "detected_at": self.detected_at.isoformat(),
            "metadata": self.metadata,
            "org_id": self.org_id,
        }


class DetectionEngine:
    """
    Runs detectors and produces findings.
    
    NO FIXES, NO REASONING - findings only.
    """
    
    def __init__(self):
        self._detectors: Dict[str, Any] = {}
        self._findings: List[Finding] = []
        logger.info("DetectionEngine initialized")
    
    def register_detector(self, detector_id: str, detector) -> None:
        """Register a detector."""
        self._detectors[detector_id] = detector
        logger.info(f"Registered detector: {detector_id}")
    
    async def run_detector(
        self,
        detector_id: str,
        context: Dict[str, Any],
    ) -> List[Finding]:
        """Run a specific detector."""
        detector = self._detectors.get(detector_id)
        if not detector:
            logger.warning(f"Detector not found: {detector_id}")
            return []
        
        try:
            findings = await detector.detect(context)
            self._findings.extend(findings)
            return findings
        except Exception as e:
            logger.error(f"Detector {detector_id} failed: {e}")
            return []
    
    async def run_all_detectors(
        self, context: Dict[str, Any]
    ) -> List[Finding]:
        """Run all registered detectors."""
        all_findings = []
        for detector_id in self._detectors:
            findings = await self.run_detector(detector_id, context)
            all_findings.extend(findings)
        return all_findings
    
    async def analyze_text(
        self,
        text: str,
        resource_type: str = "log",
        resource_id: str = "unknown",
        org_id: Optional[str] = None,
    ) -> Optional[Finding]:
        """
        Quick analysis of text using keyword classification.
        
        Uses local keyword config - no external AI calls.
        """
        threat_level = classify_threat(text)
        
        if threat_level == "benign":
            return None
        
        severity = (
            FindingSeverity.CRITICAL if threat_level == "critical"
            else FindingSeverity.MEDIUM
        )
        
        finding = Finding.create(
            detector_id="keyword_detector",
            title=f"{threat_level.title()} activity detected",
            description=text[:500],
            severity=severity,
            category=FindingCategory.SECURITY,
            resource_type=resource_type,
            resource_id=resource_id,
            evidence={"raw_text": text, "classification": threat_level},
            org_id=org_id,
        )
        
        self._findings.append(finding)
        return finding
    
    def get_findings(self, limit: int = 100) -> List[Finding]:
        """Get recent findings."""
        return self._findings[-limit:]
    
    def get_findings_by_severity(
        self, severity: FindingSeverity
    ) -> List[Finding]:
        """Get findings filtered by severity."""
        return [f for f in self._findings if f.severity == severity]
    
    def clear_findings(self) -> int:
        """Clear findings buffer and return count cleared."""
        count = len(self._findings)
        self._findings.clear()
        return count
