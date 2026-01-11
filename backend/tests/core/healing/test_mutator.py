import pytest
from core.healing.mutator import HotFixMutator

def test_mutator_proposals():
    mutator = HotFixMutator()

    anomaly_context = {
        "type": "internal_inflammation",
        "metric": "latency",
        "target": "web-service-pod-1"
    }

    proposals = mutator.propose_fix(anomaly_context)

    assert len(proposals) >= 2

    # Check patch proposal
    patch_proposal = next(p for p in proposals if p.action_type == "apply_k8s_patch")
    assert patch_proposal.target == "web-service-pod-1"
    assert "patch" in patch_proposal.parameters
    assert patch_proposal.parameters["patch"]["mutation_metadata"]["increase_factor"] == 1.2

    # Check watchdog proposal
    watchdog_proposal = next(p for p in proposals if p.action_type == "deploy_watchdog")
    assert "script_content" in watchdog_proposal.parameters
    assert "#!/bin/bash" in watchdog_proposal.parameters["script_content"]
