
import pytest
import os
import shutil
import tempfile
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.llm.tree_of_thought import TreeOfThought
from src.core.security.tpm_handler import TPMHandler
from src.core.outcomes.backtrack import BacktrackHandler
from src.core.outcomes.scorer import OutcomeScore, OutcomeCategory
from src.core.llm.llm_router import TaskType

# Mock LLMRouter
class MockLLMRouter:
    def __init__(self):
        self.generate = AsyncMock()

@pytest.fixture
def mock_llm_router():
    router = MockLLMRouter()
    # Set up default return for generate
    router.generate.return_value = MagicMock(content="Test Opinion")
    return router

@pytest.mark.asyncio
async def test_tree_of_thought(mock_llm_router):
    tot = TreeOfThought(llm_router=mock_llm_router)

    prompt = "Should we deploy to production?"
    result = await tot.reason_with_experts(prompt)

    assert "final_decision" in result
    assert "expert_opinions" in result
    assert len(result["expert_opinions"]) == 5

    # Verify calls were made
    assert mock_llm_router.generate.call_count >= 6 # 5 experts + 1 synthesis

def test_tpm_handler_signature():
    handler = TPMHandler(use_simulation=True)

    data = {"policy_id": "123", "rules": ["no_network"]}
    signature = handler.sign_policy_memory(data)

    assert isinstance(signature, str)
    assert len(signature) == 64 # SHA256 hex digest

    # Verify works
    assert handler.verify_policy_memory(data, signature) is True

    # Verify tamper resistance
    tampered_data = {"policy_id": "123", "rules": ["allow_all"]}
    assert handler.verify_policy_memory(tampered_data, signature) is False

def test_backtrack_handler():
    handler = BacktrackHandler(threshold=20.0)

    # Create a temporary git repo
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git
        os.system(f"git init {tmpdir}")
        os.system(f"cd {tmpdir} && git config user.email 'you@example.com' && git config user.name 'Your Name'")

        # Create initial commit
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Initial state")
        os.system(f"cd {tmpdir} && git add . && git commit -m 'Initial'")

        # Create a bad UNCOMMITTED change (simulating a failed action that did NOT commit)
        # Since we changed the logic to only `git reset --hard HEAD`, we test that behavior.
        with open(test_file, "w") as f:
            f.write("Bad state")
        # Do not commit

        # Create a low outcome score
        score = OutcomeScore(
            score=0.0,
            category=OutcomeCategory.FAILURE,
            confidence=1.0
        )

        # Trigger backtrack
        result = handler.handle_outcome(score, tmpdir)

        assert result is True

        # Verify revert happened (should have a new commit reverting the bad one)
        # The content should be back to "Initial state"
        with open(test_file, "r") as f:
            content = f.read()

        assert content == "Initial state"
