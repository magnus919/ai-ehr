"""
Authentication routes.

POST /auth/login      - Authenticate with email + password (+ optional MFA)
POST /auth/register   - Register a new user
POST /auth/refresh    - Refresh an access token
POST /auth/mfa/setup  - Generate a TOTP secret for the current user
POST /auth/mfa/verify - Verify a TOTP code and enable MFA
POST /auth/logout     - Logout (client-side token discard)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.schemas.user import (
    LoginRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.authenticate_user(db, payload)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    # In production the tenant_id would come from an admin flow.  For
    # bootstrapping we generate one.
    tenant_id = uuid.uuid4()
    return await auth_service.register_user(db, tenant_id, payload)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an access token",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.post(
    "/mfa/setup",
    response_model=MFASetupResponse,
    summary="Set up MFA for the current user",
)
async def mfa_setup(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MFASetupResponse:
    return await auth_service.setup_mfa(db, uuid.UUID(current_user.sub))


@router.post(
    "/mfa/verify",
    status_code=status.HTTP_200_OK,
    summary="Verify MFA code and enable MFA",
)
async def mfa_verify(
    payload: MFAVerifyRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await auth_service.verify_mfa(db, uuid.UUID(current_user.sub), payload.code)
    return {"detail": "MFA enabled successfully"}


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout (client should discard tokens)",
)
async def logout(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    # Stateless JWT — actual invalidation requires a token blocklist which
    # can be added later (e.g. Redis-backed).
    return {"detail": "Logged out successfully"}
