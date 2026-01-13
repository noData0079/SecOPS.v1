"""
TSM99 Cognitive Reset Module
============================

Surgical removal of poisoned learning deltas without lobotomizing the AI.

This module provides:
1. Poisoned commit identification in Trust Ledger
2. Git-like revert of model weights (un-applying deltas)
3. Golden Snapshot recalculation to prevent cognitive ghosting

Usage:
    from core.evolution.cognitive_reset import CognitiveReset
    
    cr = CognitiveReset(ledger_path="/var/lib/tsm99/vault/ledger.db")
    cr.identify_poisoned_deltas(topic="ssh", window_days=30)
    cr.surgical_revert(delta_ids=["delta_331", "delta_332"])
    cr.recalculate_golden_snapshot()
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import math
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class LearningDelta:
    """Represents a single learning delta in the Trust Ledger."""
    delta_id: str
    decision_id: str
    affected_component: str
    before_hash: str
    after_hash: str
    delta_blob: bytes
    reason: str
    timestamp: datetime
    confidence_shift: float = 0.0
    direction_vector: Optional[np.ndarray] = None


@dataclass
class PoisonAnalysis:
    """Result of poison analysis on a delta cluster."""
    is_poisoned: bool
    confidence: float
    poisoned_deltas: List[str]
    trend_direction: str
    cumulative_shift: float
    recommendation: str


@dataclass
class CognitiveSnapshot:
    """Immutable snapshot of AI cognitive state."""
    snapshot_id: str
    created_at: datetime
    model_hash: str
    policy_hash: str
    adapter_weights: bytes
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrustScoreCalculator:
    """
    Calculates Autonomy Trust Score using weighted temporal decay.
    
    Formula: Tₐ = (Σ(Sᵢ × e^(-λtᵢ))) / (Σ(e^(-λtᵢ))) × (1 - D)
    
    Where:
        Sᵢ = Success score of action i
        e^(-λtᵢ) = Temporal decay (recent matters more)
        D = Drift Factor from Shadow Mirror
    """
    
    def __init__(self, decay_lambda: float = 0.1):
        self.decay_lambda = decay_lambda
    
    def calculate(
        self,
        success_scores: List[Tuple[float, datetime]],  # (score, timestamp)
        drift_factor: float,
        reference_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate Autonomy Trust Score.
        
        Args:
            success_scores: List of (score, timestamp) tuples
            drift_factor: D from Shadow Mirror (0.0 to 1.0)
            reference_time: Reference point for decay calculation
            
        Returns:
            Trust score Tₐ (0.0 to 1.0)
        """
        if not success_scores:
            return 0.0
        
        reference_time = reference_time or datetime.utcnow()
        
        weighted_sum = 0.0
        weight_total = 0.0
        
        for score, timestamp in success_scores:
            # Time difference in days
            time_diff = (reference_time - timestamp).total_seconds() / 86400.0
            
            # Temporal decay weight
            weight = math.exp(-self.decay_lambda * time_diff)
            
            weighted_sum += score * weight
            weight_total += weight
        
        if weight_total == 0:
            return 0.0
        
        # Apply drift factor
        trust_score = (weighted_sum / weight_total) * (1 - drift_factor)
        
        return max(0.0, min(1.0, trust_score))


class LogicClusterAnalyzer:
    """
    Analyzes learning deltas for strategic poisoning patterns.
    
    Instead of comparing delta_331 vs delta_332, looks for trends
    across delta clusters (e.g., 100 deltas all moving toward "allow SSH from Russia").
    """
    
    def __init__(self, threshold: float = 0.3, window_days: int = 30):
        self.threshold = threshold
        self.window_days = window_days
    
    def analyze_cluster(
        self,
        deltas: List[LearningDelta],
        topic: str
    ) -> PoisonAnalysis:
        """
        Analyze a cluster of deltas for strategic poisoning.
        
        Args:
            deltas: List of learning deltas to analyze
            topic: Topic/domain being analyzed (e.g., "ssh", "auth")
            
        Returns:
            PoisonAnalysis with detection results
        """
        if not deltas:
            return PoisonAnalysis(
                is_poisoned=False,
                confidence=0.0,
                poisoned_deltas=[],
                trend_direction="none",
                cumulative_shift=0.0,
                recommendation="No deltas to analyze"
            )
        
        # Filter by topic
        topic_deltas = [d for d in deltas if topic.lower() in d.affected_component.lower()]
        
        # Calculate cumulative confidence shift
        cumulative_shift = sum(d.confidence_shift for d in topic_deltas)
        
        # Detect consistent direction (all moving same way)
        positive_count = sum(1 for d in topic_deltas if d.confidence_shift > 0)
        negative_count = sum(1 for d in topic_deltas if d.confidence_shift < 0)
        total = len(topic_deltas)
        
        if total == 0:
            return PoisonAnalysis(
                is_poisoned=False,
                confidence=0.0,
                poisoned_deltas=[],
                trend_direction="none",
                cumulative_shift=0.0,
                recommendation="No topic deltas found"
            )
        
        # Calculate direction consistency
        if positive_count / total > 0.8:
            trend_direction = "allow"
            consistency = positive_count / total
        elif negative_count / total > 0.8:
            trend_direction = "deny"
            consistency = negative_count / total
        else:
            trend_direction = "mixed"
            consistency = max(positive_count, negative_count) / total
        
        # Strategic poisoning detection
        is_poisoned = (
            len(topic_deltas) >= 10 and  # Multiple small deltas
            consistency > 0.8 and         # Consistent direction
            abs(cumulative_shift) > self.threshold  # Significant cumulative effect
        )
        
        poisoned_deltas = [d.delta_id for d in topic_deltas] if is_poisoned else []
        
        if is_poisoned:
            recommendation = (
                f"🚨 STRATEGIC POISONING DETECTED: {len(topic_deltas)} deltas "
                f"moving toward '{trend_direction}'. Recommend surgical revert."
            )
        else:
            recommendation = "No strategic poisoning pattern detected."
        
        return PoisonAnalysis(
            is_poisoned=is_poisoned,
            confidence=consistency,
            poisoned_deltas=poisoned_deltas,
            trend_direction=trend_direction,
            cumulative_shift=cumulative_shift,
            recommendation=recommendation
        )


class CognitiveReset:
    """
    Main class for surgical cognitive reset operations.
    
    Provides git-like operations for AI learning:
    - identify_poisoned_deltas(): Find the poison
    - surgical_revert(): Un-apply specific deltas
    - recalculate_golden_snapshot(): Ensure cognitive integrity
    """
    
    def __init__(
        self,
        ledger_path: str = "/var/lib/tsm99/vault/ledger.db",
        models_path: str = "/var/lib/tsm99/models",
        snapshots_path: str = "/var/lib/tsm99/snapshots"
    ):
        self.ledger_path = Path(ledger_path)
        self.models_path = Path(models_path)
        self.snapshots_path = Path(snapshots_path)
        
        self.cluster_analyzer = LogicClusterAnalyzer()
        self.trust_calculator = TrustScoreCalculator()
        
        # Ensure paths exist
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get SQLite connection to Trust Ledger."""
        return sqlite3.connect(str(self.ledger_path))
    
    def load_deltas(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        topic: Optional[str] = None
    ) -> List[LearningDelta]:
        """
        Load learning deltas from Trust Ledger.
        
        Args:
            since: Start timestamp
            until: End timestamp
            topic: Filter by affected component
            
        Returns:
            List of LearningDelta objects
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM learning_delta WHERE 1=1"
        params: List[Any] = []
        
        if since:
            query += " AND timestamp >= ?"
            params.append(since.isoformat())
        if until:
            query += " AND timestamp <= ?"
            params.append(until.isoformat())
        if topic:
            query += " AND affected_component LIKE ?"
            params.append(f"%{topic}%")
        
        query += " ORDER BY timestamp ASC"
        
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Failed to load deltas: {e}")
            return []
        finally:
            conn.close()
        
        deltas = []
        for row in rows:
            try:
                delta = LearningDelta(
                    delta_id=row[0],
                    decision_id=row[1],
                    affected_component=row[2],
                    before_hash=row[3],
                    after_hash=row[4],
                    delta_blob=row[5] if isinstance(row[5], bytes) else b"",
                    reason=row[6],
                    timestamp=datetime.fromisoformat(row[7]) if row[7] else datetime.utcnow(),
                    confidence_shift=self._extract_confidence_shift(row[6])
                )
                deltas.append(delta)
            except (IndexError, ValueError) as e:
                logger.warning(f"Skipping malformed delta row: {e}")
        
        return deltas
    
    def _extract_confidence_shift(self, reason: str) -> float:
        """Extract confidence shift from reason string."""
        # Parse reason for confidence changes
        # Format: "reward +0.4" or "penalty -0.2"
        try:
            if "+" in reason:
                return float(reason.split("+")[1].split()[0])
            elif "-" in reason:
                return -float(reason.split("-")[1].split()[0])
        except (IndexError, ValueError):
            pass
        return 0.0
    
    def identify_poisoned_deltas(
        self,
        topic: str,
        window_days: int = 30
    ) -> PoisonAnalysis:
        """
        Identify potentially poisoned deltas using cluster analysis.
        
        Args:
            topic: Domain to analyze (e.g., "ssh", "auth", "network")
            window_days: Analysis window in days
            
        Returns:
            PoisonAnalysis with detection results
        """
        since = datetime.utcnow() - timedelta(days=window_days)
        deltas = self.load_deltas(since=since, topic=topic)
        
        logger.info(f"Analyzing {len(deltas)} deltas for topic '{topic}' over {window_days} days")
        
        return self.cluster_analyzer.analyze_cluster(deltas, topic)
    
    def surgical_revert(
        self,
        delta_ids: List[str],
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """
        Surgically revert specific deltas (un-apply learning).
        
        This is git revert for AI weights - it creates inverse deltas
        rather than deleting history.
        
        Args:
            delta_ids: List of delta IDs to revert
            create_backup: Whether to create a snapshot before revert
            
        Returns:
            Dict with revert results
        """
        results = {
            "reverted": [],
            "failed": [],
            "backup_snapshot_id": None,
            "success": False
        }
        
        if not delta_ids:
            results["success"] = True
            return results
        
        # Create backup snapshot
        if create_backup:
            snapshot = self._create_snapshot("pre_revert")
            results["backup_snapshot_id"] = snapshot.snapshot_id
            logger.info(f"Created backup snapshot: {snapshot.snapshot_id}")
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        for delta_id in delta_ids:
            try:
                # Load the original delta
                cursor.execute(
                    "SELECT * FROM learning_delta WHERE delta_id = ?",
                    (delta_id,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.warning(f"Delta not found: {delta_id}")
                    results["failed"].append(delta_id)
                    continue
                
                # Create inverse delta
                inverse_delta_id = f"revert_{delta_id}"
                inverse_reason = f"Revert of {delta_id}: suspected poisoning"
                
                # Swap before/after hashes (the inverse operation)
                cursor.execute("""
                    INSERT INTO learning_delta 
                    (delta_id, decision_id, affected_component, before_hash, 
                     after_hash, delta_blob, reason, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    inverse_delta_id,
                    f"revert_{row[1]}",  # decision_id
                    row[2],               # affected_component
                    row[4],               # swap: after becomes before
                    row[3],               # swap: before becomes after
                    self._invert_delta_blob(row[5]),  # Inverted weights
                    inverse_reason,
                    datetime.utcnow().isoformat()
                ))
                
                results["reverted"].append(delta_id)
                logger.info(f"Reverted delta: {delta_id}")
                
            except sqlite3.Error as e:
                logger.error(f"Failed to revert {delta_id}: {e}")
                results["failed"].append(delta_id)
        
        conn.commit()
        conn.close()
        
        results["success"] = len(results["failed"]) == 0
        
        return results
    
    def _invert_delta_blob(self, delta_blob: bytes) -> bytes:
        """
        Invert a weight delta (negate the gradient).
        
        For adapter weights (LoRA), this means negating the delta tensor.
        """
        if not delta_blob:
            return b""
        
        try:
            # Deserialize, negate, reserialize
            delta_array = np.frombuffer(delta_blob, dtype=np.float32)
            inverted = -delta_array
            return inverted.tobytes()
        except Exception as e:
            logger.warning(f"Could not invert delta blob: {e}")
            return delta_blob
    
    def _create_snapshot(self, prefix: str) -> CognitiveSnapshot:
        """Create a cognitive state snapshot."""
        snapshot_id = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Create snapshot metadata
        snapshot = CognitiveSnapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.utcnow(),
            model_hash=self._get_current_model_hash(),
            policy_hash=self._get_current_policy_hash(),
            adapter_weights=self._get_current_adapter_weights(),
            metadata={"type": prefix}
        )
        
        # Save to disk
        snapshot_file = self.snapshots_path / f"{snapshot_id}.json"
        with open(snapshot_file, "w") as f:
            json.dump({
                "snapshot_id": snapshot.snapshot_id,
                "created_at": snapshot.created_at.isoformat(),
                "model_hash": snapshot.model_hash,
                "policy_hash": snapshot.policy_hash,
                "metadata": snapshot.metadata
            }, f, indent=2)
        
        # Save weights separately
        weights_file = self.snapshots_path / f"{snapshot_id}.weights"
        weights_file.write_bytes(snapshot.adapter_weights)
        
        return snapshot
    
    def _get_current_model_hash(self) -> str:
        """Get hash of current model state."""
        model_file = self.models_path / "current_adapter.bin"
        if model_file.exists():
            return hashlib.sha256(model_file.read_bytes()).hexdigest()[:16]
        return "no_adapter"
    
    def _get_current_policy_hash(self) -> str:
        """Get hash of current policy state."""
        policy_file = self.models_path / "policy.yaml"
        if policy_file.exists():
            return hashlib.sha256(policy_file.read_bytes()).hexdigest()[:16]
        return "default_policy"
    
    def _get_current_adapter_weights(self) -> bytes:
        """Get current adapter weights."""
        adapter_file = self.models_path / "current_adapter.bin"
        if adapter_file.exists():
            return adapter_file.read_bytes()
        return b""
    
    def recalculate_golden_snapshot(self) -> CognitiveSnapshot:
        """
        Recalculate and save a new Golden Snapshot.
        
        This should be called after surgical revert to ensure
        no "cognitive ghosting" remains.
        
        Returns:
            New Golden Snapshot
        """
        logger.info("Recalculating Golden Snapshot...")
        
        # Create new golden snapshot
        snapshot = self._create_snapshot("golden")
        
        # Update ledger to mark this as the new baseline
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO snapshots (snapshot_id, snapshot_type, created_at, state_hash, metadata)
                VALUES (?, 'golden', ?, ?, ?)
            """, (
                snapshot.snapshot_id,
                snapshot.created_at.isoformat(),
                snapshot.model_hash,
                json.dumps(snapshot.metadata)
            ))
            conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to record golden snapshot: {e}")
        finally:
            conn.close()
        
        logger.info(f"New Golden Snapshot created: {snapshot.snapshot_id}")
        
        return snapshot
    
    def full_cognitive_reset(
        self,
        topic: str,
        window_days: int = 30,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Perform full cognitive reset workflow.
        
        1. Identify poisoned deltas
        2. Surgical revert
        3. Recalculate golden snapshot
        
        Args:
            topic: Domain to analyze and reset
            window_days: Analysis window
            auto_approve: Skip confirmation (for automated systems)
            
        Returns:
            Complete reset results
        """
        results = {
            "phase": "identifying",
            "analysis": None,
            "revert_results": None,
            "new_golden_snapshot": None,
            "success": False
        }
        
        # Phase 1: Identify
        logger.info(f"Phase 1: Identifying poisoned deltas for topic '{topic}'")
        analysis = self.identify_poisoned_deltas(topic, window_days)
        results["analysis"] = {
            "is_poisoned": analysis.is_poisoned,
            "confidence": analysis.confidence,
            "poisoned_count": len(analysis.poisoned_deltas),
            "trend_direction": analysis.trend_direction,
            "cumulative_shift": analysis.cumulative_shift,
            "recommendation": analysis.recommendation
        }
        
        if not analysis.is_poisoned:
            results["phase"] = "complete"
            results["success"] = True
            logger.info("No poisoning detected. Cognitive state is clean.")
            return results
        
        # Phase 2: Surgical Revert
        if not auto_approve:
            logger.warning(
                f"Poisoning detected! {len(analysis.poisoned_deltas)} deltas identified. "
                f"Set auto_approve=True to proceed with revert."
            )
            results["phase"] = "awaiting_approval"
            return results
        
        logger.info(f"Phase 2: Reverting {len(analysis.poisoned_deltas)} poisoned deltas")
        results["phase"] = "reverting"
        revert_results = self.surgical_revert(analysis.poisoned_deltas)
        results["revert_results"] = revert_results
        
        if not revert_results["success"]:
            results["phase"] = "revert_failed"
            return results
        
        # Phase 3: Recalculate Golden Snapshot
        logger.info("Phase 3: Recalculating Golden Snapshot")
        results["phase"] = "recalculating"
        new_snapshot = self.recalculate_golden_snapshot()
        results["new_golden_snapshot"] = new_snapshot.snapshot_id
        
        results["phase"] = "complete"
        results["success"] = True
        
        logger.info(f"Cognitive Reset complete. New baseline: {new_snapshot.snapshot_id}")
        
        return results


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TSM99 Cognitive Reset Tool")
    parser.add_argument("--topic", required=True, help="Topic to analyze (e.g., ssh, auth)")
    parser.add_argument("--window", type=int, default=30, help="Analysis window in days")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve revert")
    parser.add_argument("--ledger", default="/var/lib/tsm99/vault/ledger.db", help="Ledger path")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    cr = CognitiveReset(ledger_path=args.ledger)
    results = cr.full_cognitive_reset(
        topic=args.topic,
        window_days=args.window,
        auto_approve=args.auto_approve
    )
    
    print(json.dumps(results, indent=2, default=str))
