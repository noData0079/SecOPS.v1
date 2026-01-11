import unittest
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from backend.src.core.autonomy.loop import AutonomyLoop, Observation, Outcome
from backend.src.core.autonomy.policy_engine import PolicyEngine, PolicyDecision, AgentState

class TestAutonomyLoop(unittest.TestCase):
    def setUp(self):
        self.tool_registry = {
            "test_tool": {
                "risk": "low",
                "prod_allowed": True,
                "inputs": ["arg1"]
            },
            "high_risk_tool": {
                "risk": "high",
                "prod_allowed": False,
                "inputs": []
            }
        }
        self.policy_engine = PolicyEngine(self.tool_registry)
        self.mock_model = MagicMock()
        self.mock_executor = MagicMock()

        self.approvals_path = Path("backend/tests/approvals_tmp")
        self.replay_path = Path("backend/tests/replay_tmp")

        self.loop = AutonomyLoop(
            policy_engine=self.policy_engine,
            model_fn=self.mock_model,
            tool_executor=self.mock_executor,
            replay_store_path=self.replay_path,
            approvals_path=self.approvals_path
        )
        self.loop.reset("test_incident")

    def tearDown(self):
        if self.approvals_path.exists():
            shutil.rmtree(self.approvals_path)
        if self.replay_path.exists():
            shutil.rmtree(self.replay_path)

    def test_run_step_success(self):
        """Test a successful run step."""
        obs = Observation(content="test", source="test")

        # Mock model response
        self.mock_model.return_value = {
            "tool": "test_tool",
            "confidence": 0.9,
            "args": {"arg1": "val"}
        }

        # Mock execution
        self.mock_executor.return_value = Outcome(success=True)

        decision, outcome = self.loop.run_step(obs)

        self.assertEqual(decision, PolicyDecision.ALLOW)
        self.assertTrue(outcome.success)
        self.assertEqual(self.loop.state.actions_taken, 1)

    def test_wait_approval_flow(self):
        """Test the WAIT_APPROVAL flow with file simulation."""
        obs = Observation(content="test", source="test")

        # Mock model response for high risk tool
        self.mock_model.return_value = {
            "tool": "high_risk_tool",
            "confidence": 0.9,
            "args": {}
        }

        # Mock execution
        self.mock_executor.return_value = Outcome(success=True)

        # Run step in a separate thread or just create the file beforehand for this synchronous test?
        # Since _wait_for_approval blocks, we need to ensure the file exists or is created.
        # For simplicity, let's "mock" the _wait_for_approval to just check if file exists,
        # or we can assume it blocks.
        # But wait, if I run `run_step`, it will block forever if file doesn't exist.
        # I will start a timer to create the file.

        import threading
        import time

        def create_approval():
            time.sleep(0.5)
            (self.approvals_path / "test_incident.approve").touch()

        t = threading.Thread(target=create_approval)
        t.start()

        start_time = time.time()
        decision, outcome = self.loop.run_step(obs)
        end_time = time.time()

        t.join()

        # Verify it waited
        self.assertGreater(end_time - start_time, 0.4)

        # Verify it proceeded
        self.assertEqual(decision, PolicyDecision.ALLOW)
        self.assertTrue(outcome.success)

    def test_update_stats_integration(self):
        """Verify tool stats are updated after step."""
        obs = Observation(content="test", source="test")
        self.mock_model.return_value = {
            "tool": "test_tool",
            "confidence": 0.9,
            "args": {"arg1": "val"}
        }
        self.mock_executor.return_value = Outcome(success=False) # Fail

        self.loop.run_step(obs)

        tool_state = self.loop.state.tool_states["test_tool"]
        self.assertEqual(tool_state.failure_count, 1)

if __name__ == "__main__":
    unittest.main()
