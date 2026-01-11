# backend/src/api/routes/webhooks.py

from __future__ import annotations

import logging
import json
from typing import Any, Dict

from fastapi import APIRouter, Request, status, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/webhooks",
    tags=["Webhooks"],
)

@router.post("/slack/interactive", summary="Handle Slack interactive components")
async def slack_interactive_webhook(request: Request):
    """
    Endpoint to receive interactive payloads from Slack (e.g., button clicks).

    This is a stub implementation. In a real scenario, it would verify the request signature
    and process the payload.
    """
    try:
        # Slack sends payload as form data 'payload' JSON string
        form_data = await request.form()
        payload_str = form_data.get("payload")

        if not payload_str:
             # Sometimes it might be raw JSON depending on configuration
             try:
                 payload = await request.json()
             except Exception:
                 raise HTTPException(status_code=400, detail="Missing payload")
        else:
            payload = json.loads(payload_str)

        logger.info("Received Slack interactive payload: %s", payload)

        actions = payload.get("actions", [])
        if actions:
            action = actions[0]
            value = action.get("value") # e.g., "req-123:Approve"

            if value:
                # Parse request ID and decision
                parts = value.split(":")
                if len(parts) >= 2:
                    request_id = parts[0]
                    decision = parts[1]
                    logger.info("Processing ChatOps decision: Request %s -> %s", request_id, decision)

                    # TODO: Call the actual Approval System or Autonomy Loop here.
                    # For now, we just log it as the integration "connecting" to the system.

                    return {"text": f"Request {request_id}: {decision} received."}

        return {"status": "ok"}

    except Exception as e:
        logger.exception("Error processing Slack webhook")
        raise HTTPException(status_code=500, detail="Internal processing error")
