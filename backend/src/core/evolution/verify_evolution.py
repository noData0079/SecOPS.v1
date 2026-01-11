
import unittest
import os
import shutil
import logging
from datetime import datetime, timedelta
from backend.src.core.evolution.meta_compiler import MetaCompiler
from backend.src.core.evolution.pattern_learner import PatternLearner, LogEntry
from backend.src.core.memory.policy_memory import PolicyMemory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyEvolution")

class TestEvolution(unittest.TestCase):

    def setUp(self):
        # Setup paths
        self.base_path = "backend/src/core/evolution"
        self.dummy_path = f"{self.base_path}/dummy_slow.py"
        self.test_path = f"{self.base_path}/tests/test_dummy_slow.py"

        # Reset dummy_slow.py to original slow state
        with open(self.dummy_path, 'w') as f:
            f.write("""
import time

def slow_sum(n):
    \"\"\"
    Calculates the sum of numbers from 0 to n-1 using a nested loop.
    This is intentionally O(n^2) for demonstration purposes.
    \"\"\"
    total = 0
    for i in range(n):
        for j in range(n):
            if i == j:
                total += i
    return total
""")

    def test_meta_compiler_generic(self):
        logger.info("Testing Meta-Compiler (Generic Strategy)...")

        # Define a custom strategy for this test
        def test_strategy(source, name):
            if name == "slow_sum":
                return """
import time

def slow_sum(n):
    \"\"\"
    Calculates the sum of numbers from 0 to n-1.
    Optimized by Meta-Compiler to O(1).
    \"\"\"
    if n <= 0:
        return 0
    return (n * (n - 1)) // 2
"""
            return source

        compiler = MetaCompiler(optimization_strategy=test_strategy)

        # Run Hot Swap
        compiler.hot_swap(self.dummy_path, self.test_path)

        # Verify content is now optimized
        with open(self.dummy_path, 'r') as f:
            content = f.read()
            self.assertIn("(n * (n - 1)) // 2", content)

        logger.info("Meta-Compiler generic test passed.")

    def test_pattern_learner_timing(self):
        logger.info("Testing Pattern Learner Timing Logic...")

        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp_dir:
            pm = PolicyMemory(storage_path=Path(tmp_dir))
            learner = PatternLearner(pm)

            base_time = datetime.now()

            # Scenario 1: Valid Pattern (Failure 90s after spike)
            learner.ingest_observations([
                LogEntry(source="db", metric="io_wait", value=0.9, timestamp=base_time, context={}),
                LogEntry(source="web_server_b", metric="status", value=500, timestamp=base_time + timedelta(seconds=90), context={})
            ])

            axioms = learner.extract_axioms()
            self.assertEqual(len(axioms), 1, "Should detect pattern within 2 min window")
            self.assertEqual(axioms[0]['cause'], "db.io_wait > 0.8")

    def test_pattern_learner_negative(self):
        logger.info("Testing Pattern Learner Negative Logic...")
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp_dir:
            pm = PolicyMemory(storage_path=Path(tmp_dir))
            learner = PatternLearner(pm)

            base_time = datetime.now()

            # Scenario 2: Invalid Pattern (Failure 5 mins after spike - too late)
            learner.observations = [] # Reset
            learner.ingest_observations([
                LogEntry(source="db", metric="io_wait", value=0.9, timestamp=base_time, context={}),
                LogEntry(source="web_server_b", metric="status", value=500, timestamp=base_time + timedelta(minutes=5), context={})
            ])

            axioms = learner.extract_axioms()
            self.assertEqual(len(axioms), 0, "Should NOT detect pattern outside 2 min window")

            # Scenario 3: Invalid Pattern (Failure BEFORE spike)
            learner.observations = [] # Reset
            learner.ingest_observations([
                LogEntry(source="web_server_b", metric="status", value=500, timestamp=base_time, context={}),
                LogEntry(source="db", metric="io_wait", value=0.9, timestamp=base_time + timedelta(seconds=10), context={})
            ])

            axioms = learner.extract_axioms()
            self.assertEqual(len(axioms), 0, "Should NOT detect pattern if effect precedes cause")

            logger.info("Pattern Learner negative tests passed.")

if __name__ == '__main__':
    unittest.main()
