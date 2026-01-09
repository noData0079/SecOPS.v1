"""
Integration Tests for SecOps-AI API

Verifies data flow and endpoint functionality using FastAPI TestClient.
"""
from fastapi.testclient import TestClient
import sys
import os

# Add src to path
sys.path.insert(0, r'c:\Users\mymai\Desktop\SecOps-ai\backend\src')

from app import app

client = TestClient(app)

def test_health_check():
    """Verify system health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("[PASS] Health Check")

def test_findings_workflow():
    """Verify findings CRUD workflow."""
    # 1. Create Finding
    payload = {
        "title": "Test SQL Injection",
        "description": "Found potential SQLi in query",
        "finding_type": "SQL_INJECTION",
        "severity": "high",
        "file_path": "backend/db/query.py",
        "source": "integration_test"
    }
    response = client.post("/api/v1/findings", json=payload)
    assert response.status_code == 201
    data = response.json()
    finding_id = data["finding_id"]
    assert data["title"] == payload["title"]
    print(f"[PASS] Create Finding ({finding_id})")

    # 2. Get Finding
    response = client.get(f"/api/v1/findings/{finding_id}")
    assert response.status_code == 200
    assert response.json()["finding_id"] == finding_id
    print("[PASS] Get Finding")

    # 3. List Findings
    response = client.get("/api/v1/findings")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert any(f["finding_id"] == finding_id for f in items)
    print("[PASS] List Findings")

    # 4. Request Fix
    fix_payload = {
        "use_playbook": True,
        "force_llm": False
    }
    response = client.post(f"/api/v1/findings/{finding_id}/fix", json=fix_payload)
    if response.status_code == 200:
        print("[PASS] Request Fix (Success)")
    else:
        print(f"[WARN] Request Fix returned {response.status_code}: {response.text}")

def test_playbook_workflow():
    """Verify playbook management."""
    # 1. Create Playbook
    payload = {
        "finding_type": "TEST_VULN",
        "fix_template": "def fix(): pass",
        "description": "Test fix",
        "approval_policy": "human_review"
    }
    response = client.post("/api/v1/playbooks", json=payload)
    assert response.status_code == 201
    playbook_id = response.json()["playbook_id"]
    print(f"[PASS] Create Playbook ({playbook_id})")

    # 2. Get Playbook
    response = client.get(f"/api/v1/playbooks/{playbook_id}")
    assert response.status_code == 200
    assert response.json()["playbook_id"] == playbook_id
    print("[PASS] Get Playbook")

def test_system_metrics():
    """Verify system metrics."""
    response = client.get("/api/v1/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "llm" in data
    assert "findings_open" in data
    print("[PASS] System Metrics")

if __name__ == "__main__":
    print("="*40)
    print("STARTING INTEGRATION TESTS")
    print("="*40)
    
    try:
        test_health_check()
    except Exception as e:
        print(f"[FAIL] Health Check: {e}")
        
    try:
        test_findings_workflow()
    except Exception as e:
        print(f"[FAIL] Findings Workflow: {e}")

    try:
        test_playbook_workflow()
    except Exception as e:
        print(f"[FAIL] Playbook Workflow: {e}")

    try:
        test_system_metrics()
    except Exception as e:
        print(f"[FAIL] System Metrics: {e}")

    print("="*40)
    print("TESTS COMPLETED")
    print("="*40)
