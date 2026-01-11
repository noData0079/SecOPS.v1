import pytest
from unittest.mock import MagicMock
from backend.src.core.sandbox.shadow_runner import ShadowRunner, SimulationResult
from backend.src.core.outcomes.scorer import ActionOutcome, OutcomeScore, OutcomeCategory, OutcomeScorer

@pytest.fixture
def mock_executor():
    return MagicMock()

@pytest.fixture
def mock_scorer():
    scorer = MagicMock(spec=OutcomeScorer)
    scorer.score.return_value = OutcomeScore(
        score=85.0,
        category=OutcomeCategory.SUCCESS,
        confidence=0.9
    )
    return scorer

def test_shadow_runner_simulate_success(mock_executor, mock_scorer):
    runner = ShadowRunner(tool_executor=mock_executor, scorer=mock_scorer)

    # Mock executor return
    mock_outcome = ActionOutcome(
        action_id="test",
        incident_id="test",
        tool_used="test_tool",
        args={},
        success=True
    )
    mock_executor.return_value = mock_outcome

    result = runner.simulate("test_tool", {"arg": 1})

    assert isinstance(result, SimulationResult)
    assert result.outcome == mock_outcome
    assert result.passed is True

    # Verify executor called with shadow mode
    mock_executor.assert_called_once()
    args_called = mock_executor.call_args[0]
    assert args_called[0] == "test_tool"
    assert args_called[1]["arg"] == 1
    assert args_called[1]["_execution_mode"] == "shadow"

def test_shadow_runner_simulate_failure(mock_executor, mock_scorer):
    runner = ShadowRunner(tool_executor=mock_executor, scorer=mock_scorer)

    # Executor raises exception
    mock_executor.side_effect = Exception("Tool failed")

    # Scorer should still be called with a failed outcome
    mock_scorer.score.return_value = OutcomeScore(
        score=20.0,
        category=OutcomeCategory.FAILURE,
        confidence=0.8
    )

    result = runner.simulate("test_tool", {})

    assert result.outcome.success is False
    assert "Tool failed" in result.outcome.error
    assert result.passed is False
