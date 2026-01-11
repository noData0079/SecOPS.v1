
import unittest
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock
from datetime import datetime

from backend.src.core.autonomy.loop import AutonomyLoop, Observation, Outcome, PolicyDecision, PolicyEngine
from backend.src.core.memory.episodic_store import EpisodicStore, EpisodeSnapshot
from backend.src.core.memory.semantic_store import SemanticStore
from backend.src.core.memory.distiller import KnowledgeDistiller


class TestCognitiveHealth(unittest.TestCase):
    def setUp(self):
        # Setup temporary directories
        self.test_dir = Path("test_data")
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir()

        self.cognitive_trace_dir = Path("data/cognitive_trace") # This is hardcoded in the loop class for now
        # We should back up existing cognitive traces if any, but in this sandbox it's fine.
        # Ideally we'd patch the path in the class.

        self.replay_path = self.test_dir / "replay"
        self.replay_path.mkdir()

        self.approvals_path = self.test_dir / "approvals"
        self.approvals_path.mkdir()

        self.policy_engine = MagicMock(spec=PolicyEngine)
        self.policy_engine.tool_registry = {"test_tool": {}}
        self.policy_engine.evaluate.return_value = (PolicyDecision.ALLOW, "Allowed")
        self.policy_engine.update_tool_stats = MagicMock()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        # Clean up cognitive traces created during test
        # for f in self.cognitive_trace_dir.glob("*.json"):
        #     f.unlink()

    def test_cognitive_trace_creation(self):
        """Test that cognitive trace is created with reasoning and hash."""

        # Mock model response
        mock_response = {
            "tool": "test_tool",
            "args": {"x": 1},
            "reasoning": "I need to test this.",
            "confidence": 95
        }

        def model_fn(prompt, tools):
            return mock_response

        def tool_executor(name, args):
            return Outcome(success=True)

        loop = AutonomyLoop(
            policy_engine=self.policy_engine,
            model_fn=model_fn,
            tool_executor=tool_executor,
            replay_store_path=self.replay_path,
            approvals_path=self.approvals_path
        )
        loop.reset("test_incident_001")

        obs = Observation(content="Something happened", source="test")
        decision, outcome = loop.run_step(obs)

        # Check if trace file exists
        files = list(self.cognitive_trace_dir.glob("*.json"))
        # We expect at least one file. Since we don't control the exact timestamp, we just check existence.
        # To be more precise, we can check the content of the latest file.
        self.assertTrue(len(files) > 0)

        latest_trace = sorted(files, key=lambda f: f.stat().st_mtime)[-1]
        with open(latest_trace) as f:
            data = json.load(f)

        self.assertEqual(data["reasoning"], "I need to test this.")
        self.assertEqual(data["confidence"], 95)
        self.assertTrue("reasoning_hash" in data)

    def test_low_confidence_triggers_approval(self):
        """Test that low confidence triggers WAIT_APPROVAL."""

        mock_response = {
            "tool": "test_tool",
            "args": {},
            "reasoning": "Not sure about this.",
            "confidence": 50  # < 70
        }

        def model_fn(prompt, tools):
            return mock_response

        def tool_executor(name, args):
            return Outcome(success=True)

        loop = AutonomyLoop(
            policy_engine=self.policy_engine,
            model_fn=model_fn,
            tool_executor=tool_executor,
            replay_store_path=self.replay_path,
            approvals_path=self.approvals_path
        )
        loop.reset("test_incident_002")

        # Mock _wait_for_approval to avoid blocking
        loop._wait_for_approval = MagicMock()

        obs = Observation(content="Risk here", source="test")

        # The run_step should internally call _wait_for_approval and then return ALLOW (as per logic)
        # Or return WAIT_APPROVAL if we changed logic to return it?
        # The code says:
        # if decision == PolicyDecision.WAIT_APPROVAL:
        #    self._wait_for_approval(self.incident_id)
        #    decision = PolicyDecision.ALLOW

        decision, outcome = loop.run_step(obs)

        # Check if _wait_for_approval was called
        loop._wait_for_approval.assert_called_with("test_incident_002")
        self.assertEqual(decision, PolicyDecision.ALLOW)

    def test_distiller(self):
        """Test knowledge distillation logic."""

        episodic_store = EpisodicStore(storage_path=self.test_dir / "episodic")
        semantic_store = SemanticStore(storage_path=self.test_dir / "semantic")

        distiller = KnowledgeDistiller(episodic_store, semantic_store)

        # Create dummy incidents
        for i in range(5):
            mem = episodic_store.start_incident(f"inc_{i}")
            # Add successful usage of "magic_tool"
            mem.episodes.append(EpisodeSnapshot(
                episode_id=f"ep_{i}",
                incident_id=f"inc_{i}",
                action_taken={"tool": "magic_tool"},
                outcome={"success": True}
            ))
            episodic_store.close_incident(f"inc_{i}", "resolved")

        # Create unsuccessful incidents for "bad_tool"
        for i in range(5):
            mem = episodic_store.start_incident(f"inc_bad_{i}")
            mem.episodes.append(EpisodeSnapshot(
                episode_id=f"ep_bad_{i}",
                incident_id=f"inc_bad_{i}",
                action_taken={"tool": "bad_tool"},
                outcome={"success": False}
            ))
            episodic_store.close_incident(f"inc_bad_{i}", "resolved") # Even if resolved, the tool might have failed inside?
            # Actually distiller looks at tool outcome.
            # "success = episode.outcome.get("success", False)"

        # Run distillation
        distiller.distill_daily()

        # Check semantic store
        # magic_tool should have a rule
        facts = semantic_store.get_facts_by_category("tool_effectiveness")
        magic_rule = next((f for f in facts if "magic_tool" in f.fact_id), None)
        self.assertIsNotNone(magic_rule)
        self.assertIn("highly effective", magic_rule.content)

        bad_rule = next((f for f in facts if "bad_tool" in f.fact_id), None)
        self.assertIsNotNone(bad_rule)
        self.assertIn("rarely works", bad_rule.content)

if __name__ == '__main__':
    unittest.main()
