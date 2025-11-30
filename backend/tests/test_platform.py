# backend/tests/test_platform.py

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from src.main import app
from api.deps import get_current_user


class DummyUser:
    """Minimal stand-in for an authenticated user."""

    def __init__(self) -> None:
        self.id = "user-1"
        self.org_id = "org-1"
        self.email = "test@example.com"
        self.is_active = True
        self.is_superuser = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def setup_auth_override() -> None:
    def override_get_current_user() -> DummyUser:
        return DummyUser()

    app.dependency_overrides[get_current_user] = override_get_current_user


def test_platform_status_requires_auth(client: TestClient) -> None:
    """
    /api/platform/status should not be accessible without authentication.
    """
    clear_overrides()

    resp = client.get("/api/platform/status")
    # Depending on how OAuth2 is wired, this may be 401 or 403.
    assert resp.status_code in (401, 403)


def test_platform_status_with_auth(client: TestClient) -> None:
    """
    With a fake authenticated user, /api/platform/status should:

      - return 200
      - return a JSON object with some basic platform info
    """
    clear_overrides()
    setup_auth_override()

    try:
        resp = client.get("/api/platform/status")
        assert resp.status_code == 200

        data = resp.json()
        assert isinstance(data, dict)

        # We keep this flexible: different implementations may expose
        # slightly different keys, but we expect *some* status-like info.
        # Common keys we might expect:
        #   - "status"
        #   - "env" / "environment"
        #   - "services" / "checks"
        #
        # We don't strictly require specific keys, but we assert there
        # is at least some content.
        assert len(data) > 0

        # If "status" exists, ensure it's not empty
        if "status" in data:
            assert data["status"] in ("ok", "healthy", "degraded")
    finally:
        clear_overrides()
