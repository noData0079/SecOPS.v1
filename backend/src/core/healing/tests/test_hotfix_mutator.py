import pytest
from unittest.mock import MagicMock, patch
from backend.src.core.healing.hotfix_mutator import HotFixMutator

def test_hotfix_mutator_synthesize_remedy():
    mutator = HotFixMutator()

    # Mock dependencies
    mutator.semantic_store = MagicMock()
    mutator.script_generator = MagicMock()
    mutator.sandbox = MagicMock()

    # Setup mocks
    mutator.semantic_store.search_facts.return_value = []
    mutator.script_generator.generate_tool.return_value = "print('Fixed')"
    mutator.sandbox.run_tool.return_value = {"status": "success"}

    # Test input
    anomaly_report = {
        "type": "memory_leak",
        "source": "service_a",
        "metric": "memory",
        "value": "100MB"
    }

    # Execute
    # We mock apply so it doesn't write to filesystem
    with patch.object(mutator, 'apply', return_value="fix-123") as mock_apply:
        fix_id = mutator.synthesize_remedy(anomaly_report)

        assert fix_id == "fix-123"
        mutator.script_generator.generate_tool.assert_called_once()
        mutator.sandbox.run_tool.assert_called_once()
        mock_apply.assert_called_once()

def test_hotfix_mutator_validation_failure():
    mutator = HotFixMutator()
    mutator.semantic_store = MagicMock()
    mutator.script_generator = MagicMock()
    mutator.sandbox = MagicMock()

    mutator.script_generator.generate_tool.return_value = "bad code"
    mutator.sandbox.run_tool.return_value = {"error": "SyntaxError"}

    anomaly_report = {"type": "test", "source": "test", "metric": "test", "value": 0}

    fix_id = mutator.synthesize_remedy(anomaly_report)
    assert fix_id is None
