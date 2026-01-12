# backend/tests/test_admin_routes.py

from __future__ import annotations
from typing import Dict, Any
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.api.deps import require_admin, db_session


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def setup_admin_override() -> None:
    """Mock the require_admin dependency to bypass auth for testing logic."""
    def override_require_admin() -> Dict[str, Any]:
        return {
            "id": "admin_user",
            "email": "admin@example.com",
            "role": "admin",
            "raw": {}
        }
    app.dependency_overrides[require_admin] = override_require_admin

def setup_db_override() -> MagicMock:
    mock_session = MagicMock()
    # Mock result for count queries (scalar)
    mock_session.execute.return_value.scalar.return_value = 10
    # Mock result for list queries (scalars().all())
    mock_session.execute.return_value.scalars.return_value.all.return_value = []

    def override_db_session():
        yield mock_session

    app.dependency_overrides[db_session] = override_db_session
    return mock_session


class TestAdminRoutes:
    def teardown_method(self):
        clear_overrides()

    def test_admin_overview_requires_auth(self, client: TestClient):
        clear_overrides()
        resp = client.get("/api/admin/overview")
        assert resp.status_code in (401, 403)

    def test_admin_overview_success(self, client: TestClient):
        setup_admin_override()
        setup_db_override()
        resp = client.get("/api/admin/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "platform_health" in data
        assert "active_users" in data

    def test_admin_users_success(self, client: TestClient):
        setup_admin_override()
        mock_db = setup_db_override()
        # Mock user object
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.email = "test@example.com"
        mock_user.is_active = True
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        resp = client.get("/api/admin/users")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        if data["users"]:
            assert data["users"][0]["email"] == "test@example.com"

    def test_admin_projects_success(self, client: TestClient):
        setup_admin_override()
        setup_db_override()
        resp = client.get("/api/admin/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)

    def test_admin_audit_success(self, client: TestClient):
        setup_admin_override()
        mock_db = setup_db_override()
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.event_type = "LOGIN"
        mock_log.actor_id = "user1"
        mock_log.outcome = "SUCCESS"
        mock_log.created_at = "2023-01-01"
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_log]

        resp = client.get("/api/admin/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_admin_policies_success(self, client: TestClient):
        setup_admin_override()
        setup_db_override()
        resp = client.get("/api/admin/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)

    def test_admin_billing_success(self, client: TestClient):
        setup_admin_override()
        setup_db_override()
        resp = client.get("/api/admin/billing")
        assert resp.status_code == 200
        data = resp.json()
        assert "current_period_cost" in data
        assert "breakdown" in data
