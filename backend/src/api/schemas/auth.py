# backend/src/api/schemas/auth.py

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Core user-facing models
# ---------------------------------------------------------------------------


class SignupRequest(BaseModel):
    """
    Payload for user registration.

    Business rules (enforced in AuthService, not here):
    - email must be unique
    - password strength validation
    - optional org creation when org_name is provided
    """

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(
        ...,
        min_length=8,
        description="Raw password (will be hashed by AuthService).",
    )
    name: Optional[str] = Field(
        default=None,
        description="Display name of the user.",
    )
    org_name: Optional[str] = Field(
        default=None,
        description="Optional organization name to create / join.",
    )

    class Config:
        extra = "ignore"


class LoginRequest(BaseModel):
    """
    Payload for credential-based login.
    """

    email: EmailStr = Field(..., description="User email address.")
    password: str = Field(
        ...,
        min_length=1,
        description="Raw password.",
    )

    class Config:
        extra = "ignore"


class RefreshTokenRequest(BaseModel):
    """
    Payload for refreshing access tokens using a refresh token.
    """

    refresh_token: str = Field(
        ...,
        min_length=1,
        description="Opaque refresh token string.",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# User / profile models
# ---------------------------------------------------------------------------


class UserPublic(BaseModel):
    """
    Public representation of a user, safe to expose to clients.
    """

    id: str = Field(..., description="User identifier.")
    email: EmailStr = Field(..., description="User email.")
    name: Optional[str] = Field(
        default=None,
        description="Display name.",
    )
    role: str = Field(
        "user",
        description="Role: user, admin, etc.",
    )
    org_id: Optional[str] = Field(
        default=None,
        description="Organization identifier, if any.",
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="User creation timestamp, if available.",
    )

    class Config:
        extra = "ignore"


class MeResponse(BaseModel):
    """
    Response model for /api/auth/me.
    """

    id: str = Field(..., description="User identifier.")
    email: EmailStr = Field(..., description="User email.")
    name: Optional[str] = Field(
        default=None,
        description="Display name.",
    )
    role: str = Field(
        "user",
        description="Role: user, admin, etc.",
    )
    org_id: Optional[str] = Field(
        default=None,
        description="Organization identifier, if any.",
    )

    class Config:
        extra = "ignore"


# ---------------------------------------------------------------------------
# Token responses
# ---------------------------------------------------------------------------


class AuthTokensResponse(BaseModel):
    """
    Standard token response for signup/login/refresh.

    - access_token: short-lived JWT used for API calls
    - refresh_token: longer-lived token used to obtain new access tokens
    """

    access_token: str = Field(..., description="JWT access token.")
    refresh_token: str = Field(..., description="Opaque or JWT refresh token.")
    token_type: str = Field(
        "bearer",
        description="Token type for Authorization header.",
    )

    # Optional expiries in seconds (for UI hints; backend enforces real exp)
    expires_in: Optional[int] = Field(
        default=None,
        ge=0,
        description="Access token lifetime in seconds (optional).",
    )
    refresh_expires_in: Optional[int] = Field(
        default=None,
        ge=0,
        description="Refresh token lifetime in seconds (optional).",
    )

    # Optional user snapshot to avoid extra /me call after login
    user: Optional[UserPublic] = Field(
        default=None,
        description="Optional user info for convenience.",
    )

    class Config:
        extra = "ignore"


class LogoutResponse(BaseModel):
    """
    Response for /api/auth/logout.
    """

    success: bool = Field(..., description="Whether logout succeeded.")
    message: str = Field(..., description="Human-readable status message.")

    class Config:
        extra = "ignore"
