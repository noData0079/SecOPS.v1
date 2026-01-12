from __future__ import annotations

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    success: bool
    message: str


class MeResponse(BaseModel):
    id: str
    email: Optional[EmailStr]
    name: Optional[str] = None
    role: str
    org_id: Optional[str] = None
