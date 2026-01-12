import pytest
from unittest.mock import MagicMock
from backend.src.core.evolution.shadow_mirror import ShadowMirror
from backend.src.core.outcomes.comparator import Comparator
from backend.src.core.evolution.deploy_manager import DeployManager

class MockService:
    def process(self, payload):
        return f"Processed {payload}"

    def async_process(self, payload, callback):
        result = self.process(payload)
        callback(result)

def test_comparator():
    comp = Comparator()
    # Test Match
    res = comp.analyze_diff("A", "A")
    assert res["trust_score"] == 1.0
    assert res["matches"] is True

    # Test Mismatch
    res = comp.analyze_diff("A", "B")
    assert res["trust_score"] < 1.0
    assert res["matches"] is False

def test_shadow_mirror_flow():
    baseline = MockService()
    shadow = MockService()
    scorer = Comparator()

    mirror = ShadowMirror(baseline, shadow, scorer)

    # Spy on promote_shadow_to_baseline
    mirror.promote_shadow_to_baseline = MagicMock()

    result = mirror.handle_request("test_payload")

    assert result == "Processed test_payload"
    # Since mock returns match, logic inside callback should trigger
    # In this sync mock, callback runs immediately
    # Assuming Comparator mock returns high score, verify promotion logic *could* be called
    # But Comparator mock returns consistency_count 1001 for matches, so it SHOULD be called.

    mirror.promote_shadow_to_baseline.assert_called_once()

def test_deploy_manager():
    baseline = MockService()
    shadow = MockService()
    manager = DeployManager(baseline, shadow)

    result = manager.process_request("test_payload")
    assert result == "Processed test_payload"
