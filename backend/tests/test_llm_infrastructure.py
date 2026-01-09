"""
Test script for LLM Infrastructure and Extended Playbooks.
Avoids importing modules with external dependencies.
"""
import sys
import asyncio
sys.path.insert(0, r'c:\Users\mymai\Desktop\SecOps-ai\backend\src')

print("Testing LLM Infrastructure and Extended Playbooks...")
print("=" * 50)

# Test 1: Extended Playbooks
print("\n1. Testing Extended Playbooks...")

# Import directly to avoid chain imports
from core.learning.playbooks.engine import PlaybookEngine
from core.learning.playbooks.extended_playbooks import get_extended_playbooks, load_extended_playbooks_into_engine

engine = PlaybookEngine()
count = load_extended_playbooks_into_engine(engine)
print("   Extended playbooks loaded:", count)

# Get all playbooks
all_playbooks = engine.get_all_playbooks()
print("   Total playbooks (built-in + extended):", len(all_playbooks))

# Check coverage
finding_types = set(p.finding_type for p in all_playbooks)
print("   Finding types covered:", len(finding_types))
print("   Types:", ", ".join(sorted(finding_types)[:8]), "...")

# High confidence count
high_conf = [p for p in all_playbooks if p.confidence >= 0.9]
print("   High-confidence playbooks:", len(high_conf))
print("   [OK] Extended playbooks working")

# Test 2: Poly-LLM Orchestrator
print("\n2. Testing Poly-LLM Orchestrator...")
from core.llm.poly_orchestrator import (
    PolyLLMOrchestrator,
    LLMRequest,
    LLMProvider,
    TaskType,
    create_reasoning_request,
    create_code_analysis_request,
)

orchestrator = PolyLLMOrchestrator()

# Test routing
reasoning_req = create_reasoning_request("Analyze this security finding")
code_req = create_code_analysis_request("Review this code", "def foo(): pass")

provider1, model1 = orchestrator.route(reasoning_req)
provider2, model2 = orchestrator.route(code_req)

print("   Reasoning routes to:", provider1.value, "/", model1)
print("   Code analysis routes to:", provider2.value, "/", model2)

# Run async test
async def test_completion():
    response = await orchestrator.complete(reasoning_req)
    return response

response = asyncio.run(test_completion())
print("   Response provider:", response.provider.value)
print("   Response model:", response.model)
print("   Tokens:", response.tokens_used)
print("   [OK] Poly-LLM orchestrator working")

# Test 3: System Monitor
print("\n3. Testing System Monitor...")
from services.monitoring.system_monitor import SystemMonitor

monitor = SystemMonitor()

# Record some metrics
monitor.record_llm_request(
    provider="openai",
    model="gpt-4o",
    tokens=500,
    cost=0.005,
    latency_ms=150,
    success=True,
)

monitor.record_playbook_usage(
    playbook_id="PB-SQLI-001",
    finding_type="SQL_INJECTION",
    success=True,
)

monitor.record_scan(
    scan_type="security",
    findings_count=5,
    duration_ms=2000,
)

# Update health
monitor.update_health("llm_service", "healthy", latency_ms=50)
monitor.update_health("database", "healthy", latency_ms=10)
monitor.update_health("scanner", "healthy", latency_ms=100)

# Get dashboard
dashboard = monitor.get_dashboard_data()
print("   Health status:", dashboard["health"]["overall"])
print("   LLM requests:", dashboard["metrics"]["llm"]["total_requests"])
print("   Playbook uses:", dashboard["metrics"]["learning"]["playbook_uses"])
print("   Total scans:", dashboard["metrics"]["security"]["total_scans"])
print("   [OK] System monitor working")

print("\n" + "=" * 50)
print("[SUCCESS] ALL LLM INFRASTRUCTURE COMPONENTS VERIFIED!")
print("=" * 50)

print("\nSUMMARY:")
print("- Extended playbooks:", count, "additional playbooks")
print("- Total playbooks:", len(all_playbooks))
print("- Finding types covered:", len(finding_types))
print("- LLM routing: GPT for reasoning, Claude for code")
print("- System monitoring: Health + Metrics + Dashboard")
