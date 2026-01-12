import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class AxiomSynthesizer:
    def __init__(self, semantic_store, policy_memory):
        self.semantic_store = semantic_store
        self.policy_memory = policy_memory
        self.min_confidence = 0.85 # Only promote high-confidence patterns

    def synthesize_new_axioms(self, recent_incidents: List[Dict[str, Any]]):
        """
        Scans recent incidents to find recurring 'Pain Patterns'
        and converts them into hard Symbolic Rules.
        """
        # 1. Group similar incidents via Semantic Store
        # Note: SemanticStore doesn't have find_clusters, so we use a local implementation
        # that mimics the intended behavior or uses available methods.
        patterns = self._find_clusters(recent_incidents)

        new_axioms = []
        for pattern in patterns:
            if pattern['confidence'] > self.min_confidence:
                # 2. Extract Logic (The Neuro-Symbolic Leap)
                axiom = self._induce_logic(pattern)
                new_axioms.append(axiom)

        # 3. Commit to Policy Memory
        for axiom in new_axioms:
            self._add_rule_to_policy_memory(axiom)
            print(f"[EVOLUTION] New Axiom Synthesized: {axiom['id']} - {axiom['logic_summary']}")

    def _find_clusters(self, incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups incidents by common root causes or triggers.
        """
        clusters: Dict[str, List[Dict]] = {}
        for incident in incidents:
            # key by root_cause if available, else trigger
            key = incident.get('root_cause') or incident.get('trigger') or "unknown"
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(incident)

        patterns = []
        for key, group in clusters.items():
            if not key or key == "unknown":
                continue

            # Simple confidence metric: based on number of occurrences
            count = len(group)
            confidence = min(0.99, count * 0.2) # 5 incidents = 1.0 confidence (capped at 0.99)

            patterns.append({
                'common_trigger': group[0].get('trigger'),
                'root_cause': group[0].get('root_cause'),
                'confidence': confidence,
                'incident_count': count,
                'examples': group
            })
        return patterns

    def _induce_logic(self, pattern_data: Dict) -> Dict:
        """
        Generates a deterministic 'If-Then' rule from fuzzy incident data.
        """
        # Example output structure for the Policy Layer
        data_str = str(pattern_data.get('root_cause', '')) + str(pattern_data.get('common_trigger', ''))
        axiom_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
        axiom_id = f"AXIOM-{axiom_hash}"

        root_cause = pattern_data.get('root_cause', 'unknown')
        trigger = pattern_data.get('common_trigger', 'unknown')

        # Logic summary
        logic_summary = f"Prevent issues caused by {root_cause} when {trigger} occurs."

        # Simplistic action generation for now
        # Ideally this would come from an LLM or a lookup of available remediations
        action = f"throttle_process('{root_cause}', 0.5)" if root_cause != 'unknown' else "alert_admin()"

        return {
            "id": axiom_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger,
            "condition": root_cause,
            "action": action,
            "logic_summary": logic_summary,
            "type": "SYMBOLIC_RULE"
        }

    def _add_rule_to_policy_memory(self, axiom: Dict):
        """
        Adds the rule to policy memory.
        """
        # Register the policy
        self.policy_memory.register_policy(
            policy_id=axiom['id'],
            rule_type=axiom['type'],
            description=axiom['logic_summary']
        )

        # Store full axiom details in metadata
        if hasattr(self.policy_memory, 'policies') and axiom['id'] in self.policy_memory.policies:
            record = self.policy_memory.policies[axiom['id']]
            record.metadata.update(axiom)
            # Persist changes if possible (accessing protected member if needed, or rely on next save)
            if hasattr(self.policy_memory, '_persist'):
                self.policy_memory._persist()
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
