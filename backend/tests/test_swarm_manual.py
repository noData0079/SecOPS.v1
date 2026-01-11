
import asyncio
import logging
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from core.llm.swarm_orchestrator import SwarmOrchestrator
from core.llm.local_provider import LocalLLMProvider
from core.memory.semantic_store import SemanticStore
from core.economics.governor import EconomicGovernor
from core.tools.tool_success_map import ToolSuccessMap

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_swarm():
    logger.info("Starting Swarm Test...")

    # Mock Dependencies
    mock_provider = MagicMock(spec=LocalLLMProvider)
    mock_semantic_store = MagicMock(spec=SemanticStore)
    mock_governor = MagicMock(spec=EconomicGovernor)
    mock_success_map = MagicMock(spec=ToolSuccessMap)

    # Mock Methods
    mock_provider.generate = AsyncMock(return_value="[MOCKED RESPONSE]")
    mock_semantic_store.summarize.return_value = {"total_facts": 10}
    mock_semantic_store.facts = {} # Empty dict for recent facts
    mock_governor.check_budget_health.return_value = {"status": "healthy"}
    mock_success_map.get_summary.return_value = {"total_tools": 5}

    # Mock specific responses based on system prompt or prompt
    async def mock_generate(prompt, system_prompt=None, **kwargs):
        if "Forensic Agent" in str(system_prompt):
            return "FORENSIC REPORT: Timeline reconstructed."
        elif "Policy Auditor" in str(system_prompt):
            return "AUDIT REPORT: No bypasses found."
        elif "Tool Architect" in str(system_prompt):
            return "```python\ndef new_tool(): pass\n```"
        elif "json_mode" in kwargs and kwargs["json_mode"]:
            return '{"tool": "check_logs", "args": {}}'
        return "Generic response"

    mock_provider.generate.side_effect = mock_generate

    # Instantiate Swarm with mocks
    swarm = SwarmOrchestrator(
        provider=mock_provider,
        semantic_store=mock_semantic_store,
        governor=mock_governor,
        success_map=mock_success_map
    )

    # Test 1: Forensic Delegation
    logger.info("Test 1: Forensic Delegation")
    res1 = await swarm.route_request("Please analyze the semantic store for the recent incident timeline.", {})
    logger.info(f"Result 1: {res1}")
    assert res1["tool"] == "report_agent_outcome"
    assert "FORENSIC REPORT" in res1["args"]["content"]
    mock_semantic_store.summarize.assert_called()

    # Test 2: Auditor Delegation
    logger.info("Test 2: Auditor Delegation")
    res2 = await swarm.route_request("Audit the current budget and look for bypasses.", {})
    logger.info(f"Result 2: {res2}")
    assert res2["tool"] == "report_agent_outcome"
    assert "AUDIT REPORT" in res2["args"]["content"]
    mock_governor.check_budget_health.assert_called()

    # Test 3: Architect Delegation
    logger.info("Test 3: Architect Delegation")
    res3 = await swarm.route_request("We need a new python script to handle XYZ.", {})
    logger.info(f"Result 3: {res3}")
    assert res3["tool"] == "report_agent_outcome"
    assert "def new_tool" in res3["args"]["content"]
    mock_success_map.get_summary.assert_called()

    # Test 4: Generalist Fallback
    logger.info("Test 4: Generalist Fallback")
    res4 = await swarm.route_request("Check the logs for errors.", {})
    logger.info(f"Result 4: {res4}")
    assert res4["tool"] == "check_logs"

    logger.info("All tests passed!")

if __name__ == "__main__":
    asyncio.run(test_swarm())
