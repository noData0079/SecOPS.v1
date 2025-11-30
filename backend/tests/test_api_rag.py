# backend/tests/test_api_rag.py

from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from src.main import app
from api.deps import get_current_user, get_rag_orchestrator


class DummyUser:
    """Minimal test user object compatible with deps.get_current_user usage."""

    def __init__(self) -> None:
        self.id = "user-1"
        self.org_id = "org-1"
        self.email = "test@example.com"
        self.is_active = True
        self.is_superuser = False


class DummyRagOrchestrator:
    """Fake orchestrator that mimics the shape of a real RAG response."""

    async def run(
        self,
        *,
        org_id: str,
        query: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_k: int | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return {
            "answer": f"Dummy answer for: {query}",
            "sources": [
                {
                    "title": "Dummy Source",
                    "url": "https://example.com/dummy",
                }
            ],
            "usage": {
                "input_tokens": 42,
                "output_tokens": 13,
                "total_tokens": 55,
            },
        }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def setup_overrides() -> None:
    """Apply dependency overrides for RAG tests."""
    def override_get_current_user() -> DummyUser:
        return DummyUser()

    def override_get_rag_orchestrator() -> DummyRagOrchestrator:
        return DummyRagOrchestrator()

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_rag_orchestrator] = override_get_rag_orchestrator


def clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_rag_query_validation_error(client: TestClient) -> None:
    """
    If the request body is missing required fields, FastAPI should return 422.
    """
    clear_overrides()  # we don't need auth here; we just care about schema

    resp = client.post("/api/rag/query", json={})
    assert resp.status_code == 422  # FastAPI validation error


def test_rag_query_success_shape(client: TestClient) -> None:
    """
    With overrides in place, the /api/rag/query endpoint should:

      - return 200
      - return a JSON object containing an 'answer' string
        and 'sources' list, and optional 'usage' info
    """
    setup_overrides()

    try:
        payload = {
            "query": "Explain my CI/CD security posture in simple terms.",
            # optional fields like top_k / max_tokens can be added here if your schema supports them
        }

        resp = client.post("/api/rag/query", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert isinstance(data, dict)

        # Depending on how the route is implemented, the payload may be:
        #  - directly the orchestrator result, OR
        #  - wrapped under a "result" key. Support both.
        if "result" in data:
            result = data["result"]
        else:
            result = data

        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert result["answer"].startswith("Dummy answer for:")

        assert "sources" in result
        assert isinstance(result["sources"], list)

        # usage is optional but we check shape if present
        if "usage" in result:
            usage = result["usage"]
            assert isinstance(usage, dict)
            assert "input_tokens" in usage
            assert "output_tokens" in usage
            assert "total_tokens" in usage
    finally:
        clear_overrides()
