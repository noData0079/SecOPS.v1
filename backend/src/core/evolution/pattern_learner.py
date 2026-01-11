"""
Pattern Learner - Neuro-symbolic rule induction.
"""
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CodePattern:
    name: str
    description: str
    frequency: int
    confidence: float

class PatternLearner:
    """
    Analyzes codebases and execution history to learn patterns and rules.
    """

    def __init__(self):
        self.known_patterns: List[CodePattern] = []

    def learn_patterns(self, codebase_path: str) -> List[CodePattern]:
        """
        Scans the codebase to identify recurring patterns.

        Args:
            codebase_path: Path to the directory to scan.

        Returns:
            A list of identified patterns.
        """
        # TODO: Implement static analysis / ML based pattern recognition
        return self.known_patterns

    def detect_anomalies(self, code_snippet: str) -> List[Dict[str, Any]]:
        """
        Detects deviations from learned patterns in a snippet.
        """
        # TODO: Implement anomaly detection
        return []

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from backend.src.core.memory.policy_memory import PolicyMemory, PolicyRecord

logger = logging.getLogger(__name__)

@dataclass
class LogEntry:
    source: str
    metric: str
    value: float
    timestamp: datetime
    context: Dict[str, Any]

class PatternLearner:
    """
    Learns patterns from observations and converts them into PolicyMemory rules.
    Example: "Every time Database A peaks, Web Server B fails 2 minutes later."
    -> Rule: IF db.io_wait > 0.8 THEN throttle(web_server_b.inbound)
    """

    def __init__(self, policy_memory: PolicyMemory):
        self.policy_memory = policy_memory
        self.observations: List[LogEntry] = []

    def ingest_observations(self, observations: List[LogEntry]):
        """
        Ingest new observations for analysis.
        """
        self.observations.extend(observations)

    def extract_axioms(self) -> List[Dict[str, Any]]:
        """
        Analyzes observations to find correlations.
        Searches for DB IO Wait spike followed by Web Server Failure within a time window.
        """
        axioms = []

        # Sort observations by timestamp
        sorted_obs = sorted(self.observations, key=lambda x: x.timestamp)

        db_spikes = [o for o in sorted_obs if o.source == "db" and o.metric == "io_wait" and o.value > 0.8]

        for spike in db_spikes:
            # Look for web server failure in the next 2 minutes (120 seconds)
            window_start = spike.timestamp
            window_end = spike.timestamp + timedelta(minutes=2)

            failures = [
                o for o in sorted_obs
                if o.source == "web_server_b"
                and o.metric == "status"
                and o.value == 500
                and window_start < o.timestamp <= window_end
            ]

            if failures:
                logger.info(f"Pattern detected: DB spike at {spike.timestamp} followed by failure at {failures[0].timestamp}")
                axioms.append({
                    "cause": "db.io_wait > 0.8",
                    "effect": "web_server_b.failure",
                    "confidence": 0.9,
                    "suggested_action": "throttle(web_server_b.inbound)",
                    "time_lag_seconds": (failures[0].timestamp - spike.timestamp).total_seconds()
                })
                # Break to avoid duplicate axioms for the same pattern type (simplification)
                break

        return axioms

    def generate_policy_rule(self, axiom: Dict[str, Any]) -> str:
        """
        Converts an axiom into a structured rule string.
        """
        return f"IF {axiom['cause']} THEN {axiom['suggested_action']}"

    def register_rule_in_memory(self, rule: str, description: str):
        """
        Registers the learned rule into PolicyMemory.
        """
        policy_id = f"auto_rule_{int(datetime.now().timestamp())}"

        # We store the executable rule in the metadata
        record = self.policy_memory.register_policy(
            policy_id=policy_id,
            rule_type="auto_generated",
            description=description
        )

        # Update metadata with the actual rule logic
        record.metadata["logic"] = rule
        record.metadata["source"] = "PatternLearner"
        self.policy_memory._persist() # Save changes

        logger.info(f"Registered new policy: {policy_id} -> {rule}")
        return record
