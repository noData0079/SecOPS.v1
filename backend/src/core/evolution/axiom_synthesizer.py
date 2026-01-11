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
