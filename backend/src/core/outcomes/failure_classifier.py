"""
Failure Classifier - Categorize failures for intelligent learning.

Not all failures are equal:
- Transient vs permanent
- Tool fault vs environmental fault
- Recoverable vs terminal
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FailureType(str, Enum):
    """Types of failures."""
    TRANSIENT = "transient"           # Retry might work
    PERMANENT = "permanent"           # Retry won't help
    PERMISSION = "permission"         # Access denied
    RESOURCE = "resource"             # Resource unavailable
    TIMEOUT = "timeout"               # Operation timed out
    VALIDATION = "validation"         # Invalid input/state
    DEPENDENCY = "dependency"         # External dependency failed
    UNKNOWN = "unknown"


class FailureSeverity(str, Enum):
    """Severity of failures."""
    LOW = "low"           # Minor, can continue
    MEDIUM = "medium"     # Needs attention
    HIGH = "high"         # Blocks progress
    CRITICAL = "critical" # System-wide impact


@dataclass
class ClassifiedFailure:
    """A classified failure with metadata."""
    failure_type: FailureType
    severity: FailureSeverity
    is_recoverable: bool
    recommended_action: str
    confidence: float
    patterns_matched: List[str]
    raw_error: str


class FailureClassifier:
    """
    Classifies failures to enable intelligent retry/escalation decisions.
    
    Uses pattern matching and heuristics (NO ML).
    """
    
    def __init__(self):
        # Pattern -> (FailureType, Severity, Recoverable, Action)
        self.patterns: List[tuple] = [
            # Transient failures
            (r"connection.*refused|ECONNREFUSED", FailureType.TRANSIENT, FailureSeverity.MEDIUM, True, "Retry after delay"),
            (r"timeout|timed out|deadline exceeded", FailureType.TIMEOUT, FailureSeverity.MEDIUM, True, "Retry with longer timeout"),
            (r"temporarily unavailable|service unavailable|503", FailureType.TRANSIENT, FailureSeverity.MEDIUM, True, "Retry with backoff"),
            (r"rate limit|too many requests|429", FailureType.TRANSIENT, FailureSeverity.LOW, True, "Wait and retry"),
            
            # Permission failures
            (r"permission denied|access denied|forbidden|403|401", FailureType.PERMISSION, FailureSeverity.HIGH, False, "Escalate for access"),
            (r"unauthorized|authentication failed", FailureType.PERMISSION, FailureSeverity.HIGH, False, "Check credentials"),
            
            # Resource failures
            (r"not found|404|does not exist", FailureType.RESOURCE, FailureSeverity.MEDIUM, False, "Verify resource exists"),
            (r"no such|cannot find", FailureType.RESOURCE, FailureSeverity.MEDIUM, False, "Check resource path"),
            (r"out of memory|OOM|memory limit", FailureType.RESOURCE, FailureSeverity.CRITICAL, False, "Scale resources"),
            (r"disk full|no space left", FailureType.RESOURCE, FailureSeverity.CRITICAL, False, "Free disk space"),
            
            # Validation failures
            (r"invalid|malformed|bad request|400", FailureType.VALIDATION, FailureSeverity.MEDIUM, False, "Fix input parameters"),
            (r"schema.*error|validation.*failed", FailureType.VALIDATION, FailureSeverity.MEDIUM, False, "Correct data format"),
            
            # Dependency failures
            (r"upstream|downstream|dependency|external service", FailureType.DEPENDENCY, FailureSeverity.HIGH, True, "Check dependencies"),
            (r"database.*error|db.*failed", FailureType.DEPENDENCY, FailureSeverity.HIGH, True, "Check database health"),
            
            # Permanent failures
            (r"fatal|unrecoverable|critical error", FailureType.PERMANENT, FailureSeverity.CRITICAL, False, "Manual intervention required"),
        ]
    
    def classify(self, error: str, context: Optional[Dict[str, Any]] = None) -> ClassifiedFailure:
        """
        Classify a failure from error message.
        
        Args:
            error: The error message or exception string
            context: Additional context (tool used, system state, etc.)
        
        Returns:
            ClassifiedFailure with type, severity, and recommendations
        """
        error_lower = error.lower()
        patterns_matched: List[str] = []
        
        best_match: Optional[tuple] = None
        best_confidence = 0.0
        
        for pattern, failure_type, severity, recoverable, action in self.patterns:
            if re.search(pattern, error_lower):
                patterns_matched.append(pattern)
                # Simple confidence: more specific patterns = higher confidence
                confidence = len(pattern) / 50  # Normalize by pattern length
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = (failure_type, severity, recoverable, action)
        
        if best_match:
            failure_type, severity, recoverable, action = best_match
        else:
            # Default classification
            failure_type = FailureType.UNKNOWN
            severity = FailureSeverity.MEDIUM
            recoverable = False
            action = "Investigate and escalate"
            best_confidence = 0.3
        
        # Adjust based on context
        if context:
            # If we've already retried, reduce recoverability
            if context.get("retry_count", 0) >= 3:
                recoverable = False
                action = "Max retries reached - escalate"
            
            # Critical systems get higher severity
            if context.get("environment") == "production":
                if severity == FailureSeverity.MEDIUM:
                    severity = FailureSeverity.HIGH
        
        result = ClassifiedFailure(
            failure_type=failure_type,
            severity=severity,
            is_recoverable=recoverable,
            recommended_action=action,
            confidence=min(1.0, best_confidence),
            patterns_matched=patterns_matched,
            raw_error=error[:500],  # Truncate long errors
        )
        
        logger.info(
            f"Classified failure: {failure_type.value} ({severity.value}), "
            f"recoverable={recoverable}"
        )
        
        return result
    
    def should_retry(self, failure: ClassifiedFailure, attempt: int = 1) -> bool:
        """Determine if a failure should be retried."""
        if not failure.is_recoverable:
            return False
        
        if attempt >= 3:
            return False
        
        if failure.failure_type in (FailureType.TRANSIENT, FailureType.TIMEOUT):
            return True
        
        if failure.failure_type == FailureType.DEPENDENCY and attempt < 2:
            return True
        
        return False
    
    def get_retry_delay(self, failure: ClassifiedFailure, attempt: int = 1) -> int:
        """Get recommended retry delay in seconds."""
        base_delays = {
            FailureType.TRANSIENT: 2,
            FailureType.TIMEOUT: 5,
            FailureType.DEPENDENCY: 10,
        }
        
        base = base_delays.get(failure.failure_type, 5)
        
        # Exponential backoff
        return base * (2 ** (attempt - 1))


# Singleton-ish instance for easy import
failure_classifier = FailureClassifier()


__all__ = [
    "FailureClassifier",
    "ClassifiedFailure",
    "FailureType",
    "FailureSeverity",
    "failure_classifier",
]
