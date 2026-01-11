# backend/src/integrations/enterprise/chat_ops.py

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

import httpx

from src.utils.config import Settings

logger = logging.getLogger(__name__)


class ChatOpsClient:
    """
    Integration for Chat-Ops (e.g., Slack, Teams).

    Handles sending interactive notifications and requesting approvals.
    Uses the existing 'NotificationService' logic but expands it for interactivity.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.webhook_url = getattr(settings, "SLACK_WEBHOOK_URL", None)

    async def send_message(self, text: str, blocks: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Send a message to the configured chat channel.
        """
        if not self.webhook_url:
            logger.warning("ChatOps: SLACK_WEBHOOK_URL not set. Message dropped: %s", text)
            return

        payload = {"text": text}
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(self.webhook_url, json=payload, timeout=10.0)
                if resp.status_code >= 400:
                    logger.error("ChatOps: Failed to send message: %s", resp.text)
            except Exception as e:
                logger.exception("ChatOps: Network error sending message")

    async def ask_for_approval(
        self,
        request_id: str,
        message: str,
        options: List[str] = ["Approve", "Deny"]
    ) -> None:
        """
        Send an interactive message requesting approval.

        Since we cannot easily receive webhooks in this environment without an exposed server,
        this method sends a message instructing the user how to approve (e.g., via dashboard or file).

        In a real connected setup, this would attach buttons that call back to an endpoint.
        """

        # Simulate Slack Block Kit interactive message
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{message}*\nRequest ID: `{request_id}`"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": option
                        },
                        "value": f"{request_id}:{option}"
                    } for option in options
                ]
            }
        ]

        await self.send_message(f"APPROVAL REQUEST: {message}", blocks=blocks)
        logger.info("ChatOps: Sent approval request %s to Slack.", request_id)
