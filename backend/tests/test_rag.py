# backend/tests/test_rag.py

from __future__ import annotations

from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.api.deps import get_current_user, get_optional_current_user, get_rag_orchestrator


class DummyUser:
    """Minimal stand-in for an authenticated user."""

    def __init__(self) -> None:
        self.id = "user-1"
        self.org_id = "org-1"
        self.email = "test@example.com"
        self.is_active = True
        self.is_superuser = False


class DummyRagOrchestrator:
    """Fake RAG orchestrator that returns a deterministic response."""

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
        # Shape kept generic so it works with the Pydantic response model in the API.
        return {
            "answer": f"Dummy answer for: {query}",
            "sources": [],
            "usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            },
        }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_rag_query_requires_auth(client: TestClient) -> None:
    """
    Calling /api/rag/query without auth should fail with 401/403.
    """
    # Make sure we are not overriding auth dependencies here.
    app.dependency_overrides.clear()

    resp = client.post(
        "/api/rag/query",
        json={"query": "test query without auth"},
    )

    # FastAPI/OAuth2 typically uses 401, but if you wired 403 it's also acceptable.
    assert resp.status_code in (401, 403)


def test_rag_query_happy_path_with_overrides(client: TestClient) -> None:
    """
    With a fake authenticated user and fake RAG orchestrator, the endpoint
    should return a 200 and a well-formed JSON response.
    """

    # Arrange: override dependencies to avoid real DB/LLM calls
    async def override_get_current_user() -> DummyUser:
        return DummyUser()

    def override_get_rag_orchestrator() -> DummyRagOrchestrator:
        return DummyRagOrchestrator()

    # Override both get_current_user and get_optional_current_user just to be safe,
    # since the route uses get_optional_current_user but the dep logic checks get_current_user override.
    # But overriding get_optional_current_user directly is the most reliable way.
    app.dependency_overrides[get_optional_current_user] = override_get_current_user
    app.dependency_overrides[get_rag_orchestrator] = override_get_rag_orchestrator

    try:
        payload = {"query": "How secure is my system?"}

        resp = client.post("/api/rag/query", json=payload)
        assert resp.status_code == 200

        data = resp.json()
        assert isinstance(data, dict)

        # Depending on how the route wraps the orchestrator result,
        # `data` might be either the raw result or under a "result" key.
        # Handle both cases defensively.
        if "result" in data:
            result = data["result"]
        else:
            result = data

        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert "sources" in result
        assert isinstance(result["sources"], list)
    finally:
        # Always clear overrides so other tests are unaffected
        app.dependency_overrides.clear()
