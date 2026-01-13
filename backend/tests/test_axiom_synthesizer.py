"""
Tests for Axiom Synthesizer.
"""
import pytest
from unittest.mock import MagicMock
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

    # Correct instantiation based on the class definition
    synthesizer = AxiomSynthesizer(mock_semantic_store, mock_policy_memory)

    # Verify initialization
    assert synthesizer.semantic_store == mock_semantic_store
    assert synthesizer.policy_memory == mock_policy_memory

    # Test synthesize_new_axioms flow
    incidents = [
        {"root_cause": "cpu_spike", "trigger": "process_x"},
        {"root_cause": "cpu_spike", "trigger": "process_x"},
        {"root_cause": "cpu_spike", "trigger": "process_x"},
        {"root_cause": "cpu_spike", "trigger": "process_x"},
        {"root_cause": "cpu_spike", "trigger": "process_x"}
    ]

    synthesizer.synthesize_new_axioms(incidents)

    # Should have registered a policy
    assert mock_policy_memory.register_policy.called
