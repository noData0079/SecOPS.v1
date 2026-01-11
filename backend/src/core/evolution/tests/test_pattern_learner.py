import pytest
from datetime import datetime, timedelta
from backend.src.core.evolution.pattern_learner import PatternLearner, LogEntry
from backend.src.core.memory.policy_memory import PolicyMemory

class MockPolicyMemory:
    def __init__(self):
        self.policies = []

    def register_policy(self, policy_id, rule_type, description):
        # Return a mock object that can accept metadata assignment
        class MockRecord:
            metadata = {}
        return MockRecord()

    def _persist(self):
        pass

def test_pattern_learner_axioms():
    learner = PatternLearner(policy_memory=MockPolicyMemory())

    now = datetime.now()

    observations = [
        LogEntry(source="db", metric="io_wait", value=0.9, timestamp=now, context={}),
        LogEntry(source="web_server_b", metric="status", value=500, timestamp=now + timedelta(seconds=30), context={})
    ]

    learner.ingest_observations(observations)
    axioms = learner.extract_axioms()

    assert len(axioms) == 1
    assert axioms[0]["cause"] == "db.io_wait > 0.8"
    assert axioms[0]["effect"] == "web_server_b.failure"

def test_pattern_learner_git_latency():
    learner = PatternLearner(policy_memory=MockPolicyMemory())
    now = datetime.now()

    observations = [
        LogEntry(source="git", metric="push_event", value=1, timestamp=now, context={"author": "TeamB"}),
        LogEntry(source="prod_api", metric="latency", value=1200, timestamp=now + timedelta(minutes=1), context={})
    ]

    learner.ingest_observations(observations)
    axioms = learner.extract_axioms()

    assert len(axioms) == 1
    assert "git_event.author == 'TeamB'" in axioms[0]["cause"]
    assert axioms[0]["suggested_action"] == "pre_warm_cache()"

def test_register_rule():
    mock_memory = MockPolicyMemory()
    learner = PatternLearner(policy_memory=mock_memory)

    record = learner.register_rule_in_memory("IF x THEN y", "Test Rule")
    assert record.metadata["logic"] == "IF x THEN y"
