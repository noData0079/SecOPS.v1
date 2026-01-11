"""
Axiom Synthesizer - Neuro-Symbolic Logic Induction

This module turns "fuzzy" neural observations into "hard" IT code (Axioms).
It enforces logic like: IF agent_id == 7 AND db_load > 0.6 THEN set_throttle(0.5)
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)

@dataclass
class Observation:
    """Represents a data point from the system."""
    source: str
    metrics: Dict[str, Any]
    timestamp: float

@dataclass
class Axiom:
    """Represents a synthesized hard rule."""
    condition: str
    action: str
    confidence: float
    created_at: float

class AxiomSynthesizer:
    """
    Synthesizes hard axioms from repeated patterns in observations.
    """

    def __init__(self):
        self.observations: List[Observation] = []
        self.axioms: List[Axiom] = []
        # Threshold to trigger axiom creation (e.g., seen pattern 3 times)
        self.pattern_threshold = 3
        self.pattern_counts: Dict[str, int] = {}

    def ingest_observation(self, source: str, metrics: Dict[str, Any]):
        """
        Ingests a new observation and checks for patterns.
        """
        obs = Observation(source, metrics, time.time())
        self.observations.append(obs)

        # Prune old observations (keep last 1000)
        if len(self.observations) > 1000:
            self.observations = self.observations[-1000:]

        self._analyze_patterns(obs)

    def _analyze_patterns(self, latest_obs: Observation):
        """
        Analyzes observations to find causal links.
        Simulated logic: If db_load > 0.6 and agent_id == 7 consistently, create axiom.
        """
        # Hardcoded simulation for the demo scenario
        if latest_obs.source == "agent_7" and latest_obs.metrics.get("db_load", 0) > 0.6:
            pattern_key = "agent_7_high_db_load"
            self.pattern_counts[pattern_key] = self.pattern_counts.get(pattern_key, 0) + 1

            if self.pattern_counts[pattern_key] >= self.pattern_threshold:
                self._synthesize_axiom(
                    condition="agent_id == 7 AND db_load > 0.6",
                    action="set_throttle(0.5)"
                )
                # Reset count to avoid spamming
                self.pattern_counts[pattern_key] = 0

    def _synthesize_axiom(self, condition: str, action: str):
        """
        Creates a new Axiom.
        """
        # Check if exists
        for ax in self.axioms:
            if ax.condition == condition and ax.action == action:
                return

        new_axiom = Axiom(
            condition=condition,
            action=action,
            confidence=0.99, # High confidence for synthesized axioms
            created_at=time.time()
        )
        self.axioms.append(new_axiom)
        logger.info(f"Synthesized New Axiom: IF {condition} THEN {action}")

    def get_active_axioms(self) -> List[Axiom]:
        return self.axioms

    def evaluate(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Evaluates current context against axioms.
        Returns the action string if a rule matches.
        """
        for axiom in self.axioms:
            # Simple eval for demonstration.
            # In production, use a safe rule engine or AST evaluation.
            try:
                # We need to parse the condition string relative to context
                # "agent_id == 7 AND db_load > 0.6"
                # We can do a simple replacement for this MVP
                cond = axiom.condition.replace("AND", "and").replace("OR", "or")

                # Check if context has keys needed
                # For safety, we only allow known keys in eval
                safe_context = {k: v for k, v in context.items() if k in ["agent_id", "db_load", "cpu_usage"]}

                if eval(cond, {"__builtins__": {}}, safe_context):
                    return axiom.action
            except Exception as e:
                logger.debug(f"Axiom eval failed: {e}")
                continue
        return None
