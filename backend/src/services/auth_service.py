# backend/src/services/auth_service.py

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional, Tuple, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.utils.config import Settings, settings  # type: ignore[attr-defined]
from src.db.models import User, Organization, ApiToken
from src.api.schemas.auth import SignupRequest, LoginRequest, AuthTokensResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return _pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # If verification fails for any reason, treat as mismatch.
        return False


# ---------------------------------------------------------------------------
# JWT configuration
# ---------------------------------------------------------------------------


class JwtSettings:
    """Wrapper around JWT-related configuration."""

    def __init__(self, cfg: Settings) -> None:
        self.secret_key: str = (
            getattr(cfg, "JWT_SECRET_KEY", None)
            or os.getenv("JWT_SECRET_KEY")
            or getattr(cfg, "SECRET_KEY", None)
            or os.getenv("SECRET_KEY")
            or "CHANGE_ME_IN_PRODUCTION"
        )

        self.algorithm: str = (
            getattr(cfg, "JWT_ALGORITHM", None)
            or os.getenv("JWT_ALGORITHM")
            or "HS256"
        )

        default_exp = (
            getattr(cfg, "ACCESS_TOKEN_EXPIRE_MINUTES", None)
            or os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
            or "60"
        )
        try:
            self.access_token_expire_minutes: int = int(default_exp)
        except ValueError:
            self.access_token_expire_minutes = 60


_jwt_cfg = JwtSettings(settings)  # type: ignore[arg-type]


def create_access_token(
    *,
    subject: str,
    org_id: str,
    is_superuser: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=_jwt_cfg.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode = {
        "sub": str(subject),
        "org_id": str(org_id),
        "is_superuser": bool(is_superuser),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    encoded_jwt = jwt.encode(
        to_encode,
        _jwt_cfg.secret_key,
        algorithm=_jwt_cfg.algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_cfg.secret_key,
            algorithms=[_jwt_cfg.algorithm],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None
    except Exception:
        return None


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    async def register_user(self, payload: SignupRequest) -> AuthTokensResponse:
        # Check if user exists
        stmt = select(User).where(User.email == payload.email)
        result = self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("User already exists")

        # Create Org (auto-create for now)
        org = Organization(id=token_urlsafe(16), name=f"{payload.username or 'User'}'s Org")
        self.db.add(org)
        self.db.flush()

        # Create User
        user = User(
            id=token_urlsafe(16),
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.username,
            is_active=True,
            is_superuser=False,
            # org_id would be here in a real multi-tenant schema
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # Create Token
        token = create_access_token(subject=user.id, org_id=org.id, is_superuser=user.is_superuser)

        return AuthTokensResponse(
            access_token=token,
            refresh_token="ref_token_placeholder", # Implement refresh logic if needed
            token_type="bearer",
            expires_in=_jwt_cfg.access_token_expire_minutes * 60
        )

    async def authenticate_user(self, payload: LoginRequest) -> AuthTokensResponse:
        stmt = select(User).where(User.email == payload.email)
        result = self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise PermissionError("Invalid credentials")

        # Mock org for now since User model update didn't include org_id
        org_id = "org_default"

        token = create_access_token(subject=user.id, org_id=org_id, is_superuser=user.is_superuser)

        return AuthTokensResponse(
            access_token=token,
            refresh_token="ref_token_placeholder",
            token_type="bearer",
            expires_in=_jwt_cfg.access_token_expire_minutes * 60
        )

    async def refresh_tokens(self, refresh_token: str) -> AuthTokensResponse:
        # Simplified placeholder
        raise NotImplementedError("Refresh token flow not implemented yet")

    async def logout_user(self, current_user: Dict[str, Any], token: str) -> None:
        # Blacklist logic would go here
        pass
