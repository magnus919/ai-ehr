"""
Authentication and authorisation business logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pyotp
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    MFASetupResponse,
    TokenResponse,
    UserCreate,
    UserResponse,
)


async def register_user(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    payload: UserCreate,
) -> UserResponse:
    """Register a new user within a tenant."""

    # Check for duplicate email
    stmt = select(User).where(
        User.tenant_id == tenant_id,
        User.email == payload.email,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        npi=payload.npi,
    )
    db.add(user)
    await db.flush()
    return UserResponse.model_validate(user)


async def authenticate_user(
    db: AsyncSession,
    payload: LoginRequest,
) -> TokenResponse:
    """Validate credentials and return JWT tokens."""

    stmt = select(User).where(User.email == payload.email, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # MFA check
    if user.mfa_enabled:
        if not payload.mfa_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA code required",
            )
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(payload.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code",
            )

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()

    access = create_access_token(user.id, user.tenant_id, user.role)
    refresh = create_refresh_token(user.id, user.tenant_id)

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_tokens(
    db: AsyncSession,
    refresh_token: str,
) -> TokenResponse:
    """Issue new access and refresh tokens from a valid refresh token."""

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type; refresh token required",
        )

    user_id = uuid.UUID(payload["sub"])
    stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access = create_access_token(user.id, user.tenant_id, user.role)
    new_refresh = create_refresh_token(user.id, user.tenant_id)

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def setup_mfa(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> MFASetupResponse:
    """Generate a new TOTP secret for the user."""

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    secret = pyotp.random_base32()
    user.mfa_secret = secret
    await db.flush()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name=settings.MFA_ISSUER_NAME)

    return MFASetupResponse(secret=secret, provisioning_uri=uri)


async def verify_mfa(
    db: AsyncSession,
    user_id: uuid.UUID,
    code: str,
) -> bool:
    """Verify a TOTP code and enable MFA for the user on success."""

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not set up for this user",
        )

    totp = pyotp.TOTP(user.mfa_secret)
    if not totp.verify(code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid MFA code",
        )

    user.mfa_enabled = True
    await db.flush()
    return True
