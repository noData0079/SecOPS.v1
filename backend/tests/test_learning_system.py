"""
Test script for Self-Evolving Learning System components.
"""
import pytest
from core.learning import OutcomeIntelligenceEngine, FixSource
from core.learning import PlaybookEngine, FixPlaybook
from core.learning import PolicyLearner, SignalValue
from core.learning import LearningLoopOrchestrator, FixDecision

def test_outcome_intelligence_engine():
    print("\n1. Testing Outcome Intelligence Engine...")
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

    # Assertions
    assert outcome.outcome_id is not None
    assert outcome.is_success is True

    # Check effectiveness stats
    stats = engine.get_effectiveness_stats("SQL_INJECTION")
    assert stats.get("success_rate", 0) >= 0

def test_playbook_engine():
    print("\n2. Testing Fix Playbook Engine...")
    playbook_engine = PlaybookEngine()

    # Find matching playbook
    decision, playbook, reason = playbook_engine.get_fix_decision(
        finding_type="SQL_INJECTION",
        context={"language": "nodejs", "framework": "express"}
    )

    # Assertions
    assert decision is not None
    assert reason is not None

    # Check stats
    pb_stats = playbook_engine.get_stats()
    assert "total_playbooks" in pb_stats

def test_policy_learner():
    print("\n3. Testing Policy Learner...")
    policy_learner = PolicyLearner()

    # Evaluate a signal
    should_process, classification, eval_reason = policy_learner.evaluate_signal(
        signal_type="finding",
        finding_type="SQL_INJECTION",
        source="scanner"
    )

    # Assertions
    assert should_process is not None
    assert classification.value is not None

    # Get risk priority
    risk_score, risk_reason = policy_learner.get_risk_priority("SQL_INJECTION")
    assert risk_score is not None

def test_learning_loop_orchestrator():
    print("\n4. Testing Learning Loop Orchestrator...")
    orchestrator = LearningLoopOrchestrator()

    # Process a finding through complete loop
    result = orchestrator.process_finding(
        finding_id="F-002",
        finding_type="SQL_INJECTION",
        context={"language": "nodejs", "framework": "express"}
    )

    # Assertions
    assert result.loop_id is not None
    assert result.fix_decision.value is not None

    # Simulate verification
    orchestrator.record_verification(
        loop_id=result.loop_id,
        verification_passed=True,
        time_to_resolution=30,
        risk_reduction=0.85,
    )

    # Get system intelligence
    intelligence = orchestrator.get_system_intelligence()
    assert "llm_calls_saved" in intelligence
    assert "total_cost_saved" in intelligence
    assert "system_maturity" in intelligence
