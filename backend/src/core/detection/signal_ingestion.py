# backend/src/core/detection/signal_ingestion.py

"""
Signal Ingestion Service - Layer 2

Collects events from all sources with NO reasoning, NO filtering, NO AI.
Pure event collection and normalization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class SignalSource(str, Enum):
    """Sources of signals."""
    GIT_REPOSITORY = "git_repository"
    CI_CD_PIPELINE = "ci_cd_pipeline"
    CLOUD_CONFIG = "cloud_config"
    RUNTIME_LOGS = "runtime_logs"
    RUNTIME_METRICS = "runtime_metrics"
    SECURITY_SCANNER = "security_scanner"
    COMPLIANCE_INPUT = "compliance_input"
    EXTERNAL_ALERT = "external_alert"


@dataclass
class Signal:
    """Normalized signal from any source."""
    
    id: str
    source: SignalSource
    source_id: str  # Original ID from source system
    timestamp: datetime
    event_type: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    org_id: Optional[str] = None
    
    @classmethod
    def create(
        cls,
        source: SignalSource,
        source_id: str,
        event_type: str,
        payload: Dict[str, Any],
        org_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Signal":
        """Factory method to create a new signal."""
        return cls(
            id=str(uuid4()),
            source=source,
            source_id=source_id,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            payload=payload,
            metadata=metadata or {},
            org_id=org_id,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "source": self.source.value,
            "source_id": self.source_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "payload": self.payload,
            "metadata": self.metadata,
            "org_id": self.org_id,
        }


class SignalIngestionService:
    """
    Collects and normalizes signals from all sources.
    
    This is the GROUND TRUTH layer - no AI, no reasoning, just events.
    """
    
    def __init__(self):
        self._buffer: List[Signal] = []
        self._handlers: Dict[SignalSource, List] = {}
        logger.info("SignalIngestionService initialized")
    
    async def ingest(self, signal: Signal) -> str:
        """
        Ingest a signal into the system.
        
        Returns: Signal ID
        """
        self._buffer.append(signal)
        logger.debug(f"Ingested signal {signal.id} from {signal.source.value}")
        
        # Notify registered handlers
        for handler in self._handlers.get(signal.source, []):
            try:
                await handler(signal)
            except Exception as e:
                logger.error(f"Handler error for signal {signal.id}: {e}")
        
        return signal.id
    
    async def ingest_batch(self, signals: List[Signal]) -> List[str]:
        """Ingest multiple signals."""
        ids = []
        for signal in signals:
            signal_id = await self.ingest(signal)
            ids.append(signal_id)
        return ids
    
    async def ingest_raw(
        self,
        source: SignalSource,
        source_id: str,
        event_type: str,
        payload: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> str:
        """Convenience method to ingest from raw data."""
        signal = Signal.create(
            source=source,
            source_id=source_id,
            event_type=event_type,
            payload=payload,
            org_id=org_id,
        )
        return await self.ingest(signal)
    
    def register_handler(self, source: SignalSource, handler) -> None:
        """Register a handler for a signal source."""
        if source not in self._handlers:
            self._handlers[source] = []
        self._handlers[source].append(handler)
    
    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self._buffer)
    
    async def flush_buffer(self) -> List[Signal]:
        """Flush and return buffered signals."""
        signals = self._buffer.copy()
        self._buffer.clear()
        return signals
    
    async def get_signals_by_source(
        self, source: SignalSource, limit: int = 100
    ) -> List[Signal]:
        """Get recent signals from a specific source."""
        return [s for s in self._buffer if s.source == source][:limit]
