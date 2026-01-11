"""
Immutable Trace - Audit-Grade Proof for Decisions

Every decision is backed by a "Reasoning Trace" (Why it happened)
and a "Verification Result" (Outcome score).
This trace is cryptographically signed (hashed) to ensure immutability.
"""

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class ReasoningTrace:
    """Captures the reasoning behind a decision."""
    decision: str  # e.g., "Blocked IP 1.2.3.4"
    reasoning: str  # "Correlated with 5 failed logins..."
    context: Dict[str, Any]  # Metadata about the state/observation
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class VerificationResult:
    """Captures the verification of an action's outcome."""
    success_score: int  # 0-100
    details: str  # "No further attempts recorded"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ImmutableTrace:
    """An immutable, signed record of a decision and its verification."""
    trace_id: str
    reasoning: ReasoningTrace
    verification: Optional[VerificationResult] = None
    signature: Optional[str] = None

    @classmethod
    def create(cls, reasoning: ReasoningTrace, verification: Optional[VerificationResult] = None) -> 'ImmutableTrace':
        """Factory method to create a new trace."""
        return cls(
            trace_id=str(uuid.uuid4()),
            reasoning=reasoning,
            verification=verification
        )

    def compute_hash(self) -> str:
        """Computes SHA-256 hash of the trace content."""
        # Serialization logic to ensure determinism (sort keys)

        def json_serial(obj):
            """JSON serializer for objects not serializable by default json code"""
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        data = {
            "trace_id": self.trace_id,
            "reasoning": asdict(self.reasoning),
            "verification": asdict(self.verification) if self.verification else None,
        }

        # Sort keys to ensure deterministic hash
        payload = json.dumps(data, sort_keys=True, default=json_serial)
        return hashlib.sha256(payload.encode()).hexdigest()

    def sign(self) -> None:
        """Finalizes the trace with a hash signature."""
        self.signature = self.compute_hash()

    def verify(self) -> bool:
        """Verifies the integrity of the trace."""
        if not self.signature:
            return False
        return self.signature == self.compute_hash()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "trace_id": self.trace_id,
            "reasoning": {
                **asdict(self.reasoning),
                "timestamp": self.reasoning.timestamp.isoformat()
            },
            "verification": {
                **asdict(self.verification),
                "timestamp": self.verification.timestamp.isoformat()
            } if self.verification else None,
            "signature": self.signature
        }
