import unittest
from datetime import datetime
from backend.src.core.autonomy.policy_engine import (
    PolicyEngine,
    PolicyDecision,
    AgentState,
    ProposedAction,
    RiskLevel,
    ToolState
)

class TestPolicyEngine(unittest.TestCase):
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
            },
            "medium_risk_tool": {
                "risk": "medium",
                "prod_allowed": True,
                "inputs": []
            }
        }
        self.engine = PolicyEngine(self.tool_registry)
        self.state = AgentState()
        # Initialize tool states for testing decay
        self.state.tool_states["test_tool"] = ToolState(confidence=1.0)
        self.state.tool_states["high_risk_tool"] = ToolState(confidence=1.0)
        self.state.tool_states["medium_risk_tool"] = ToolState(confidence=1.0)

    def test_high_risk_wait_approval(self):
        """Test that high risk actions return WAIT_APPROVAL."""
        action = {
            "tool": "high_risk_tool",
            "confidence": 0.9,
            "args": {}
        }
        decision, reason = self.engine.evaluate(action, self.state)
        self.assertEqual(decision, PolicyDecision.WAIT_APPROVAL)
        self.assertIn("waiting for approval", reason)

    def test_blacklisting_failures(self):
        """Test dynamic blacklisting after max failures."""
        # Fail twice
        self.engine.update_tool_stats(self.state, "test_tool", success=False)
        self.engine.update_tool_stats(self.state, "test_tool", success=False)

        # Check if blacklisted
        self.assertTrue(self.state.tool_states["test_tool"].is_blacklisted)
        self.assertIn("Too many failures", self.state.tool_states["test_tool"].blacklist_reason)

        # Try to use again
        action = {
            "tool": "test_tool",
            "confidence": 0.9,
            "args": {"arg1": "val"}
        }
        decision, reason = self.engine.evaluate(action, self.state)
        self.assertEqual(decision, PolicyDecision.BLOCK)

    def test_confidence_decay(self):
        """Test confidence decay for unused tools."""
        initial_confidence = self.state.tool_states["test_tool"].confidence

        # Use another tool successfully
        self.engine.update_tool_stats(self.state, "medium_risk_tool", success=True)

        # Check decay on test_tool (unused)
        self.assertLess(self.state.tool_states["test_tool"].confidence, initial_confidence)

        # Check boost/maintenance on medium_risk_tool (used)
        self.assertGreaterEqual(self.state.tool_states["medium_risk_tool"].confidence, 1.0) # Boosted to cap or kept

    def test_medium_risk_low_confidence(self):
        """Test escalation for medium risk with low confidence."""
        # Case 1: Low Model Confidence
        action = {
            "tool": "medium_risk_tool",
            "confidence": 0.5, # Below 0.70 threshold
            "args": {}
        }
        decision, reason = self.engine.evaluate(action, self.state)
        self.assertEqual(decision, PolicyDecision.ESCALATE)

        # Case 2: Low Policy Confidence
        # Artificially lower policy confidence
        self.state.tool_states["medium_risk_tool"].confidence = 0.4
        action["confidence"] = 0.9 # High model confidence

        decision, reason = self.engine.evaluate(action, self.state)
        self.assertEqual(decision, PolicyDecision.ESCALATE)

if __name__ == "__main__":
    unittest.main()
