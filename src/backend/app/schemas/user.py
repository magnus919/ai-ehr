"""Pydantic schemas for User and authentication resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for registering a new user."""

    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(
        "practitioner",
        pattern=r"^(admin|practitioner|nurse|staff|patient)$",
    )
    npi: Optional[str] = Field(None, pattern=r"^\d{10}$")


class UserUpdate(BaseModel):
    """Schema for updating a user profile."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(
        None,
        pattern=r"^(admin|practitioner|nurse|staff|patient)$",
    )
    npi: Optional[str] = Field(None, pattern=r"^\d{10}$")
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Public user representation (password never exposed)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    npi: Optional[str] = None
    is_active: bool
    mfa_enabled: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Credentials for login."""

    email: EmailStr
    password: str
    mfa_code: Optional[str] = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """Returned on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Request to refresh an access token."""

    refresh_token: str


class MFASetupResponse(BaseModel):
    """Returned when MFA is set up."""

    secret: str
    provisioning_uri: str


class MFAVerifyRequest(BaseModel):
    """Verify an MFA TOTP code."""

    code: str = Field(..., min_length=6, max_length=6)
