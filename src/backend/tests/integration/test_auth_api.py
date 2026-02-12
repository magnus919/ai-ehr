"""
Integration tests for the Authentication API endpoints.

Tests exercise the full auth lifecycle: registration, login, MFA setup,
token refresh, and logout.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


AUTH_PATH = "/auth"


class TestRegistration:
    """POST /auth/register"""

    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient):
        """Registering a new user returns 201 with user details."""
        payload = {
            "email": "new.user@openmedrecord.health",
            "password": "Str0ng!P@ssword123",
            "first_name": "New",
            "last_name": "User",
            "role": "physician",
        }
        response = await client.post(f"{AUTH_PATH}/register", json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["email"] == payload["email"]
        assert "id" in body
        # Password must never be returned
        assert "password" not in body
        assert "hashed_password" not in body

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Registering with an existing email returns 409 Conflict."""
        payload = {
            "email": "duplicate@openmedrecord.health",
            "password": "Str0ng!P@ssword123",
            "first_name": "First",
            "last_name": "User",
            "role": "nurse",
        }
        # First registration
        await client.post(f"{AUTH_PATH}/register", json=payload)

        # Duplicate
        response = await client.post(f"{AUTH_PATH}/register", json=payload)
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """A weak password is rejected with 422."""
        payload = {
            "email": "weak.pass@example.com",
            "password": "123",
            "first_name": "Weak",
            "last_name": "Password",
            "role": "admin",
        }
        response = await client.post(f"{AUTH_PATH}/register", json=payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email_format(self, client: AsyncClient):
        """An invalid email format is rejected with 422."""
        payload = {
            "email": "not-an-email",
            "password": "V@lidP@ss123!",
            "first_name": "Bad",
            "last_name": "Email",
            "role": "physician",
        }
        response = await client.post(f"{AUTH_PATH}/register", json=payload)

        assert response.status_code == 422


class TestLogin:
    """POST /auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Valid credentials return 200 with access and refresh tokens."""
        # Register
        reg_payload = {
            "email": "login.test@openmedrecord.health",
            "password": "V@lidP@ss123!",
            "first_name": "Login",
            "last_name": "Test",
            "role": "physician",
        }
        await client.post(f"{AUTH_PATH}/register", json=reg_payload)

        # Login
        login_payload = {
            "email": "login.test@openmedrecord.health",
            "password": "V@lidP@ss123!",
        }
        response = await client.post(f"{AUTH_PATH}/login", json=login_payload)

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Wrong password returns 401 Unauthorized."""
        # Register first
        reg_payload = {
            "email": "wrong.pass@openmedrecord.health",
            "password": "CorrectP@ss123!",
            "first_name": "Wrong",
            "last_name": "Pass",
            "role": "nurse",
        }
        await client.post(f"{AUTH_PATH}/register", json=reg_payload)

        # Attempt login with wrong password
        login_payload = {
            "email": "wrong.pass@openmedrecord.health",
            "password": "Wr0ngP@ss123!",
        }
        response = await client.post(f"{AUTH_PATH}/login", json=login_payload)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with a non-existent email returns 401."""
        payload = {
            "email": "nonexistent@openmedrecord.health",
            "password": "AnyP@ss123!",
        }
        response = await client.post(f"{AUTH_PATH}/login", json=payload)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_response_does_not_leak_user_existence(
        self, client: AsyncClient
    ):
        """Error messages for wrong email and wrong password are identical."""
        # Non-existent user
        r1 = await client.post(
            f"{AUTH_PATH}/login",
            json={"email": "ghost@example.com", "password": "P@ss123!"},
        )
        # Wrong password (register first)
        await client.post(
            f"{AUTH_PATH}/register",
            json={
                "email": "real@example.com",
                "password": "CorrectP@ss!1",
                "first_name": "R",
                "last_name": "U",
                "role": "admin",
            },
        )
        r2 = await client.post(
            f"{AUTH_PATH}/login",
            json={"email": "real@example.com", "password": "WrongP@ss!1"},
        )

        # Both should be 401 with the same error message
        assert r1.status_code == r2.status_code == 401
        assert r1.json().get("detail") == r2.json().get("detail")


class TestMFASetup:
    """POST /auth/mfa/setup and POST /auth/mfa/verify"""

    @pytest.mark.asyncio
    async def test_mfa_setup_returns_secret_and_qr(
        self, client: AsyncClient, auth_headers: dict
    ):
        """MFA setup returns a TOTP secret and a provisioning URI."""
        response = await client.post(f"{AUTH_PATH}/mfa/setup", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert "secret" in body
        assert "provisioning_uri" in body
        assert "otpauth://totp/" in body["provisioning_uri"]

    @pytest.mark.asyncio
    async def test_mfa_setup_requires_auth(self, client: AsyncClient):
        """MFA setup without authentication returns 401."""
        response = await client.post(f"{AUTH_PATH}/mfa/setup")
        assert response.status_code == 401


class TestTokenRefresh:
    """POST /auth/token/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_token_returns_new_access_token(self, client: AsyncClient):
        """A valid refresh token returns a new access token."""
        # Register and login
        email = "refresh.test@openmedrecord.health"
        password = "Refr3sh!P@ss123"
        await client.post(
            f"{AUTH_PATH}/register",
            json={
                "email": email,
                "password": password,
                "first_name": "Refresh",
                "last_name": "Test",
                "role": "physician",
            },
        )
        login_resp = await client.post(
            f"{AUTH_PATH}/login",
            json={"email": email, "password": password},
        )
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        response = await client.post(
            f"{AUTH_PATH}/token/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["access_token"] != login_resp.json()["access_token"]

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        """An invalid refresh token returns 401."""
        response = await client.post(
            f"{AUTH_PATH}/token/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401
