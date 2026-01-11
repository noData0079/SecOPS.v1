import unittest
import shutil
import json
from pathlib import Path
from datetime import datetime
from backend.src.core.autonomy.replay import ReplayEngine

class TestReplayEngine(unittest.TestCase):
    def setUp(self):
        self.storage_path = Path("backend/tests/replay_engine_tmp")
        self.engine = ReplayEngine(self.storage_path)

    def tearDown(self):
        if self.storage_path.exists():
            shutil.rmtree(self.storage_path)

    def test_store_and_load(self):
        """Test storing and loading replay records."""
        record = self.engine.store(
            incident_id="inc_123",
            actions=[{"tool": "test", "args": {}}],
            outcome="resolved",
            resolution_time_seconds=60
        )

        self.assertEqual(len(self.engine.records), 1)
        self.assertEqual(self.engine.records[0].incident_id, "inc_123")

        # reload
        new_engine = ReplayEngine(self.storage_path)
        self.assertEqual(len(new_engine.records), 1)
        self.assertEqual(new_engine.records[0].incident_id, "inc_123")

    def test_analyze_patterns(self):
        """Test pattern analysis."""
        self.engine.store(
            incident_id="inc_1",
            actions=[{"tool": "t1"}],
            outcome="resolved",
            resolution_time_seconds=10
        )
        self.engine.store(
            incident_id="inc_2",
            actions=[{"tool": "t1"}, {"tool": "t2"}],
            outcome="failed",
            resolution_time_seconds=20
        )

        patterns = self.engine.analyze_patterns()

        self.assertEqual(patterns["total_incidents"], 2)
        self.assertEqual(patterns["resolution_rate"], 0.5)
        self.assertEqual(patterns["most_used_tools"][0][0], "t1") # t1 used twice

if __name__ == "__main__":
    unittest.main()
