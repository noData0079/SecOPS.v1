import pytest
import shutil
import os
import time
from backend.src.core.evolution.meta_compiler import MetaCompiler

@pytest.fixture
def temp_test_dir(tmp_path):
    d = tmp_path / "test_evolution"
    d.mkdir()
    return d

def test_meta_compiler_optimization(temp_test_dir):
    # 1. Create a slow script
    slow_script = temp_test_dir / "slow_module.py"
    slow_script.write_text("""
def slow_sum(n):
    total = 0
    for i in range(n):
        for j in range(1): # Dummy inner loop
            total += i
    return total
""")

    # 2. Create a test for it
    test_script = temp_test_dir / "test_slow.py"
    test_script.write_text(f"""
import sys
import os
sys.path.append('{str(temp_test_dir)}')
from slow_module import slow_sum
import unittest

class TestSlow(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(slow_sum(10), 45)

if __name__ == '__main__':
    unittest.main()
""")

    compiler = MetaCompiler()

    # 3. Benchmark before (mocked or real)
    # We rely on the internal logic of hot_swap to run benchmarks

    # 4. Trigger hot_swap
    compiler.hot_swap(str(slow_script), str(test_script))

    # 5. Check if code was updated
    new_code = slow_script.read_text()
    assert "Optimized by Meta-Compiler" in new_code
    assert "n * (n - 1)" in new_code

def test_meta_compiler_revert_on_failure(temp_test_dir):
    # Create a script that "optimizes" to broken code
    broken_script = temp_test_dir / "broken_module.py"
    broken_script.write_text("""
def slow_sum(n):
    return sum(range(n))
""")

    test_script = temp_test_dir / "test_broken.py"
    test_script.write_text(f"""
import sys
sys.path.append('{str(temp_test_dir)}')
from broken_module import slow_sum
import unittest

class TestBroken(unittest.TestCase):
    def test_sum(self):
        self.assertEqual(slow_sum(10), 45)

if __name__ == '__main__':
    unittest.main()
""")

    # Override optimization strategy to return broken code
    def broken_strategy(source, func_name):
        return "def slow_sum(n): return 0 # Broken"

    compiler = MetaCompiler(optimization_strategy=broken_strategy)
    compiler.analyze_module = lambda x: "slow_sum" # Force analysis success

    compiler.hot_swap(str(broken_script), str(test_script))

    # Should revert
    content = broken_script.read_text()
    assert "sum(range(n))" in content
    assert "return 0 # Broken" not in content

def test_outdated_libraries():
    compiler = MetaCompiler()
    outdated = compiler.check_outdated_libraries()
    assert "requests" in outdated
