# backend/src/services/auth_service.py

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.config import Settings, settings  # type: ignore[attr-defined]
from db.models import User, Organization, ApiToken

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

    subject: typically the user ID (as string)
    org_id:  organization ID the user belongs to
    is_superuser: whether token should carry admin claim
    expires_delta: optional custom expiry (defaults to config)
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

    Returns the payload dict or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token,
            _jwt_cfg.secret_key,
            algorithms=[_jwt_cfg.algorithm],
        )
        if payload.get("type") != "access":
            logger.warning("decode_access_token: invalid token type: %s", payload.get("type"))
            return None
        return payload
    except JWTError as exc:
        logger.info("decode_access_token: JWT error: %s", exc)
        return None
    except Exception:
        logger.exception("decode_access_token: unexpected error")
        return None


# ---------------------------------------------------------------------------
# Database helpers: users / orgs
# ---------------------------------------------------------------------------


async def get_user_by_email(
    db: AsyncSession,
    *,
    email: str,
) -> Optional[User]:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    *,
    user_id: str,
) -> Optional[User]:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_org_by_id(
    db: AsyncSession,
    *,
    org_id: str,
) -> Optional[Organization]:
    stmt = select(Organization).where(Organization.id == org_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
) -> Optional[User]:
    """
    Return the user if email/password pair is correct and user is active; else None.
    """
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_organization(
    db: AsyncSession,
    *,
    name: str,
    slug: str,
) -> Organization:
    """
    Create a new organization.

    Caller is responsible for ensuring uniqueness of slug (we also have
    a DB constraint). In case of collisions, the DB will raise an error.
    """
    org = Organization(name=name, slug=slug)
    db.add(org)
    await db.flush()  # assign PK
    return org


async def create_user(
    db: AsyncSession,
    *,
    org: Organization,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    is_superuser: bool = False,
) -> User:
    """
    Create a new user belonging to the given org.
    """
    user = User(
        org_id=org.id,
        email=email.strip().lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()  # assign PK
    return user


# ---------------------------------------------------------------------------
# API Tokens
# ---------------------------------------------------------------------------


def _generate_api_token_plain() -> str:
    """
    Generate a random API token string.

    We never store this raw value in DB – we only keep a hash.
    """
    return token_urlsafe(40)  # ~ 320 bits of entropy


def _hash_api_token(token: str) -> str:
    """
    Hash API token using the same password hashing context.
    """
    return _pwd_context.hash(token)


def verify_api_token_hash(token: str, token_hash: str) -> bool:
    """
    Verify API token against its stored hash.
    """
    try:
        return _pwd_context.verify(token, token_hash)
    except Exception:
        return False


async def create_api_token(
    db: AsyncSession,
    *,
    user: User,
    org: Organization,
    name: str,
    expires_in_days: Optional[int] = None,
) -> Tuple[str, ApiToken]:
    """
    Create a new API token for a user and org.

    Returns:
        (plain_token, ApiToken ORM object)

    The plain token is only returned once – caller should show it to the user
    and/or persist it securely on client side. The DB only stores its hash.
    """
    plain_token = _generate_api_token_plain()
    token_hash = _hash_api_token(plain_token)

    expires_at: Optional[datetime] = None
    if expires_in_days is not None and expires_in_days > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    api_token = ApiToken(
        user_id=user.id,
        org_id=org.id,
        name=name,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(api_token)
    await db.flush()

    logger.info("Created API token %s for user=%s org=%s", api_token.id, user.id, org.id)
    return plain_token, api_token


async def get_user_by_api_token(
    db: AsyncSession,
    *,
    token: str,
) -> Optional[User]:
    """
    Resolve user from an API token value (bearer token in header).

    Behaviour:
      - find candidate ApiToken rows for the org (we must scan, since token_hash can't be reversed)
      - verify token against each hash
      - check expiry
      - update last_used_at (fire-and-forget if you want)
    """
    # We cannot search by hash, so we need to fetch all tokens and verify each.
    # If the number of tokens per user/org remains small (normal), this is fine.
    stmt = select(ApiToken).where(ApiToken.expires_at.is_(None) | (ApiToken.expires_at > datetime.now(timezone.utc)))
    result = await db.execute(stmt)
    tokens = result.scalars().all()

    matched_token: Optional[ApiToken] = None
    for row in tokens:
        if verify_api_token_hash(token, row.token_hash):
            matched_token = row
            break

    if not matched_token:
        return None

    # Update last_used_at
    matched_token.last_used_at = datetime.now(timezone.utc)
    try:
        await db.flush()
    except Exception:  # not critical if last_used_at fails
        logger.exception("Failed to update last_used_at for API token %s", matched_token.id)

    # Fetch associated user (active check)
    stmt_user = select(User).where(User.id == matched_token.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return user


# ---------------------------------------------------------------------------
# High-level helper: token-based authentication
# ---------------------------------------------------------------------------


async def get_user_from_access_token(
    db: AsyncSession,
    *,
    token: str,
) -> Optional[User]:
    """
    Decode JWT access token and load the corresponding user.

    Returns None if token invalid/expired or user not found/inactive.
    """
    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user = await get_user_by_id(db, user_id=str(user_id))
    if not user or not user.is_active:
        return None

    return user
