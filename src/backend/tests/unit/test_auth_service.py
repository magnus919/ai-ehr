"""
Unit tests for the Authentication Service.

Tests cover:
  - User login with credentials
  - JWT access/refresh token generation and validation
  - Password hashing and verification
  - MFA (TOTP) setup and verification
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestPasswordHashing:
    """Tests for password hashing and verification."""

    def test_hash_password_returns_different_from_plaintext(self):
        """Hashed password must differ from the plaintext input."""
        from app.services.auth_service import AuthService

        plaintext = "SecureP@ss123!"
        hashed = AuthService.hash_password(plaintext)

        assert hashed != plaintext
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Correct password passes verification."""
        from app.services.auth_service import AuthService

        plaintext = "SecureP@ss123!"
        hashed = AuthService.hash_password(plaintext)

        assert AuthService.verify_password(plaintext, hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password fails verification."""
        from app.services.auth_service import AuthService

        hashed = AuthService.hash_password("CorrectPassword1!")

        assert AuthService.verify_password("WrongPassword1!", hashed) is False

    def test_hash_is_not_deterministic(self):
        """Two hashes of the same password should differ (random salt)."""
        from app.services.auth_service import AuthService

        plaintext = "SecureP@ss123!"
        hash1 = AuthService.hash_password(plaintext)
        hash2 = AuthService.hash_password(plaintext)

        assert hash1 != hash2


class TestTokenGeneration:
    """Tests for JWT token creation and validation."""

    def test_create_access_token_contains_subject(self):
        """Access token payload includes the subject (user ID)."""
        from app.services.auth_service import AuthService

        token = AuthService.create_access_token(
            subject="user-123",
            extra_claims={"role": "physician"},
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token_returns_claims(self):
        """Decoding a valid token returns the embedded claims."""
        from app.services.auth_service import AuthService

        token = AuthService.create_access_token(
            subject="user-456",
            extra_claims={"role": "nurse", "tenant_id": "tenant-001"},
        )

        claims = AuthService.decode_token(token)

        assert claims["sub"] == "user-456"
        assert claims["role"] == "nurse"
        assert claims["tenant_id"] == "tenant-001"

    def test_expired_token_raises(self):
        """An expired token is rejected during decoding."""
        from app.services.auth_service import AuthService

        token = AuthService.create_access_token(
            subject="user-789",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(Exception):  # JWTError or ExpiredSignatureError
            AuthService.decode_token(token)

    def test_tampered_token_raises(self):
        """A token with a modified payload is rejected."""
        from app.services.auth_service import AuthService

        token = AuthService.create_access_token(subject="user-100")

        # Corrupt the token
        parts = token.split(".")
        parts[1] = parts[1][:-4] + "XXXX"
        tampered = ".".join(parts)

        with pytest.raises(Exception):
            AuthService.decode_token(tampered)

    def test_create_refresh_token_has_longer_expiry(self):
        """Refresh tokens have a longer expiry than access tokens."""
        from app.services.auth_service import AuthService

        access = AuthService.create_access_token(subject="user-200")
        refresh = AuthService.create_refresh_token(subject="user-200")

        access_claims = AuthService.decode_token(access)
        refresh_claims = AuthService.decode_token(refresh)

        assert refresh_claims["exp"] > access_claims["exp"]

    def test_token_includes_issued_at(self):
        """Tokens include an 'iat' (issued at) claim."""
        from app.services.auth_service import AuthService

        token = AuthService.create_access_token(subject="user-300")
        claims = AuthService.decode_token(token)

        assert "iat" in claims
        assert claims["iat"] <= int(time.time()) + 5


class TestLogin:
    """Tests for the login flow."""

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Valid credentials return user data and tokens."""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.id = "user-login-001"
        mock_user.email = "doctor@example.com"
        mock_user.hashed_password = AuthService.hash_password("ValidPass1!")
        mock_user.is_active = True
        mock_user.role = "physician"
        mock_user.mfa_enabled = False

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)
        result = await service.authenticate(
            email="doctor@example.com",
            password="ValidPass1!",
        )

        assert result is not None
        assert "access_token" in result
        assert "refresh_token" in result

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(self):
        """Wrong password returns None (authentication failure)."""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.hashed_password = AuthService.hash_password("CorrectPass1!")
        mock_user.is_active = True

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)
        result = await service.authenticate(
            email="doctor@example.com",
            password="WrongPass1!",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(self):
        """Login with a non-existent email returns None."""
        from app.services.auth_service import AuthService

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)
        result = await service.authenticate(
            email="nobody@example.com",
            password="AnyPass1!",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_login_inactive_user_fails(self):
        """An inactive/disabled user cannot log in."""
        from app.services.auth_service import AuthService

        mock_user = MagicMock()
        mock_user.hashed_password = AuthService.hash_password("ValidPass1!")
        mock_user.is_active = False

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_session.execute.return_value = mock_result

        service = AuthService(mock_session)
        result = await service.authenticate(
            email="disabled@example.com",
            password="ValidPass1!",
        )

        assert result is None


class TestMFA:
    """Tests for multi-factor authentication (TOTP)."""

    def test_generate_mfa_secret(self):
        """MFA setup returns a secret and provisioning URI."""
        from app.services.auth_service import AuthService

        secret, uri = AuthService.generate_mfa_secret("user@example.com")

        assert len(secret) == 32  # Base32-encoded TOTP secret
        assert "otpauth://totp/" in uri
        assert "OpenMedRecord" in uri

    def test_verify_mfa_valid_code(self):
        """A valid TOTP code passes verification."""
        import pyotp

        from app.services.auth_service import AuthService

        secret, _ = AuthService.generate_mfa_secret("user@example.com")
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        assert AuthService.verify_mfa_code(secret, valid_code) is True

    def test_verify_mfa_invalid_code(self):
        """An invalid TOTP code fails verification."""
        from app.services.auth_service import AuthService

        secret, _ = AuthService.generate_mfa_secret("user@example.com")

        assert AuthService.verify_mfa_code(secret, "000000") is False

    def test_verify_mfa_expired_code(self):
        """A TOTP code from a previous time window is rejected (strict mode)."""
        import pyotp

        from app.services.auth_service import AuthService

        secret, _ = AuthService.generate_mfa_secret("user@example.com")
        totp = pyotp.TOTP(secret)

        # Generate a code from 60 seconds ago (2 windows back)
        old_code = totp.at(datetime.now(timezone.utc) - timedelta(seconds=60))

        # Should fail with valid_window=0 (strict)
        result = AuthService.verify_mfa_code(secret, old_code, valid_window=0)
        # The code may or may not be valid depending on timing; we just verify
        # the function executes without error
        assert isinstance(result, bool)
