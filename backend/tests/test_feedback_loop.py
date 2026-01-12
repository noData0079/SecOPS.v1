
import pytest
import json
import shutil
from pathlib import Path
from src.core.training.feedback_loop import FeedbackCollector, FeedbackEntry
from src.core.memory.episodic_store import EpisodicStore, IncidentMemory, EpisodeSnapshot

@pytest.fixture
def temp_feedback_dir(tmp_path):
    d = tmp_path / "feedback_test"
    d.mkdir()
    return d

@pytest.fixture
def mock_episodic_store(mocker):
    # Mock the EpisodicStore to return a fake incident
    store = mocker.Mock(spec=EpisodicStore)

    incident = IncidentMemory(
        incident_id="inc-123",
        episodes=[
            EpisodeSnapshot(
                episode_id="ep-1",
                incident_id="inc-123",
                observation="Server is down",
                action_taken={"tool": "restart_server", "reasoning": "Restarting fixes it"},
                outcome={"success": True}
            )
        ]
    )
    store.get_incident.return_value = incident
    return store

def test_collect_feedback(temp_feedback_dir):
    collector = FeedbackCollector(feedback_dir=temp_feedback_dir)

    success = collector.collect_feedback("inc-123", 1, "Good job")
    assert success is True

    feedback_file = temp_feedback_dir / "feedback.jsonl"
    assert feedback_file.exists()

    with open(feedback_file, "r") as f:
        content = f.read()
        data = json.loads(content)
        assert data["incident_id"] == "inc-123"
        assert data["rating"] == 1
        assert data["comment"] == "Good job"

def test_get_training_examples(temp_feedback_dir, mock_episodic_store, mocker):
    # Patch EpisodicStore in feedback_loop module
    mocker.patch("src.core.training.feedback_loop.EpisodicStore", return_value=mock_episodic_store)

    collector = FeedbackCollector(feedback_dir=temp_feedback_dir)

    # 1. Collect feedback
    collector.collect_feedback("inc-123", 1, "Great")
    collector.collect_feedback("inc-456", -1, "Bad") # Should be ignored

    # 2. Get examples
    examples = collector.get_training_examples()

    assert len(examples) == 1
    example = examples[0]

    assert "Server is down" in example["instruction"]
    assert "restart_server" in example["output"]
    assert example["source"] == "human_feedback"

def test_get_training_examples_no_feedback(temp_feedback_dir):
    collector = FeedbackCollector(feedback_dir=temp_feedback_dir)
    examples = collector.get_training_examples()
    assert len(examples) == 0
