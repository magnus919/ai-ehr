"""
Authentication and cryptographic utilities.

- JWT access / refresh token creation and verification
- Password hashing with Argon2
- OAuth2 bearer token dependency for FastAPI
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── OAuth2 scheme ────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── JWT helpers ──────────────────────────────────────────────────────────
def _create_token(
    data: Dict[str, Any],
    expires_delta: timedelta,
    token_type: str = "access",
) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "exp": now + expires_delta,
            "iat": now,
            "type": token_type,
        }
    )
    return jwt.encode(  # nosec B105 -- key is loaded from env vars, not hardcoded
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    role: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    data: Dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": role,
    }
    if extra:
        data.update(extra)
    return _create_token(
        data,
        timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(user_id: UUID, tenant_id: UUID) -> str:
    return _create_token(
        {"sub": str(user_id), "tenant_id": str(tenant_id)},
        timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES),
        token_type="refresh",
    )


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT.  Raises HTTPException on failure."""
    try:
        payload = jwt.decode(  # nosec B105 -- key is loaded from env vars, not hardcoded
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


class TokenPayload:
    """Convenience wrapper around the decoded JWT payload."""

    def __init__(self, payload: Dict[str, Any]) -> None:
        self.sub: str = payload.get("sub", "")
        self.tenant_id: str = payload.get("tenant_id", "")
        self.role: str = payload.get("role", "")
        self.token_type: str = payload.get("type", "access")
        self.exp: Optional[int] = payload.get("exp")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """FastAPI dependency: extracts and validates the JWT bearer token,
    returning the decoded payload as a ``TokenPayload`` instance."""
    payload = decode_token(token)
    token_data = TokenPayload(payload)
    if not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type; access token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data


def require_role(*allowed_roles: str):
    """Return a dependency that enforces role-based access control."""

    async def _check_role(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _check_role
