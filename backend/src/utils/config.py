# backend/src/utils/config.py

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    All values can be overridden via environment variables.
    We also support a .env file at project root in development.

    Examples:

      # Database
      DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/secops
      DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@host:5432/secops

      # JWT / secrets
      SECRET_KEY=super-secret
      JWT_SECRET_KEY=super-secret
      JWT_ALGORITHM=HS256
      ACCESS_TOKEN_EXPIRE_MINUTES=60

      # Metrics
      METRICS_ENABLED=true
      METRICS_NAMESPACE=secops_ai

      # Cost / pricing
      COST_BASE_CURRENCY=USD
      COST_MARGIN_TIERS_JSON=[{"limit":10,"margin":0.2},{"limit":1000,"margin":0.25}]
      MODEL_PRICING_JSON={"deepseek:r1":{"input":0.003,"output":0.003}}

      # Email
      EMAIL_ENABLED=true
      EMAIL_FROM=no-reply@secops.ai
      EMAIL_SMTP_HOST=smtp.gmail.com
      EMAIL_SMTP_PORT=587
      EMAIL_SMTP_USER=...
      EMAIL_SMTP_PASSWORD=...
      EMAIL_USE_TLS=true

      # Slack
      SLACK_ENABLED=true
      SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

      # Webhooks
      WEBHOOK_ENABLED=true
      WEBHOOK_URL=https://example.com/secops/webhook
    """

    # ------------------------------------------------------------------ #
    # Core / environment
    # ------------------------------------------------------------------ #

    ENV: str = Field(default="development", description="Environment name")
    DEBUG: bool = Field(default=False, description="Debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Root log level")

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #

    # Sync style URL (used by Alembic / admin tools)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Sync SQLAlchemy database URL, e.g. postgresql+psycopg2://...",
    )

    # Async URL (used by application runtime; if not set, derived from DATABASE_URL)
    DATABASE_URL_ASYNC: Optional[str] = Field(
        default=None,
        description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://...",
    )

    # ------------------------------------------------------------------ #
    # Security / JWT
    # ------------------------------------------------------------------ #

    SECRET_KEY: str = Field(
        default="CHANGE_ME_IN_PRODUCTION",
        description="Fallback secret key if JWT_SECRET_KEY not set",
    )
    JWT_SECRET_KEY: Optional[str] = Field(
        default=None,
        description="JWT signing secret; falls back to SECRET_KEY if not set",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="JWT access token expiry in minutes",
    )

    # ------------------------------------------------------------------ #
    # Metrics / monitoring
    # ------------------------------------------------------------------ #

    METRICS_ENABLED: bool = Field(
        default=True,
        description="Enable Prometheus metrics collector",
    )
    METRICS_NAMESPACE: str = Field(
        default="secops_ai",
        description="Prometheus metrics namespace",
    )

    # ------------------------------------------------------------------ #
    # Cost tracking / pricing
    # ------------------------------------------------------------------ #

    COST_BASE_CURRENCY: str = Field(
        default="USD",
        description="Base currency for cost accounting",
    )

    # JSON strings; parsed by CostTracker if provided
    COST_MARGIN_TIERS_JSON: Optional[str] = Field(
        default=None,
        description="JSON list of margin tiers, overrides defaults if set",
    )
    MODEL_PRICING_JSON: Optional[str] = Field(
        default=None,
        description="JSON map of model pricing per 1M tokens",
    )

    # ------------------------------------------------------------------ #
    # Email (SMTP)
    # ------------------------------------------------------------------ #

    EMAIL_ENABLED: bool = Field(
        default=False,
        description="Enable email notifications",
    )
    EMAIL_FROM: str = Field(
        default="no-reply@secops.local",
        description="Default from address for outgoing emails",
    )
    EMAIL_SMTP_HOST: str = Field(
        default="localhost",
        description="SMTP server hostname",
    )
    EMAIL_SMTP_PORT: int = Field(
        default=587,
        description="SMTP server port",
    )
    EMAIL_SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP username (if authentication required)",
    )
    EMAIL_SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password (if authentication required)",
    )
    EMAIL_USE_TLS: bool = Field(
        default=True,
        description="Whether to use STARTTLS for SMTP",
    )

    # ------------------------------------------------------------------ #
    # Slack
    # ------------------------------------------------------------------ #

    SLACK_ENABLED: bool = Field(
        default=False,
        description="Enable Slack notifications",
    )
    SLACK_WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Slack incoming webhook URL",
    )

    # ------------------------------------------------------------------ #
    # Generic Webhook
    # ------------------------------------------------------------------ #

    WEBHOOK_ENABLED: bool = Field(
        default=False,
        description="Enable global webhook notifications",
    )
    WEBHOOK_URL: Optional[str] = Field(
        default=None,
        description="Global webhook target URL",
    )

    # ------------------------------------------------------------------ #
    # Model configuration
    # ------------------------------------------------------------------ #

    # You can add more knobs later (e.g. default provider, default model names etc.)
    DEFAULT_LLM_PROVIDER: str = Field(
        default="deepseek",
        description="Default LLM provider identifier",
    )
    DEFAULT_LLM_MODEL: str = Field(
        default="r1",
        description="Default LLM model name",
    )

    # ------------------------------------------------------------------ #
    # Pydantic settings configuration
    # ------------------------------------------------------------------ #

    model_config = SettingsConfigDict(
        env_prefix="",              # no prefix; use raw env vars
        env_file=".env",            # optional .env at project root
        env_file_encoding="utf-8",
        extra="ignore",             # ignore unknown env vars
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Lazy singleton settings loader.

    Usage:

        from utils.config import settings

        print(settings.DATABASE_URL)
    """
    # If you ever want to override env in tests, clear this cache.
    return Settings()


# Convenience global instance used everywhere in the backend
settings = get_settings()


# Small helper for places where you might need to know if we're in production
def is_production() -> bool:
    env = (os.getenv("ENV") or settings.ENV).lower()
    return env in {"prod", "production"}
