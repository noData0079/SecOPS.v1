
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch, AsyncMock
import json
from src.main import app

# Create a TestClient for the app
client = TestClient(app)

@pytest.fixture
def mock_rag_system():
    with patch("src.api.routes.relay.get_rag_system") as mock_get:
        mock_system = MagicMock()
        mock_get.return_value = mock_system

        # Mock the answer_query response
        mock_response = MagicMock()
        mock_response.answer = "Hello from the Sovereign Brain!"

        # IMPORTANT: answer_query is async, so we must use AsyncMock
        mock_system.answer_query = AsyncMock(return_value=mock_response)

        yield mock_system

def test_websocket_connection(mock_rag_system):
    """
    Test that we can connect to the websocket and send/receive messages.
    """
    with client.websocket_connect("/chat?client_id=test_client") as websocket:
        # Send a message
        websocket.send_text(json.dumps({"text": "Hello"}))

        # Receive response
        data = websocket.receive_text()
        response = json.loads(data)

        assert "response" in response
        assert response["response"] == "Hello from the Sovereign Brain!"

        # Verify context injection
        # Note: Since answer_query is async, we await or check call args appropriately
        # In mock, we can just check call_args

        assert mock_rag_system.answer_query.called
        call_args = mock_rag_system.answer_query.call_args
        assert call_args is not None

        kwargs = call_args.kwargs
        assert kwargs["org_id"] == "test_client"
        assert kwargs["request"].client == "test_client"

def test_websocket_missing_client_id():
    """
    Test connection fails or handles missing client_id (FastAPI validation).
    """
    # client_id is required
    with pytest.raises(Exception): # starlette.websockets.WebSocketDisconnect or similar
         with client.websocket_connect("/chat") as websocket:
            pass
