# backend/src/utils/security.py

from __future__ import annotations

import logging
import re
import string
from typing import Iterable, Optional

from fastapi import Request

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Basic text sanitization
# ---------------------------------------------------------------------------


def sanitize_text(
    value: str,
    *,
    max_length: int = 5000,
    collapse_whitespace: bool = True,
    strip_control_chars: bool = True,
) -> str:
    """
    Sanitize a generic text input.

    - trims leading/trailing whitespace
    - optionally collapses internal whitespace
    - optionally strips non-printable control characters
    - enforces a maximum length

    This is suitable for things like titles, descriptions, queries, etc.
    """
    if value is None:
        return ""

    text = str(value)

    if strip_control_chars:
        text = "".join(ch for ch in text if ch in string.printable or ch == "\n")

    if collapse_whitespace:
        text = re.sub(r"\s+", " ", text)

    text = text.strip()

    if len(text) > max_length:
        logger.debug(
            "sanitize_text: truncating from %d to %d characters",
            len(text),
            max_length,
        )
        text = text[:max_length]

    return text


def sanitize_query(value: str, *, max_length: int = 2048) -> str:
    """
    Specialized sanitizer for search / RAG queries.

    - strips control chars
    - collapses whitespace
    - enforces a lower max length than generic text
    """
    return sanitize_text(
        value,
        max_length=max_length,
        collapse_whitespace=True,
        strip_control_chars=True,
    )


# ---------------------------------------------------------------------------
# URL / redirect safety
# ---------------------------------------------------------------------------


_URL_RE = re.compile(
    r"^https?://"  # http:// or https://
    r"[A-Za-z0-9\-._~%]+"  # host (very simple; we don't fully parse)
    r"(?::\d+)?"  # optional port
    r"(?:[/?#][^\s]*)?$",  # optional path/query/fragment
    re.IGNORECASE,
)


def is_valid_url(url: str) -> bool:
    """
    Basic URL validation for external links.

    This is intentionally simple; for stricter needs, use urllib.parse
    or pydantic's HttpUrl types.
    """
    if not url:
        return False
    return bool(_URL_RE.match(url))


def is_safe_redirect_url(url: str, allowed_hosts: Iterable[str]) -> bool:
    """
    Check that a redirect URL is safe:

      - must be absolute HTTP(S)
      - host must be in allowed_hosts, or it must be a relative path ("/...")

    This prevents open-redirect vulnerabilities.
    """
    if not url:
        return False

    # Allow purely relative paths
    if url.startswith("/"):
        return True

    if not is_valid_url(url):
        return False

    # Extract host in a cheap way
    # Example: https://example.com:8000/path?x=1
    try:
        host = url.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0]
        host = host.split("@", 1)[-1]  # strip userinfo if any
        host = host.lower()
    except Exception:
        return False

    allowed = {h.lower().strip() for h in allowed_hosts if h}
    return host in allowed


# ---------------------------------------------------------------------------
# Identifier / slug validation
# ---------------------------------------------------------------------------


_GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def validate_github_repo_slug(slug: str) -> bool:
    """
    Validate a GitHub repo slug like "owner/repo".

    Does not confirm existence; just checks the format.
    """
    if not slug:
        return False
    return bool(_GITHUB_REPO_RE.match(slug))


_ORG_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def sanitize_org_slug(candidate: str) -> str:
    """
    Sanitize a string into a safe org slug.

    Rules:
      - lowercase
      - keep alphanumeric and hyphen
      - must start with alphanumeric
      - trim length to 63 chars (similar to DNS label)
    """
    candidate = (candidate or "").strip().lower()
    # replace spaces with hyphen
    candidate = re.sub(r"\s+", "-", candidate)
    # drop invalid chars
    candidate = re.sub(r"[^a-z0-9-]", "", candidate)
    # trim leading non-alnum
    candidate = re.sub(r"^[^a-z0-9]+", "", candidate)
    # trim to 63 chars
    candidate = candidate[:63] or "org"
    return candidate


def is_valid_org_slug(slug: str) -> bool:
    """
    Validate org slug format (same rules as sanitize_org_slug target).
    """
    if not slug:
        return False
    return bool(_ORG_SLUG_RE.match(slug))


# ---------------------------------------------------------------------------
# Secret masking (for logs)
# ---------------------------------------------------------------------------


def mask_secret(value: Optional[str], *, show_last: int = 4) -> str:
    """
    Mask a secret value for logging.

    Example:
        mask_secret("sk-abcdef123456") -> "********3456"
    """
    if not value:
        return ""
    s = str(value)
    if len(s) <= show_last:
        return "*" * len(s)
    return "*" * (len(s) - show_last) + s[-show_last:]


# ---------------------------------------------------------------------------
# Simple rate-limit / fingerprint helper
# ---------------------------------------------------------------------------


def client_fingerprint_from_request(request: Request) -> str:
    """
    Derive a simple client fingerprint for logging/rate limiting:
      - IP (remote addr)
      - user-agent (if present)

    This is *not* for security-critical identity, only for coarse rate limiting
    or abuse detection signals.
    """
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    fp = f"{client_host}|{user_agent}"
    return fp
