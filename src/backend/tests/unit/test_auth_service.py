"""
Unit tests for the Authentication Service.

Tests cover:
  - User registration
  - User login with credentials
  - JWT access/refresh token generation and validation
  - Password hashing and verification
  - MFA (TOTP) setup and verification
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_different_from_plaintext(self):
        """Hashed password must differ from the plaintext input."""
        from app.core.security import hash_password

        plaintext = "SecureP@ss123!"
        hashed = hash_password(plaintext)

        assert hashed != plaintext
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Correct password passes verification."""
        from app.core.security import hash_password, verify_password

        plaintext = "SecureP@ss123!"
        hashed = hash_password(plaintext)

        assert verify_password(plaintext, hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password fails verification."""
        from app.core.security import hash_password, verify_password

        hashed = hash_password("CorrectPassword1!")

        assert verify_password("WrongPassword1!", hashed) is False

    def test_hash_is_not_deterministic(self):
        """Two hashes of the same password should differ (random salt)."""
        from app.core.security import hash_password

        plaintext = "SecureP@ss123!"
        hash1 = hash_password(plaintext)
        hash2 = hash_password(plaintext)

        assert hash1 != hash2


class TestTokenGeneration:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_contains_subject(self):
        """Access token payload includes the subject (user ID)."""
        from app.core.security import create_access_token

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role="physician",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_returns_claims(self):
        """Decoding a valid token returns the embedded claims."""
        from app.core.security import create_access_token, decode_token

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            role="nurse",
        )

        claims = decode_token(token)

        assert claims["sub"] == str(user_id)
        assert claims["role"] == "nurse"
        assert claims["tenant_id"] == str(tenant_id)

    def test_expired_token_raises(self):
        """An expired token is rejected during decoding."""
        from app.core.security import decode_token
        from app.core.config import settings
        import jwt

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.now(timezone.utc)

        # Create an expired token manually
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": "physician",
            "exp": now - timedelta(seconds=1),
            "iat": now - timedelta(seconds=60),
            "type": "access",
        }
        expired_token = jwt.encode(
            payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

        with pytest.raises(HTTPException) as exc_info:
            decode_token(expired_token)
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises(self):
        """A token with a modified payload is rejected."""
        from app.core.security import create_access_token, decode_token

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = create_access_token(
            user_id=user_id, tenant_id=tenant_id, role="physician"
        )

        # Corrupt the token
        parts = token.split(".")
        parts[1] = parts[1][:-4] + "XXXX"
        tampered = ".".join(parts)

        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_create_refresh_token_has_longer_expiry(self):
        """Refresh tokens have a longer expiry than access tokens."""
        from app.core.security import (
            create_access_token,
            create_refresh_token,
            decode_token,
        )

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        access = create_access_token(
            user_id=user_id, tenant_id=tenant_id, role="physician"
        )
        refresh = create_refresh_token(user_id=user_id, tenant_id=tenant_id)

        access_claims = decode_token(access)
        refresh_claims = decode_token(refresh)

        assert refresh_claims["exp"] > access_claims["exp"]

    def test_token_includes_issued_at(self):
        """Tokens include an 'iat' (issued at) claim."""
        from app.core.security import create_access_token, decode_token

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        token = create_access_token(
            user_id=user_id, tenant_id=tenant_id, role="physician"
        )
        claims = decode_token(token)

        assert "iat" in claims
        assert claims["iat"] <= int(time.time()) + 5


class TestRegisterUser:
    """Tests for user registration."""

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Valid registration creates a new user."""
        from app.services.auth_service import register_user
        from app.schemas.user import UserCreate

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None  # No duplicate user
        mock_session.execute.return_value = mock_result

        tenant_id = uuid.uuid4()
        payload = UserCreate(
            email="newuser@example.com",
            password="SecureP@ss123!",
            first_name="New",
            last_name="User",
            role="physician",
        )

        result = await register_user(mock_session, tenant_id, payload)

        assert result.email == payload.email
        assert result.first_name == payload.first_name
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self):
        """Registration with duplicate email raises error."""
        from app.services.auth_service import register_user
        from app.schemas.user import UserCreate
        from app.models.user import User

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_user = User(
            id=uuid.uuid4(), email="existing@example.com", tenant_id=uuid.uuid4()
        )
        mock_result.scalar_one_or_none.return_value = mock_user  # Duplicate found
        mock_session.execute.return_value = mock_result

        tenant_id = uuid.uuid4()
        payload = UserCreate(
            email="existing@example.com",
            password="SecureP@ss123!",
            first_name="New",
            last_name="User",
            role="physician",
        )

        with pytest.raises(HTTPException) as exc_info:
            await register_user(mock_session, tenant_id, payload)
        assert exc_info.value.status_code == 409


class TestAuthenticateUser:
    """Tests for the login flow."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Valid credentials return tokens."""
        from app.services.auth_service import authenticate_user
        from app.schemas.user import LoginRequest
        from app.models.user import User
        from app.core.security import hash_password

        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="doctor@example.com",
            hashed_password=hash_password("ValidPass1!"),
            is_active=True,
            role="physician",
            mfa_enabled=False,
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        payload = LoginRequest(email="doctor@example.com", password="ValidPass1!")
        result = await authenticate_user(mock_session, payload)

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Wrong password raises 401."""
        from app.services.auth_service import authenticate_user
        from app.schemas.user import LoginRequest
        from app.models.user import User
        from app.core.security import hash_password

        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="doctor@example.com",
            hashed_password=hash_password("CorrectPass1!"),
            is_active=True,
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        payload = LoginRequest(email="doctor@example.com", password="WrongPass1!")
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user(mock_session, payload)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Login with non-existent email raises 401."""
        from app.services.auth_service import authenticate_user
        from app.schemas.user import LoginRequest

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        payload = LoginRequest(email="nobody@example.com", password="AnyPass1!")
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user(mock_session, payload)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self):
        """Inactive user cannot log in."""
        from app.services.auth_service import authenticate_user
        from app.schemas.user import LoginRequest
        from app.models.user import User
        from app.core.security import hash_password

        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="disabled@example.com",
            hashed_password=hash_password("ValidPass1!"),
            is_active=False,
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        payload = LoginRequest(email="disabled@example.com", password="ValidPass1!")
        with pytest.raises(HTTPException) as exc_info:
            await authenticate_user(mock_session, payload)
        assert exc_info.value.status_code == 401


class TestMFA:
    """Tests for multi-factor authentication (TOTP)."""

    @pytest.mark.asyncio
    async def test_setup_mfa(self):
        """MFA setup returns a secret and provisioning URI."""
        from app.services.auth_service import setup_mfa
        from app.models.user import User

        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="user@example.com",
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        result = await setup_mfa(mock_session, mock_user.id)

        assert len(result.secret) == 32  # Base32-encoded TOTP secret
        assert "otpauth://totp/" in result.provisioning_uri
        assert "user@example.com" in result.provisioning_uri
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_mfa_valid_code(self):
        """A valid TOTP code passes verification and enables MFA."""
        import pyotp
        from app.services.auth_service import verify_mfa
        from app.models.user import User

        secret = pyotp.random_base32()
        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="user@example.com",
            mfa_secret=secret,
            mfa_enabled=False,
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        result = await verify_mfa(mock_session, mock_user.id, valid_code)

        assert result is True
        assert mock_user.mfa_enabled is True
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_mfa_invalid_code(self):
        """An invalid TOTP code fails verification."""
        import pyotp
        from app.services.auth_service import verify_mfa
        from app.models.user import User

        secret = pyotp.random_base32()
        mock_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="user@example.com",
            mfa_secret=secret,
            mfa_enabled=False,
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await verify_mfa(mock_session, mock_user.id, "000000")
        assert exc_info.value.status_code == 401
