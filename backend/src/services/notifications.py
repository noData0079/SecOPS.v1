# backend/src/services/notifications.py

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Dict, Iterable, Optional

from utils.config import Settings, settings  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)

# httpx is small and async-friendly, but we treat it as optional.
try:
    import httpx  # type: ignore

    _HTTPX_AVAILABLE = True
except Exception:  # pragma: no cover
    _HTTPX_AVAILABLE = False

# aiosmtplib is optional; if missing, email sends will no-op with a warning.
try:
    import aiosmtplib  # type: ignore

    _AIOSMTP_AVAILABLE = True
except Exception:  # pragma: no cover
    _AIOSMTP_AVAILABLE = False


# ---------------------------------------------------------------------------
# Configuration models
# ---------------------------------------------------------------------------


@dataclass
class EmailConfig:
    enabled: bool
    from_address: str
    smtp_host: str
    smtp_port: int
    username: Optional[str]
    password: Optional[str]
    use_tls: bool

    @classmethod
    def from_settings(cls, cfg: Settings) -> "EmailConfig":
        enabled = bool(
            getattr(cfg, "EMAIL_ENABLED", None)
            or os.getenv("EMAIL_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
        )

        from_address = (
            getattr(cfg, "EMAIL_FROM", None)
            or os.getenv("EMAIL_FROM")
            or "no-reply@secops.local"
        )
        smtp_host = (
            getattr(cfg, "EMAIL_SMTP_HOST", None)
            or os.getenv("EMAIL_SMTP_HOST")
            or "localhost"
        )
        smtp_port_raw = (
            getattr(cfg, "EMAIL_SMTP_PORT", None)
            or os.getenv("EMAIL_SMTP_PORT")
            or "587"
        )
        try:
            smtp_port = int(smtp_port_raw)
        except ValueError:
            smtp_port = 587

        username = (
            getattr(cfg, "EMAIL_SMTP_USER", None)
            or os.getenv("EMAIL_SMTP_USER")
            or None
        )
        password = (
            getattr(cfg, "EMAIL_SMTP_PASSWORD", None)
            or os.getenv("EMAIL_SMTP_PASSWORD")
            or None
        )

        use_tls = bool(
            getattr(cfg, "EMAIL_USE_TLS", None)
            or os.getenv("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes", "on"}
        )

        return cls(
            enabled=enabled,
            from_address=from_address,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            username=username,
            password=password,
            use_tls=use_tls,
        )


@dataclass
class SlackConfig:
    enabled: bool
    webhook_url: Optional[str]

    @classmethod
    def from_settings(cls, cfg: Settings) -> "SlackConfig":
        enabled = bool(
            getattr(cfg, "SLACK_ENABLED", None)
            or os.getenv("SLACK_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
        )

        webhook = (
            getattr(cfg, "SLACK_WEBHOOK_URL", None)
            or os.getenv("SLACK_WEBHOOK_URL")
            or None
        )

        # If no URL, treat as disabled.
        if not webhook:
            enabled = False

        return cls(enabled=enabled, webhook_url=webhook)


@dataclass
class WebhookConfig:
    """
    Generic webhook configuration for system-wide events.

    In the future, you might support multiple webhooks per org.
    For now, this is a global hook endpoint.
    """

    enabled: bool
    url: Optional[str]

    @classmethod
    def from_settings(cls, cfg: Settings) -> "WebhookConfig":
        enabled = bool(
            getattr(cfg, "WEBHOOK_ENABLED", None)
            or os.getenv("WEBHOOK_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
        )

        url = (
            getattr(cfg, "WEBHOOK_URL", None)
            or os.getenv("WEBHOOK_URL")
            or None
        )

        if not url:
            enabled = False

        return cls(enabled=enabled, url=url)


# ---------------------------------------------------------------------------
# Notification service
# ---------------------------------------------------------------------------


class NotificationService:
    """
    Minimal, deployment-ready notification service.

    Supports:
      - Email (SMTP)
      - Slack incoming webhooks
      - Generic HTTP webhooks

    All methods are safe no-ops if not configured or if optional dependencies
    (httpx / aiosmtplib) are not installed.
    """

    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg
        self.email_cfg = EmailConfig.from_settings(cfg)
        self.slack_cfg = SlackConfig.from_settings(cfg)
        self.webhook_cfg = WebhookConfig.from_settings(cfg)

        logger.info(
            "NotificationService initialized "
            "(email_enabled=%s, slack_enabled=%s, webhook_enabled=%s)",
            self.email_cfg.enabled,
            self.slack_cfg.enabled,
            self.webhook_cfg.enabled,
        )

    # ------------------------------------------------------------------ #
    # Email
    # ------------------------------------------------------------------ #

    async def send_email(
        self,
        *,
        to_addresses: Iterable[str],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
    ) -> None:
        """
        Send an email to one or more recipients.

        - If EMAIL_ENABLED is false, this is a no-op.
        - If aiosmtplib is missing, this is a no-op (with warning).
        """
        if not self.email_cfg.enabled:
            logger.debug("NotificationService.send_email skipped: email disabled")
            return

        if not _AIOSMTP_AVAILABLE:
            logger.warning(
                "NotificationService.send_email: aiosmtplib not installed. "
                "Email sending is disabled."
            )
            return

        recipients = list({addr.strip() for addr in to_addresses if addr.strip()})
        if not recipients:
            logger.debug("NotificationService.send_email skipped: no recipients")
            return

        msg = EmailMessage()
        msg["From"] = self.email_cfg.from_address
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject

        # Plain-text / HTML handling
        if body_html:
            msg.set_content(body_text or "")
            msg.add_alternative(body_html, subtype="html")
        else:
            msg.set_content(body_text or "")

        try:
            logger.info("Sending email to %s (subject=%s)", recipients, subject)
            await aiosmtplib.send(
                msg,
                hostname=self.email_cfg.smtp_host,
                port=self.email_cfg.smtp_port,
                username=self.email_cfg.username,
                password=self.email_cfg.password,
                start_tls=self.email_cfg.use_tls,
            )
        except Exception:
            logger.exception("NotificationService.send_email failed")

    # ------------------------------------------------------------------ #
    # Slack
    # ------------------------------------------------------------------ #

    async def send_slack_message(
        self,
        *,
        text: str,
        blocks: Optional[Any] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Send a Slack message via incoming webhook.

        - If SLACK_ENABLED is false or no webhook URL, this is a no-op.
        - If httpx is not available, this is a no-op (with warning).
        """
        if not self.slack_cfg.enabled or not self.slack_cfg.webhook_url:
            logger.debug("NotificationService.send_slack_message skipped: Slack disabled")
            return

        if not _HTTPX_AVAILABLE:
            logger.warning(
                "NotificationService.send_slack_message: httpx not installed. "
                "Slack notifications are disabled."
            )
            return

        payload: Dict[str, Any] = {
            "text": text,
        }
        if blocks is not None:
            payload["blocks"] = blocks
        if extra:
            payload.update(extra)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    self.slack_cfg.webhook_url,
                    json=payload,
                )
            if resp.status_code >= 400:
                logger.warning(
                    "NotificationService.send_slack_message: non-200 status (%s): %s",
                    resp.status_code,
                    resp.text,
                )
        except Exception:
            logger.exception("NotificationService.send_slack_message failed")

    # ------------------------------------------------------------------ #
    # Generic Webhooks
    # ------------------------------------------------------------------ #

    async def send_webhook_event(
        self,
        *,
        event_type: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Send a generic webhook event.

        - If WEBHOOK_ENABLED is false or no URL, this is a no-op.
        - If httpx is not available, this is a no-op.

        Example payload:
            event_type = "issue.created"
            payload = {"org_id": "...", "issue_id": "...", "severity": "high"}

        In future, this can be extended to support per-org webhooks.
        """
        if not self.webhook_cfg.enabled or not self.webhook_cfg.url:
            logger.debug("NotificationService.send_webhook_event skipped: webhook disabled")
            return

        if not _HTTPX_AVAILABLE:
            logger.warning(
                "NotificationService.send_webhook_event: httpx not installed. "
                "Webhook sending is disabled."
            )
            return

        body = {
            "event_type": event_type,
            "payload": payload,
        }

        req_headers: Dict[str, str] = {
            "Content-Type": "application/json",
        }
        if headers:
            req_headers.update(headers)

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(
                    self.webhook_cfg.url,
                    data=json.dumps(body),
                    headers=req_headers,
                )
            if resp.status_code >= 400:
                logger.warning(
                    "NotificationService.send_webhook_event: non-200 status (%s): %s",
                    resp.status_code,
                    resp.text,
                )
        except Exception:
            logger.exception("NotificationService.send_webhook_event failed")


# Global singleton for easy import
notifications = NotificationService(settings)  # type: ignore[arg-type]
