
import pytest
import os
from unittest.mock import MagicMock, patch
from backend.src.core.healing.hotfix_mutator import HotFixMutator, Anomaly

class TestHotFixMutator:

    @pytest.fixture
    def mock_deps(self):
        return {
            "script_generator": MagicMock(),
            "ghost_sim": MagicMock(),
            "sandbox": MagicMock()
        }

    @pytest.fixture
    def mutator(self, mock_deps):
        mutator = HotFixMutator(
            script_generator=mock_deps["script_generator"],
            ghost_sim=mock_deps["ghost_sim"],
            sandbox=mock_deps["sandbox"]
        )
        # Mock ghost simulation to return success by default
        mock_deps["ghost_sim"].simulate_scenario.return_value = {"outcome": "success"}
        # Mock sandbox to return success
        mock_deps["sandbox"].run_tool.return_value = {}
        return mutator

    def test_identify_anomaly(self, mutator):
        context = {
            "type": "memory_leak",
            "source": "nginx",
            "metric": "ram",
            "value": "1GB"
        }
        anomaly = mutator.identify(context)
        assert isinstance(anomaly, Anomaly)
        assert anomaly.type == "memory_leak"
        assert anomaly.source == "nginx"

    def test_evolve_solution_generates_script(self, mutator, mock_deps):
        # Setup mocks
        mock_deps["script_generator"].generate_tool.return_value = "#!/bin/bash\nclean_cache"

        anomaly = Anomaly(type="memory_leak", source="nginx", metric="ram", value="1GB", metadata={})
        best_script = mutator.evolve_solution(anomaly)

        assert best_script is not None
        # Should return one of the seeds or mutated versions
        # Our mock generator returned a script, so it should be in population
        # and likely chosen if fitness is good.
        # The simple fitness function rewards "nginx" in script (source match).
        # "#!/bin/bash\nclean_cache" doesn't have "nginx".
        # But "restart nginx" seed does.
        # So "restart nginx" might win.
        assert "nginx" in best_script or "clean_cache" in best_script

    def test_validate(self, mutator, mock_deps):
        anomaly = Anomaly(type="memory_leak", source="nginx", metric="ram", value="1GB", metadata={})
        script = "echo 'test'"

        # Sandbox stub returns {} which is considered success in validation logic
        valid = mutator.validate(script, anomaly)
        assert valid is True
        mock_deps["sandbox"].run_tool.assert_called_once()

    def test_apply_creates_file_with_ttl(self, mutator, tmp_path):
        # Use tmp_path fixture for safe file testing
        script = "#!/bin/bash\necho 'hello'"
        fix_id = mutator.apply(script, "nginx", ttl_hours=1, deploy_path=tmp_path)

        assert fix_id is not None

        expected_path = tmp_path / f"hotfix_{fix_id}.sh"
        assert expected_path.exists()

        content = expected_path.read_text()
        assert "echo 'hello'" in content
        assert "# TTL Enforcement" in content
        assert "sleep 3600" in content
        assert "rm -- \"$0\"" in content

    @patch("backend.src.core.healing.hotfix_mutator.subprocess.Popen")
    def test_apply_executes_script(self, mock_popen, mutator, tmp_path):
        script = "#!/bin/bash\necho 'hello'"
        mutator.apply(script, "nginx", ttl_hours=1, deploy_path=tmp_path)

        # Check if subprocess.Popen was called
        assert mock_popen.called

    def test_resolve_pain_point_full_flow(self, mutator, mock_deps, tmp_path):
        context = {
            "type": "memory_leak",
            "source": "redis",
            "metric": "ram",
            "value": "2GB"
        }

        # Mock generator to return a valid script containing the source name for higher fitness
        mock_deps["script_generator"].generate_tool.return_value = "#!/bin/bash\necho 'fixing redis'"

        # Monkeypatch apply to use tmp_path
        original_apply = mutator.apply
        mutator.apply = lambda s, t, ttl=1: original_apply(s, t, ttl, deploy_path=tmp_path)

        fix_id = mutator.resolve_pain_point(context)

        assert fix_id is not None
        mock_deps["ghost_sim"].simulate_scenario.assert_called_once()

        filepath = tmp_path / f"hotfix_{fix_id}.sh"
        assert filepath.exists()
