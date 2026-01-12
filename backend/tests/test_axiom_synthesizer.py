
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from backend.src.core.evolution.axiom_synthesizer import AxiomSynthesizer

def test_axiom_synthesizer_flow():
    # Mock dependencies
    mock_semantic_store = MagicMock()
    mock_policy_memory = MagicMock()

    # Mock PolicyRecord returned by register_policy
    mock_policy_record = MagicMock()
    mock_policy_record.metadata = {}
    mock_policy_memory.register_policy.return_value = mock_policy_record

    # Mock policies dict in policy_memory
    mock_policy_memory.policies = {}

    # When register_policy is called, we should simulate adding it to policies dict
    # so that the subsequent check `axiom['id'] in self.policy_memory.policies` passes
    def side_effect_register(policy_id, rule_type, description):
        mock_policy_memory.policies[policy_id] = mock_policy_record
        return mock_policy_record

    mock_policy_memory.register_policy.side_effect = side_effect_register

    synthesizer = AxiomSynthesizer(mock_semantic_store, mock_policy_memory)

    # Sample incidents
    # We need at least 5 similar incidents to reach confidence > 0.85 (since 5 * 0.2 = 1.0)
    # The code calculates confidence as min(0.99, count * 0.2)
    # 4 incidents * 0.2 = 0.8 (too low)
    # 5 incidents * 0.2 = 1.0 (pass)
    incidents = [
        {"trigger": "high_latency", "root_cause": "db_backup", "timestamp": "2023-01-01T10:00:00"},
        {"trigger": "high_latency", "root_cause": "db_backup", "timestamp": "2023-01-01T10:05:00"},
        {"trigger": "high_latency", "root_cause": "db_backup", "timestamp": "2023-01-01T10:10:00"},
        {"trigger": "high_latency", "root_cause": "db_backup", "timestamp": "2023-01-01T10:15:00"},
        {"trigger": "high_latency", "root_cause": "db_backup", "timestamp": "2023-01-01T10:20:00"},
    ]

    synthesizer.synthesize_new_axioms(incidents)

    # Verify clustering
    # Should have called register_policy once
    assert mock_policy_memory.register_policy.call_count == 1

    # call_args could be args tuple or kwargs, so we check specifically
    call_args = mock_policy_memory.register_policy.call_args
    # call_args[1] is kwargs, call_args[0] is args
    kwargs = call_args[1]

    policy_id = kwargs.get('policy_id')
    rule_type = kwargs.get('rule_type')

    assert rule_type == "SYMBOLIC_RULE"
    assert "AXIOM-" in policy_id

    # Verify metadata update
    assert "action" in mock_policy_record.metadata
    assert mock_policy_record.metadata["action"] == "throttle_process('db_backup', 0.5)"
