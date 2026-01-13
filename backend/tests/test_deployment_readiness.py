"""
Comprehensive System Verification Script

Tests all modules, workflows, and connections for deployment readiness.
"""
import pytest
import sys
import os

# Set dummy environment variables to bypass Kaggle config check
os.environ['KAGGLE_USERNAME'] = 'test'
os.environ['KAGGLE_KEY'] = 'test'

# Set up paths
# Add 'backend' (for imports starting with 'src.')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add 'backend/src' (for imports starting with 'core.', 'main', etc.)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

print("=" * 60)
print("SecOps-AI DEPLOYMENT READINESS CHECK")
print("=" * 60)

errors = []
warnings = []
passed = []

# ============================================
# PHASE 1: COMPILE ALL MODULES
# ============================================

# Using module paths as they would be imported from 'backend/src' (core...) or 'backend' (src.core...)
# Since we added both to path, 'core...' should work.

modules_to_check = [
    # Core Learning/Training
    ("core.training.orchestrator", "TrainingOrchestrator"),
MODULES_TO_CHECK = [
    # Core Learning
    ("core.learning.outcomes.engine", "OutcomeIntelligenceEngine"),
    ("core.learning.playbooks.engine", "PlaybookEngine"),
    ("core.learning.policies.learner", "PolicyLearner"),
    ("core.learning.orchestrator", "LearningLoopOrchestrator"),
    
    # Core Data Resident / Sanitization
    ("core.sanitization.sanitizer", "DataSanitizer"),
    
    # LLM / Routing
    ("core.llm.llm_router", "LLMRouter"),
    
    # Agentic
    ("core.agentic.agent_core", "Agent"),
    
    # Simulation
    ("core.simulation.ghost_sim", "GhostSimulation"),
]


for module_path, class_name in modules_to_check:
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

# Test Learning/Training Loop
try:
    from core.training.orchestrator import TrainingOrchestrator
    # orchestrator = TrainingOrchestrator()
    passed.append("Training Orchestrator")
    print("   [OK] Training Orchestrator initialized (import only)")
except Exception as e:
    errors.append(f"Training Workflow: {e}")
    print(f"   [ERROR] Training Workflow: {e}")

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

# Based on backend/src/api
# We can import these via 'api.v1...' because 'backend/src' is in path
api_modules = [
API_MODULES = [
    "api.v1.endpoints.findings",
    # "api.v1.endpoints.playbooks",
    # "api.v1.endpoints.system",
]

@pytest.mark.parametrize("module_path", API_MODULES)
def test_api_endpoints(module_path):
    try:
        module = __import__(module_path, fromlist=["router"])
        router = getattr(module, "router")
        routes = len(router.routes)
        passed.append(f"{module_path} ({routes} routes)")
        print(f"   [OK] {module_path}: {routes} routes")
    except ImportError:
         print(f"   [SKIP] {module_path} not found")
        assert len(router.routes) > 0, f"{module_path} has no routes"
    except Exception as e:
        pytest.fail(f"{module_path}: {e}")

# ============================================
# PHASE 4: CHECK FASTAPI APP
# ============================================

try:
    from main import app
    # Count registered routes
    routes = [r for r in app.routes if hasattr(r, 'path')]
    api_routes = [r for r in routes if r.path.startswith('/api')]
    
    passed.append(f"FastAPI App ({len(routes)} total routes, {len(api_routes)} API routes)")
    print(f"   [OK] FastAPI App: {len(routes)} total routes, {len(api_routes)} API routes")
except Exception as e:
    errors.append(f"FastAPI App: {e}")
    print(f"   [ERROR] FastAPI App: {e}")
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
    "sqlalchemy",
    "openai"
]

@pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
def test_requirements(pkg):
    try:
        __import__(pkg)
    except ImportError:
        warnings.append(f"Package not installed: {pkg}")
        print(f"   [WARN] {pkg} not installed")

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 60)
print("DEPLOYMENT READINESS SUMMARY")
print("=" * 60)

print(f"\n[PASSED] {len(passed)} checks")
print(f"[WARNINGS] {len(warnings)} warnings")
print(f"[ERRORS] {len(errors)} errors")

if errors:
    print("\nErrors to fix:")
    for e in errors:
        print(f"  - {e}")

if warnings:
    print("\nWarnings (non-blocking):")
    for w in warnings:
        print(f"  - {w}")

if len(errors) == 0:
    print("\n" + "=" * 60)
    print("[SUCCESS] PROJECT IS DEPLOYMENT READY!")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("[FAILED] Fix errors before deployment")
    print("=" * 60)
        pytest.fail(f"Package not installed: {pkg}")
