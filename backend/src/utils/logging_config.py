# backend/src/utils/logging_config.py

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

from .config import settings, is_production


def _get_log_level() -> int:
    """
    Resolve log level from settings / env, defaulting to INFO.
    """
    raw = os.getenv("LOG_LEVEL") or settings.LOG_LEVEL
    raw = str(raw).upper()
    return getattr(logging, raw, logging.INFO)


class JsonLogFormatter(logging.Formatter):
    """
    Simple JSON log formatter for production deployments.

    Produces log entries like:

        {
          "ts": "2025-11-19T12:34:56.789123Z",
          "level": "INFO",
          "logger": "uvicorn.error",
          "message": "Application startup complete",
          "extra": {...}
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        log: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach exception info if present
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)

        # Attach extra fields if present (record.__dict__ may have extras)
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k
            not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }
        }
        if extra_fields:
            log["extra"] = extra_fields

        return json.dumps(log, ensure_ascii=False)


class ConsoleLogFormatter(logging.Formatter):
    """
    Simple human-readable formatter for local development.
    """

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        logger_name = record.name
        msg = record.getMessage()

        base = f"[{ts}] [{level:<8}] [{logger_name}] {msg}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def setup_logging() -> None:
    """
    Configure root logging for the application.

    - Sets root logger level based on settings.LOG_LEVEL / LOG_LEVEL env
    - Configures console handler with either JSON or human-friendly format
    - Normalizes uvicorn / FastAPI loggers to match
    """
    level = _get_log_level()
    production = is_production()

    # Remove existing handlers to avoid duplicate logs (especially when
    # running via uvicorn which may preconfigure logging).
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if production:
        formatter: logging.Formatter = JsonLogFormatter()
    else:
        formatter = ConsoleLogFormatter()

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # Silence overly noisy loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(level)
    logging.getLogger("uvicorn").setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiosmtplib").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Small banner in dev
    root_logger.info(
        "Logging initialized (level=%s, production=%s)",
        logging.getLevelName(level),
        production,
    )
