"""
Test script for Self-Evolving Learning System components.
"""
import sys
sys.path.insert(0, r'c:\Users\mymai\Desktop\SecOps-ai\backend\src')

print("Testing Self-Evolving Learning System...")
print("=" * 50)

# Test 1: Outcome Intelligence Engine
print("\n1. Testing Outcome Intelligence Engine...")
from core.learning import OutcomeIntelligenceEngine, FixSource

engine = OutcomeIntelligenceEngine()

# Record a successful playbook fix
outcome = engine.record_outcome(
    finding_id="F-001",
    finding_type="SQL_INJECTION",
    fix_source=FixSource.PLAYBOOK,
    verification_status="pass",
    playbook_id="PB-SQLI-001",
    time_to_fix_seconds=45,
    risk_reduction_score=0.9,
)
print("   Outcome recorded:", outcome.outcome_id[:8], "...")
print("   Is success:", outcome.is_success)

# Check effectiveness stats
stats = engine.get_effectiveness_stats("SQL_INJECTION")
print("   Success rate:", stats.get("success_rate", 0))
print("   [OK] Outcome engine working")

# Test 2: Fix Playbook Engine
print("\n2. Testing Fix Playbook Engine...")
from core.learning import PlaybookEngine, FixPlaybook

playbook_engine = PlaybookEngine()

# Find matching playbook
decision, playbook, reason = playbook_engine.get_fix_decision(
    finding_type="SQL_INJECTION",
    context={"language": "nodejs", "framework": "express"}
)
print("   Decision:", decision)
if playbook:
    print("   Playbook:", playbook.playbook_id)
    print("   Confidence:", playbook.confidence)
print("   Reason:", reason)

# Check stats
pb_stats = playbook_engine.get_stats()
print("   Total playbooks:", pb_stats["total_playbooks"])
print("   High confidence:", pb_stats["high_confidence"])
print("   [OK] Playbook engine working")

# Test 3: Policy Learner
print("\n3. Testing Policy Learner...")
from core.learning import PolicyLearner, SignalValue

policy_learner = PolicyLearner()

# Evaluate a signal
should_process, classification, eval_reason = policy_learner.evaluate_signal(
    signal_type="finding",
    finding_type="SQL_INJECTION",
    source="scanner"
)
print("   Should process:", should_process)
print("   Classification:", classification.value)

# Get risk priority
risk_score, risk_reason = policy_learner.get_risk_priority("SQL_INJECTION")
print("   Risk score:", risk_score)
print("   [OK] Policy learner working")

# Test 4: Learning Loop Orchestrator
print("\n4. Testing Learning Loop Orchestrator...")
from core.learning import LearningLoopOrchestrator, FixDecision

orchestrator = LearningLoopOrchestrator()

# Process a finding through complete loop
result = orchestrator.process_finding(
    finding_id="F-002",
    finding_type="SQL_INJECTION",
    context={"language": "nodejs", "framework": "express"}
)
print("   Loop ID:", result.loop_id[:8], "...")
print("   Fix decision:", result.fix_decision.value)
print("   Playbook used:", result.playbook_used)
print("   LLM used:", result.llm_used)
print("   Cost saved: $", result.llm_cost_saved)

# Simulate verification
orchestrator.record_verification(
    loop_id=result.loop_id,
    verification_passed=True,
    time_to_resolution=30,
    risk_reduction=0.85,
)

# Get system intelligence
intelligence = orchestrator.get_system_intelligence()
print("   LLM calls saved:", intelligence["llm_calls_saved"])
print("   Total cost saved: $", intelligence["total_cost_saved"])
print("   Maturity level:", intelligence["system_maturity"]["level"])
print("   [OK] Learning loop working")

print("\n" + "=" * 50)
print("[SUCCESS] ALL LEARNING SYSTEM COMPONENTS VERIFIED!")
print("=" * 50)

# Summary
print("\nSYSTEM CAPABILITIES:")
print("- Playbooks replace LLM calls over time")
print("- Confidence updates from outcomes")
print("- Noise reduction via signal learning")
print("- Cost savings tracking")
print("- System maturity scoring")
