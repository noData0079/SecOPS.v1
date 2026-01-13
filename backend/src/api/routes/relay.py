# backend/src/api/routes/relay.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
import logging
from typing import Optional

from src.rag.AdvancedRAGSystem import get_rag_system
from src.api.schemas.rag import RAGQueryRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/chat")
async def chat_relay(websocket: WebSocket, client_id: str = Query(..., description="Client ID for context isolation")):
    """
    Secure Relay WebSocket Endpoint.

    1. Authenticates connection (TODO: add token auth)
    2. Receives user message
    3. Injects client_id into RAG context
    4. Streams response from 'Brain' (AdvancedRAGSystem)
    """
    await websocket.accept()
    logger.info(f"Client {client_id} connected to Relay")

    rag_system = get_rag_system()

    # In a real scenario, we would fetch client config here
    # client_config = await get_client_config(client_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                user_query = message_data.get("text")
            except json.JSONDecodeError:
                 await websocket.send_text(json.dumps({"error": "Invalid JSON"}))
                 continue

            if not user_query:
                continue

            # Forward to "Brain" with Context Injection
            # We use org_id=client_id to leverage the namespace filtering we implemented
            # We pass client_id in the 'client' field of RAGQueryRequest which maps to context metadata

            rag_request = RAGQueryRequest(
                query=user_query,
                mode="default",
                client=client_id, # This propagates to context.metadata["client"]
                top_k=5
            )

            # TODO: Handle user_id properly. For now using "anonymous" or session ID if available
            response = await rag_system.answer_query(
                org_id=client_id,
                user_id="anonymous_widget_user",
                request=rag_request
            )

            # Stream back response
            # Format matches what the widget expects: { "response": "..." }
            await websocket.send_text(json.dumps({
                "response": response.answer
            }))

    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in relay: {e}")
        try:
            await websocket.close(code=1011, reason="Internal Error")
        except:
            pass
