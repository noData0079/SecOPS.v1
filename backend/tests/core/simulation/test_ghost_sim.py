import pytest
from unittest.mock import MagicMock
from backend.src.core.simulation.digital_twin import DigitalTwinManager, GhostEnvironment
from backend.src.core.simulation.ghost_sim import GhostSimulation
from backend.src.core.simulation.mcts_engine import MCTSEngine

def test_digital_twin_manager():
    manager = DigitalTwinManager()
    env = manager.clone_subsystem("api_gateway")
    assert isinstance(env, GhostEnvironment)
    assert env.impact_area == "api_gateway"
    assert len(manager.active_twins) == 1

def test_ghost_environment_stress_test():
    env = GhostEnvironment("db_shard")
    env.apply_patch("hash123")
    results = env.run_stress_test(5)

    assert results.success_rate > 0.9
    assert "Applied patch hash123" in results.logs[0]

def test_ghost_simulation_validation():
    manager = DigitalTwinManager()
    ghost_sim = GhostSimulation(manager)

    # Mock result
    result = ghost_sim.validate_evolution("hash123", "network_layer")

    # Check if logic passed (default mocked values in DigitalTwin pass)
    assert result["status"] == "GREEN"
    assert result["score"] >= 0.95

def test_mcts_engine():
    engine = MCTSEngine(simulation_budget=10)
    initial_state = {"latency": 10, "error_rate": 0.0}
    proposed_change = {"latency_optimization": True}

    result = engine.simulate_change(initial_state, proposed_change)
    assert "recommended" in result
    assert "safety_score" in result
