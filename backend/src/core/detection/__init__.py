# backend/src/core/detection/__init__.py

"""Detection layer for SecOps platform."""

from .signal_ingestion import SignalIngestionService, Signal, SignalSource
from .detection_engine import DetectionEngine, Finding, FindingSeverity
from .correlation_engine import CorrelationEngine, CorrelatedFinding

__all__ = [
    "SignalIngestionService",
    "Signal",
    "SignalSource",
    "DetectionEngine",
    "Finding",
    "FindingSeverity",
    "CorrelationEngine",
    "CorrelatedFinding",
]
