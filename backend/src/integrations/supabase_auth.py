# backend/src/integrations/supabase_auth.py

from __future__ import annotations

import logging
import os
from typing import Any, Dict

from jose import JWTError, jwt

logger = logging.getLogger(__name__)


class SupabaseAuthError(Exception):
    """Raised when Supabase JWT validation fails."""


def _get_jwt_secret() -> str:
    """
    Resolve the secret used to verify Supabase JWTs.

    Typically this is SUPABASE_JWT_SECRET from Supabase project settings
    (Settings → API → JWT Secret). We also fall back to SUPABASE_SERVICE_ROLE
    if configured that way.
    """
    secret = (
        os.getenv("SUPABASE_JWT_SECRET")
        or os.getenv("SUPABASE_SERVICE_ROLE")
        or ""
    )
    if not secret:
        logger.warning(
            "Supabase JWT secret not configured. Set SUPABASE_JWT_SECRET in env "
            "to enable JWT verification."
        )
    return secret


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decode and validate a Supabase JWT access token.

    - Verifies signature using SUPABASE_JWT_SECRET
    - Uses HS256 by default (Supabase default)
    - Does NOT enforce audience by default, to avoid misconfig problems.

    Raises SupabaseAuthError on any failure.
    """
    secret = _get_jwt_secret()
    if not secret:
        raise SupabaseAuthError("Supabase JWT secret not configured")

    algorithm = os.getenv("SUPABASE_JWT_ALGORITHM", "HS256")

    try:
        payload: Dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        logger.warning("Supabase JWT decode failed: %s", exc)
        raise SupabaseAuthError("Invalid or expired Supabase token") from exc
