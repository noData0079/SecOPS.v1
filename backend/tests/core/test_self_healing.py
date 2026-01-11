import pytest
import os
import json
from datetime import datetime
from backend.src.core.autonomy.mutator import MutationEngine, MutationResult
from backend.src.core.outcomes.rca_engine import RootCauseSynthesizer, ReplayEntry
from backend.src.core.tools.hotpatcher import HotPatcher

# --- Mutation Engine Tests ---

class TestMutationEngine:
    def test_timeout_mutation(self):
        engine = MutationEngine()

        args = {"timeout": 10, "url": "http://example.com"}
        error = "Connection timed out after 10000ms"

        result = engine.mutate("http_request", args, error)

        assert result.should_retry is True
        assert result.strategy == "timeout_increase"
        assert result.new_args["timeout"] == 20

    def test_validation_failure_heuristic(self):
        # We don't have many heuristics implemented yet, but let's test the retry logic
        engine = MutationEngine()
        args = {"count": "5"}
        error = "400 Bad Request: Invalid parameter"

        # Without model, it should just fail or retry without change if classified as transient
        # 400 is VALIDATION -> usually not recoverable without model
        result = engine.mutate("some_tool", args, error)
        assert result.should_retry is False

    def test_model_mutation(self):
        engine = MutationEngine()
        args = {"invalid_json": True}
        error = "Validation failed"

        def mock_model(prompt):
            return '```json\n{"valid_json": true}\n```'

        result = engine.mutate("test_tool", args, error, model_fn=mock_model)

        assert result.should_retry is True
        assert result.new_args == {"valid_json": True}
        assert result.strategy == "model_correction"


# --- RCA Engine Tests ---

class TestRCAEngine:
    def test_root_cause_analysis(self):
        engine = RootCauseSynthesizer()

        # Create a history
        # 1. Successful read
        e1 = ReplayEntry(
            incident_id="inc-1",
            observation="Obs 1",
            action={"tool": "get_logs"},
            outcome={"success": True},
            resolution_time_seconds=10
        )
        # 2. State change (Root Cause)
        e2 = ReplayEntry(
            incident_id="inc-1",
            observation="Obs 2",
            action={"tool": "update_config", "args": {"bad": "config"}},
            outcome={"success": True}, # It succeeded but caused issues later
            resolution_time_seconds=20
        )
        # 3. Read (Verification)
        e3 = ReplayEntry(
            incident_id="inc-1",
            observation="Obs 3",
            action={"tool": "get_status"},
            outcome={"success": True},
            resolution_time_seconds=30
        )
        # 4. Failure
        e4 = ReplayEntry(
            incident_id="inc-1",
            observation="Obs 4",
            action={"tool": "restart_service"},
            outcome={"success": False, "error": "Config invalid"},
            resolution_time_seconds=40
        )

        history = [e1, e2, e3, e4]

        report = engine.analyze("inc-1", history)

        assert report is not None
        assert report.root_cause_action_index == 1 # e2 is index 1
        assert "update_config" in report.reasoning
        assert "restart_service" in report.reasoning


# --- HotPatcher Tests ---

class TestHotPatcher:
    def test_apply_firewall_rule(self):
        patcher = HotPatcher()

        # Valid rule
        outcome = patcher.apply_firewall_rule("BLOCK 10.0.0.1")
        assert outcome.success is True
        assert outcome.side_effects is True

        # Invalid rule
        outcome = patcher.apply_firewall_rule("ALLOW ALL")
        assert outcome.success is False

    def test_patch_file(self, tmp_path):
        patcher = HotPatcher()

        # Create dummy file in current working directory to pass security check
        # We'll use a temporary file name
        import os
        cwd = os.getcwd()
        test_file = os.path.join(cwd, "test_temp_patch.conf")

        with open(test_file, "w") as f:
            f.write("server_port=80")

        try:
            outcome = patcher.patch_file(test_file, "server_port=80", "server_port=8080")

            assert outcome.success is True
            with open(test_file, "r") as f:
                assert f.read() == "server_port=8080"

            # Check backup
            backup = test_file + ".bak"
            assert os.path.exists(backup)
            with open(backup, "r") as f:
                assert f.read() == "server_port=80"
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
            if os.path.exists(test_file + ".bak"):
                os.remove(test_file + ".bak")

    def test_revert_patch(self, tmp_path):
        patcher = HotPatcher()

        f = tmp_path / "test.conf"
        f.write_text("server_port=8080")

        # Create backup manually
        backup = tmp_path / "test.conf.bak"
        backup.write_text("server_port=80")

        outcome = patcher.revert_patch(str(f))

        assert outcome.success is True
        assert f.read_text() == "server_port=80"
        assert not backup.exists()
