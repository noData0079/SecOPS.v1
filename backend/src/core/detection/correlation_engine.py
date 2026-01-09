# backend/src/core/detection/correlation_engine.py

"""
Correlation & Noise Reduction Engine - Layer 4

Correlates findings, suppresses duplicates, identifies patterns.
This is where real risk ≠ noise.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .detection_engine import Finding, FindingSeverity

logger = logging.getLogger(__name__)


@dataclass
class CorrelatedFinding:
    """A correlated finding with related context."""
    
    id: str
    primary_finding: Finding
    related_findings: List[Finding]
    correlation_score: float  # 0.0 to 1.0
    pattern: Optional[str]
    risk_multiplier: float  # Combined risk level
    deduplicated: bool
    suppressed: bool
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def effective_severity(self) -> FindingSeverity:
        """Calculate effective severity based on correlation."""
        base_severity = self.primary_finding.severity
        
        if self.risk_multiplier >= 2.0:
            if base_severity == FindingSeverity.MEDIUM:
                return FindingSeverity.HIGH
            elif base_severity == FindingSeverity.HIGH:
                return FindingSeverity.CRITICAL
        
        return base_severity
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "primary_finding": self.primary_finding.to_dict(),
            "related_findings": [f.to_dict() for f in self.related_findings],
            "correlation_score": self.correlation_score,
            "pattern": self.pattern,
            "risk_multiplier": self.risk_multiplier,
            "effective_severity": self.effective_severity.value,
            "deduplicated": self.deduplicated,
            "suppressed": self.suppressed,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class CorrelationEngine:
    """
    Correlates multiple findings into real risk signals.
    
    - Deduplication
    - Signal correlation  
    - Noise suppression
    - Pattern detection
    """
    
    def __init__(
        self,
        dedup_window_minutes: int = 60,
        min_correlation_score: float = 0.5,
    ):
        self._dedup_window = timedelta(minutes=dedup_window_minutes)
        self._min_correlation = min_correlation_score
        self._seen_findings: Dict[str, datetime] = {}
        self._patterns: Dict[str, List[Finding]] = {}
        self._suppression_rules: List[Dict[str, Any]] = []
        logger.info("CorrelationEngine initialized")
    
    def _generate_dedup_key(self, finding: Finding) -> str:
        """Generate deduplication key for a finding."""
        return f"{finding.detector_id}:{finding.resource_id}:{finding.title}"
    
    def _is_duplicate(self, finding: Finding) -> bool:
        """Check if finding is a duplicate within the window."""
        key = self._generate_dedup_key(finding)
        
        if key in self._seen_findings:
            last_seen = self._seen_findings[key]
            if datetime.utcnow() - last_seen < self._dedup_window:
                return True
        
        self._seen_findings[key] = datetime.utcnow()
        return False
    
    def _should_suppress(self, finding: Finding) -> bool:
        """Check if finding should be suppressed."""
        for rule in self._suppression_rules:
            if rule.get("detector_id") == finding.detector_id:
                return True
            if rule.get("resource_pattern"):
                if rule["resource_pattern"] in finding.resource_id:
                    return True
        return False
    
    def _find_related(
        self,
        finding: Finding,
        all_findings: List[Finding],
    ) -> List[Finding]:
        """Find findings related to the given finding."""
        related = []
        
        for other in all_findings:
            if other.id == finding.id:
                continue
            
            # Same resource
            if other.resource_id == finding.resource_id:
                related.append(other)
                continue
            
            # Same detector with temporal proximity
            if other.detector_id == finding.detector_id:
                time_diff = abs(
                    (finding.detected_at - other.detected_at).total_seconds()
                )
                if time_diff < 300:  # 5 minutes
                    related.append(other)
        
        return related
    
    def _calculate_correlation_score(
        self,
        primary: Finding,
        related: List[Finding],
    ) -> float:
        """Calculate correlation score based on relationships."""
        if not related:
            return 0.0
        
        score = 0.0
        
        for r in related:
            # Same resource = high correlation
            if r.resource_id == primary.resource_id:
                score += 0.4
            
            # Same detector = medium correlation
            if r.detector_id == primary.detector_id:
                score += 0.2
            
            # Same severity = low correlation boost
            if r.severity == primary.severity:
                score += 0.1
        
        return min(score, 1.0)
    
    def _detect_pattern(
        self,
        finding: Finding,
        related: List[Finding],
    ) -> Optional[str]:
        """Detect patterns in related findings."""
        if len(related) >= 3:
            detectors = {f.detector_id for f in related}
            if len(detectors) == 1:
                return f"repeated_{finding.detector_id}"
            return "multi_detector_cluster"
        
        if len(related) >= 2:
            resources = {f.resource_id for f in related}
            if len(resources) == 1:
                return "resource_hotspot"
        
        return None
    
    def add_suppression_rule(self, rule: Dict[str, Any]) -> None:
        """Add a suppression rule."""
        self._suppression_rules.append(rule)
        logger.info(f"Added suppression rule: {rule}")
    
    async def correlate(
        self,
        findings: List[Finding],
    ) -> List[CorrelatedFinding]:
        """
        Process findings through correlation engine.
        
        Returns correlated findings with deduplication and noise reduction.
        """
        results = []
        
        for finding in findings:
            is_dup = self._is_duplicate(finding)
            suppressed = self._should_suppress(finding)
            
            related = self._find_related(finding, findings)
            score = self._calculate_correlation_score(finding, related)
            pattern = self._detect_pattern(finding, related)
            
            # Calculate risk multiplier
            risk_mult = 1.0
            if len(related) > 0:
                risk_mult += len(related) * 0.25
            if pattern:
                risk_mult += 0.5
            
            correlated = CorrelatedFinding(
                id=str(uuid4()),
                primary_finding=finding,
                related_findings=related,
                correlation_score=score,
                pattern=pattern,
                risk_multiplier=risk_mult,
                deduplicated=is_dup,
                suppressed=suppressed,
                created_at=datetime.utcnow(),
            )
            
            results.append(correlated)
        
        # Filter out suppressed and duplicates for final output
        active_findings = [
            cf for cf in results
            if not cf.suppressed and not cf.deduplicated
        ]
        
        logger.info(
            f"Correlated {len(findings)} findings -> "
            f"{len(active_findings)} active, "
            f"{len(results) - len(active_findings)} filtered"
        )
        
        return active_findings
    
    async def correlate_single(
        self,
        finding: Finding,
        context_findings: Optional[List[Finding]] = None,
    ) -> CorrelatedFinding:
        """Correlate a single finding."""
        context = context_findings or []
        results = await self.correlate([finding] + context)
        
        for r in results:
            if r.primary_finding.id == finding.id:
                return r
        
        # Fallback if not in results (was filtered)
        return CorrelatedFinding(
            id=str(uuid4()),
            primary_finding=finding,
            related_findings=[],
            correlation_score=0.0,
            pattern=None,
            risk_multiplier=1.0,
            deduplicated=True,
            suppressed=False,
            created_at=datetime.utcnow(),
        )
