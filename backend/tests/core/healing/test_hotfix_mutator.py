
import pytest
import os
from unittest.mock import MagicMock, patch
from backend.src.core.healing.hotfix_mutator import HotFixMutator, Anomaly

class TestHotFixMutator:

    @pytest.fixture
    def mutator(self):
        return HotFixMutator()

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

    @patch("backend.src.core.healing.hotfix_mutator.SemanticStore")
    def test_hypothesize(self, MockSemanticStore, mutator):
        # Mock SemanticStore behavior
        mutator.semantic_store.search_facts = MagicMock(return_value=[
            MagicMock(content="Fix memory leak by pruning cache")
        ])

        anomaly = Anomaly(type="memory_leak", source="nginx", metric="ram", value="1GB")
        facts = mutator.hypothesize(anomaly)

        assert len(facts) == 1
        assert facts[0].content == "Fix memory leak by pruning cache"
        mutator.semantic_store.search_facts.assert_called_with("memory_leak nginx fix")

    def test_synthesize_fallback(self, mutator):
        # Test fallback logic when ScriptGenerator returns empty (default stub)
        anomaly = Anomaly(type="memory_leak", source="nginx", metric="ram", value="1GB")
        script = mutator.synthesize(anomaly, [])

        assert "#!/bin/bash" in script
        assert "Hotfix: Prune cache" in script
        assert "nginx" in script

    def test_validate(self, mutator):
        anomaly = Anomaly(type="memory_leak", source="nginx", metric="ram", value="1GB")
        script = "echo 'test'"

        # Sandbox stub returns {} which is considered success in validation logic
        valid = mutator.validate(script, anomaly)
        assert valid is True

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
        # Ensure TTL is inserted at top (checking if it appears before echo)
        ttl_index = content.find("# TTL Enforcement")
        echo_index = content.find("echo 'hello'")
        assert ttl_index < echo_index
        assert "sleep 3600" in content
        assert "rm -- \"$0\"" in content

    def test_apply_creates_python_file_with_ttl(self, mutator, tmp_path):
        # Use tmp_path fixture for safe file testing
        script = "#!/usr/bin/env python3\nprint('hello')"
        fix_id = mutator.apply(script, "nginx", ttl_hours=1, deploy_path=tmp_path)

        assert fix_id is not None

        expected_path = tmp_path / f"hotfix_{fix_id}.py"
        assert expected_path.exists()

        content = expected_path.read_text()
        assert "print('hello')" in content
        assert "import os" in content
        assert "import subprocess" in content
        assert "sleep 3600" in content

        # Ensure TTL is inserted at top (after shebang)
        ttl_index = content.find("import subprocess")
        print_index = content.find("print('hello')")
        assert ttl_index < print_index

    @patch("backend.src.core.healing.hotfix_mutator.subprocess.Popen")
    def test_apply_executes_script(self, mock_popen, mutator, tmp_path):
        script = "#!/bin/bash\necho 'hello'"
        mutator.apply(script, "nginx", ttl_hours=1, deploy_path=tmp_path)

        # Check if subprocess.Popen was called
        assert mock_popen.called

    def test_generate_memory_prune_script_sanitization(self, mutator):
        # Test sanitization
        unsafe_target = "../../../etc/passwd"
        script = mutator._generate_memory_prune_script(unsafe_target)

        assert unsafe_target not in script
        assert "unknown_service" in script

        safe_target = "nginx-service_v1"
        script = mutator._generate_memory_prune_script(safe_target)
        assert safe_target in script

    def test_resolve_pain_point_full_flow(self, mutator, tmp_path):
        context = {
            "type": "memory_leak",
            "source": "redis",
            "metric": "ram",
            "value": "2GB"
        }

        # Patch the default path in apply method or ensure validation allows logic flow
        # We can't easily patch the default arg but we can mock apply or just let it write to /tmp/tsm99/hotfixes
        # Ideally, we should inject the path into the mutator or methods.
        # Since 'resolve_pain_point' calls 'apply' without path arg, it uses default.
        # We will mock the 'apply' method to verify it's called or use a patch on Path inside the module if strict.
        # For integration test, we can check if it returns an ID.

        # To avoid side effects in /tmp, let's mock the apply method partially or just check success.
        # But we want to test the full flow.

        # Let's monkeypatch HotFixMutator.apply to use tmp_path
        original_apply = mutator.apply
        mutator.apply = lambda s, t, ttl=1: original_apply(s, t, ttl, deploy_path=tmp_path)

        fix_id = mutator.resolve_pain_point(context)
        assert fix_id is not None

        filepath = tmp_path / f"hotfix_{fix_id}.sh"
        assert filepath.exists()
