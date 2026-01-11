
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import os
from core.economics.governor import EconomicGovernor
from core.llm.llm_router import LLMRouter, TaskType
from core.economics.resource_arbiter import ResourceArbiter
from core.memory.economic_memory import EconomicMemory, CostBudget

class TestEconomicGovernor:
    def test_evaluate_model_tier(self):
        governor = EconomicGovernor()

        # Test default behavior
        assert governor.evaluate_model_tier("critical") == "high_tier"
        assert governor.evaluate_model_tier("high") == "high_tier"
        assert governor.evaluate_model_tier("medium") == "low_tier"
        assert governor.evaluate_model_tier("low") == "low_tier"

    def test_evaluate_model_tier_budget_constrained(self):
        memory = MagicMock(spec=EconomicMemory)
        budget = MagicMock(spec=CostBudget)
        budget.daily_remaining = 1.0 # Very low budget
        memory.get_budget.return_value = budget

        governor = EconomicGovernor(economic_memory=memory)

        # Should downgrade high severity tasks
        assert governor.evaluate_model_tier("critical", tenant_id="test_tenant") == "low_tier"
        assert governor.evaluate_model_tier("high", tenant_id="test_tenant") == "low_tier"

class TestLLMRouterIntegration:
    @patch("core.llm.llm_router.economic_governor")
    def test_select_model_integration(self, mock_governor):
        router = LLMRouter(enable_data_isolation=False)

        # Mock governor to return specific tiers
        mock_governor.evaluate_model_tier.return_value = "high_tier"

        # Should pick high tier model for openai
        model = router._select_model(TaskType.GENERAL, "openai", incident_severity="critical", tenant_id="test_tenant")
        mock_governor.evaluate_model_tier.assert_called_with("critical", "test_tenant")
        assert model == "gpt-4-turbo-preview"

        # Mock governor to return low tier
        mock_governor.evaluate_model_tier.return_value = "low_tier"
        model = router._select_model(TaskType.GENERAL, "openai", incident_severity="low", tenant_id="test_tenant")
        mock_governor.evaluate_model_tier.assert_called_with("low", "test_tenant")
        assert model == "gpt-3.5-turbo"

class TestResourceArbiter:
    def test_monitor_resources_critical(self, tmp_path):
        # Create a simulation file
        sim_file = tmp_path / "gpu_usage"
        sim_file.write_text("95.0")

        arbiter = ResourceArbiter(simulation_file=sim_file)
        status = arbiter.monitor_resources()

        assert status.is_critical_state is True
        assert status.gpu_memory_used_percent == 95.0

    def test_monitor_resources_normal(self, tmp_path):
        sim_file = tmp_path / "gpu_usage"
        sim_file.write_text("50.0")

        arbiter = ResourceArbiter(simulation_file=sim_file)
        status = arbiter.monitor_resources()

        assert status.is_critical_state is False

    def test_should_allow_task(self, tmp_path):
        sim_file = tmp_path / "gpu_usage"
        sim_file.write_text("95.0") # Critical

        arbiter = ResourceArbiter(simulation_file=sim_file)

        # Should allow critical tasks
        assert arbiter.should_allow_task("security") is True
        assert arbiter.should_allow_task("sovereign_core") is True

        # Should deny non-critical tasks
        assert arbiter.should_allow_task("general") is False
        assert arbiter.should_allow_task("logging") is False
