import pytest
from unittest.mock import MagicMock, patch
from backend.src.core.simulation.chaos_agent import ChaosAgent, ChaosScenario
from backend.src.core.autonomy.policy_engine import PolicyDecision
from backend.src.core.sandbox.shadow_runner import SimulationResult
from backend.src.core.outcomes.scorer import OutcomeScore, OutcomeCategory, ActionOutcome

@pytest.fixture
def mock_components():
    return {
        "policy_engine": MagicMock(),
        "policy_memory": MagicMock(),
        "shadow_runner": MagicMock(),
    }

def test_chaos_agent_run_session(mock_components):
    agent = ChaosAgent(**mock_components)

    # Mock scenario list to just one for predictability
    agent.scenarios = [
        ChaosScenario(
            name="Test Attack",
            description="test",
            tool_name="risky_tool",
            malicious_args={},
            expected_policy_decision=PolicyDecision.BLOCK
        )
    ]

    # Mock Policy Engine to ALLOW (simulating a vulnerability)
    mock_components["policy_engine"].evaluate.return_value = (PolicyDecision.ALLOW, "Allowed")

    # Mock Shadow Runner to FAIL (confirming it's bad)
    mock_components["shadow_runner"].simulate.return_value = SimulationResult(
        outcome=ActionOutcome(
            action_id="1", incident_id="1", tool_used="risky_tool", args={}, success=False
        ),
        score=OutcomeScore(score=10.0, category=OutcomeCategory.FAILURE, confidence=0.9)
    )

    # Run session for minimal time
    agent.run_chaos_session(duration_seconds=0.1)

    # Verify Policy Memory was updated
    mock_components["policy_memory"].record_application.assert_called()
    mock_components["policy_memory"].register_policy.assert_called()

def test_chaos_agent_successful_defense(mock_components):
    agent = ChaosAgent(**mock_components)

    agent.scenarios = [
        ChaosScenario(
            name="Test Attack",
            description="test",
            tool_name="risky_tool",
            malicious_args={},
            expected_policy_decision=PolicyDecision.BLOCK
        )
    ]

    # Policy BLOCKS correctly
    mock_components["policy_engine"].evaluate.return_value = (PolicyDecision.BLOCK, "Blocked")

    agent.run_chaos_session(duration_seconds=0.1)

    # Shadow runner should NOT be called
    mock_components["shadow_runner"].simulate.assert_not_called()

    # Policy memory updated with success
    mock_components["policy_memory"].record_application.assert_called_with(
        "policy-risky_tool", was_effective=True
    )
