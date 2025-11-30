# backend/src/api/routes/auth.py

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.auth import (
    SignupRequest,
    LoginRequest,
    AuthTokensResponse,
    RefreshTokenRequest,
    LogoutResponse,
    MeResponse,
)
from api.deps import get_auth_service, get_current_user
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Auth"],
)


@router.post(
    "/signup",
    response_model=AuthTokensResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def signup(
    payload: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    """
    Register a new user and return access + refresh tokens.

    Business rules (enforced by AuthService, not this router):
    - Enforce unique email / username
    - Hash passwords securely (e.g., bcrypt)
    - Optionally send verification email
    """
    try:
        tokens = await auth_service.register_user(payload)
        return tokens
    except ValueError as exc:
        # For predictable business errors, return 400
        logger.info("Signup failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during signup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during signup.",
        ) from exc


@router.post(
    "/login",
    response_model=AuthTokensResponse,
    summary="Login with credentials",
)
async def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    """
    Authenticate user and return fresh access + refresh tokens.

    `AuthService.authenticate_user` is responsible for:
    - Validating credentials
    - Checking disabled/blocked users
    - Updating last-login metadata if needed
    """
    try:
        tokens = await auth_service.authenticate_user(payload)
        return tokens
    except PermissionError as exc:
        logger.info("Login failed (invalid credentials): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during login.",
        ) from exc


@router.post(
    "/refresh",
    response_model=AuthTokensResponse,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokensResponse:
    """
    Exchange a valid refresh token for a new access token (and optionally a new refresh).

    The AuthService handles:
    - Verifying refresh token signature and expiry
    - Optional rotation (invalidate old refresh tokens)
    """
    try:
        tokens = await auth_service.refresh_tokens(payload.refresh_token)
        return tokens
    except PermissionError as exc:
        logger.info("Token refresh failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during token refresh")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error during token refresh.",
        ) from exc


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout current user",
)
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> LogoutResponse:
    """
    Logout current user.

    Implementation details (inside AuthService):
    - Optionally blacklist the presented access token
    - Invalidate refresh tokens for this user/session
    - Record logout event for audit/logging
    """
    try:
        # We may want to pass token or session identifier to auth_service
        auth_header = request.headers.get("Authorization", "")
        await auth_service.logout_user(current_user, auth_header)
        return LogoutResponse(
            success=True,
            message="Logged out successfully.",
        )
    except Exception as exc:
        logger.exception("Unexpected error during logout")
        # Logout failures are not catastrophic for the client
        return LogoutResponse(
            success=False,
            message="Logout failed internally, but your token will expire automatically.",
        )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user profile",
)
async def get_me(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> MeResponse:
    """
    Return information about the current authenticated user.

    `get_current_user` is responsible for:
    - Validating and decoding access token
    - Loading user from DB/cache
    - Raising HTTP 401 if token invalid
    """
    return MeResponse(
        id=str(current_user.get("id")),
        email=current_user.get("email"),
        name=current_user.get("name"),
        role=current_user.get("role", "user"),
        org_id=current_user.get("org_id"),
    )
