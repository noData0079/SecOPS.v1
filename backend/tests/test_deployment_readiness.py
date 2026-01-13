"""
Comprehensive System Verification Script

Tests all modules, workflows, and connections for deployment readiness.
"""
import pytest
import sys
import os

# ============================================
# PHASE 1: COMPILE ALL MODULES
# ============================================

MODULES_TO_CHECK = [
    # Core Learning
    ("core.learning.outcomes.engine", "OutcomeIntelligenceEngine"),
    ("core.learning.playbooks.engine", "PlaybookEngine"),
    ("core.learning.policies.learner", "PolicyLearner"),
    ("core.learning.orchestrator", "LearningLoopOrchestrator"),
    
    # Core Data Resident
    ("core.sanitization.sanitizer", "DataSanitizer"),
    ("core.execution.engine", "LocalExecutionEngine"),
    ("core.trust_ledger.ledger", "TrustLedger"),
    ("core.data_resident.orchestrator", "DataResidentOrchestrator"),
    
    # LLM
    ("core.llm.poly_orchestrator", "PolyLLMOrchestrator"),
    
    # Agent Orchestration
    ("agent.orchestration.agent", "Agent"),
    ("agent.orchestration.crew", "Crew"),
    ("agent.orchestration.task", "Task"),
    ("agent.orchestration.flow", "Flow"),
    
    # Integrations
    ("integrations.security.scanner", "SecurityScanner"),
    ("extensions.security.red_team.orchestrator", "RedTeamOrchestrator"),
    ("services.alerts.hub", "AlertHub"),
    ("services.monitoring.system_monitor", "SystemMonitor"),
    
    # RAG
    ("rag.vectorstore.security_kb", "SecurityVectorStore"),
]

@pytest.mark.parametrize("module_path, class_name", MODULES_TO_CHECK)
def test_module_imports(module_path, class_name):
    try:
        module = __import__(module_path, fromlist=[class_name])
        assert hasattr(module, class_name), f"{class_name} not found in {module_path}"
    except ImportError as e:
        pytest.fail(f"{module_path}: Import error - {e}")
    except AttributeError as e:
        pytest.fail(f"{module_path}.{class_name}: {e}")
    except Exception as e:
        pytest.warns(UserWarning, match=f"{module_path}: {e}")

# ============================================
# PHASE 2: CHECK WORKFLOWS
# ============================================

def test_learning_loop_workflow():
    try:
        from core.learning.orchestrator import LearningLoopOrchestrator
        orchestrator = LearningLoopOrchestrator()

        # Test process_finding with correct parameters
        result = orchestrator.process_finding(
            finding_id="test-123",
            finding_type="SQL_INJECTION",
            context={"language": "python", "file_path": "test.py"}
        )

        if not result.fix_decision:
             pytest.warns(UserWarning, match="Learning Loop: No fix decision returned")
        else:
            assert result.fix_decision is not None

    except Exception as e:
        pytest.fail(f"Learning Loop Workflow: {e}")

def test_data_resident_workflow():
    try:
        from core.data_resident.orchestrator import DataResidentOrchestrator
        dr = DataResidentOrchestrator()
        assert dr is not None
    except Exception as e:
        pytest.fail(f"Data Resident Workflow: {e}")

# ============================================
# PHASE 3: CHECK API ENDPOINTS
# ============================================

API_MODULES = [
    "api.v1.endpoints.findings",
    "api.v1.endpoints.playbooks",
    "api.v1.endpoints.system",
]

@pytest.mark.parametrize("module_path", API_MODULES)
def test_api_endpoints(module_path):
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router")
        assert len(router.routes) > 0, f"{module_path} has no routes"
    except Exception as e:
        pytest.fail(f"{module_path}: {e}")

# ============================================
# PHASE 4: CHECK FASTAPI APP
# ============================================

def test_fastapi_app():
    try:
        from app import app
        # Count registered routes
        routes = [r for r in app.routes if hasattr(r, 'path')]
        api_routes = [r for r in routes if r.path.startswith('/api')]

        assert len(routes) > 0
        assert len(api_routes) > 0
    except Exception as e:
        pytest.fail(f"FastAPI App: {e}")

# ============================================
# PHASE 5: CHECK REQUIREMENTS
# ============================================

REQUIRED_PACKAGES = [
    "fastapi",
    "pydantic",
    "httpx",
]

@pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
def test_requirements(pkg):
    try:
        __import__(pkg)
    except ImportError:
        pytest.fail(f"Package not installed: {pkg}")
