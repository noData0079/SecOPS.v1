import unittest
import os
import json
import shutil
from backend.src.core.tools.synthesis_engine import ToolSynthesizer
from backend.src.core.simulation.chaos_agent import ChaosAgent, DigitalTwin, SystemState
from backend.src.core.network.p2p_sync import P2PSyncEngine

class TestAdvancedFeatures(unittest.TestCase):

    def setUp(self):
        # Setup temporary directories for testing
        self.test_approvals_dir = "backend/approvals_test"
        self.test_export_dir = "data/exports_test/threat_dna"
        self.test_import_dir = "data/imports_test/threat_dna"

        os.makedirs(self.test_approvals_dir, exist_ok=True)
        os.makedirs(self.test_export_dir, exist_ok=True)
        os.makedirs(self.test_import_dir, exist_ok=True)

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.test_approvals_dir):
            shutil.rmtree(self.test_approvals_dir)
        if os.path.exists("data/exports_test"):
            shutil.rmtree("data/exports_test")
        if os.path.exists("data/imports_test"):
            shutil.rmtree("data/imports_test")

    def test_dynamic_tool_synthesis(self):
        """Test that the MacGyver engine generates a tool and queues it for approval."""
        synthesizer = ToolSynthesizer()
        # Override the directory for test safety
        synthesizer.approvals_path = self.test_approvals_dir

        # 1. Synthesize a valid tool
        result = synthesizer.generate_tool_candidate(
            tool_name="test_tool",
            purpose="testing synthesis"
        )

        self.assertEqual(result["status"], "wait_approval")

        # Verify file exists
        files = os.listdir(self.test_approvals_dir)
        self.assertTrue(len(files) > 0, "No approval file created")

        with open(os.path.join(self.test_approvals_dir, files[0]), "r") as f:
            content = json.load(f)
            self.assertEqual(content["tool_name"], "test_tool")

        # 2. Synthesize an unsafe tool (Sandbox check)
        unsafe_code = "import os; os.system('rm -rf /')"
        result_unsafe = synthesizer.generate_tool_candidate(
            tool_name="unsafe_tool",
            purpose="destruction",
            simulated_code=unsafe_code
        )
        self.assertEqual(result_unsafe["status"], "rejected")

    def test_predictive_threat_simulation(self):
        """Test that the Chaos Agent finds vulnerabilities in the Digital Twin."""
        # Setup a vulnerable state
        vulnerable_state = SystemState(db_encryption_active=False)
        twin = DigitalTwin(initial_state=vulnerable_state)
        chaos = ChaosAgent(twin)

        results = chaos.run_simulation()

        # We expect at least one success (SQLInjection_Unencrypted)
        successes = [r for r in results if r.success]
        self.assertTrue(len(successes) > 0)

        found = False
        for s in successes:
            if s.attack_name == "SQLInjection_Unencrypted":
                found = True
                self.assertIsNotNone(s.remediation_plan)
                self.assertIn("Enable Database Encryption", s.remediation_plan)

        self.assertTrue(found, "Did not detect the unencrypted DB vulnerability")

    def test_federated_sovereignty(self):
        """Test the P2P sync (export/import of ThreatDNA)."""
        engine = P2PSyncEngine()
        # Override dirs
        engine.export_dir = self.test_export_dir
        engine.import_dir = self.test_import_dir

        # 1. Register and Export
        engine.register_threat("Test_Threat", "bad_signature_123", "Block IP")
        engine.export_threat_dna()

        # Verify export file exists
        files = os.listdir(self.test_export_dir)
        self.assertEqual(len(files), 1)

        # 2. Simulate Transfer (Copy from export to import)
        src = os.path.join(self.test_export_dir, files[0])
        dst = os.path.join(self.test_import_dir, files[0])
        shutil.copy(src, dst)

        # 3. Import (New engine instance to simulate peer)
        peer_engine = P2PSyncEngine()
        peer_engine.export_dir = self.test_export_dir
        peer_engine.import_dir = self.test_import_dir

        count = peer_engine.import_threat_dna()
        self.assertEqual(count, 1)

        import hashlib
        expected_hash = hashlib.sha256("bad_signature_123".encode()).hexdigest()
        self.assertTrue(any(t.signature_hash == expected_hash for t in peer_engine.known_threats.values()))

if __name__ == '__main__':
    unittest.main()
