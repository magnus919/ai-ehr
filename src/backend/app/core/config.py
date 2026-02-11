"""
Application configuration using Pydantic Settings.

All sensitive values are loaded from environment variables or a .env file.
"""

from __future__ import annotations

import secrets
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the OpenMedRecord backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "OpenMedRecord"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # production | staging | development

    # ── Server ───────────────────────────────────────────────────────────
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    WORKERS: int = 4

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://openmed:openmed@localhost:5432/openmedrecord"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    # ── JWT / Auth ───────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_urlsafe(64)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # ── Encryption ───────────────────────────────────────────────────────
    FIELD_ENCRYPTION_KEY: str = ""  # Fernet key – must be set in production
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    # ── Multi-Tenancy ────────────────────────────────────────────────────
    DEFAULT_TENANT_SCHEMA: str = "public"

    # ── MFA ───────────────────────────────────────────────────────────────
    MFA_ISSUER_NAME: str = "OpenMedRecord"

    # ── Audit ────────────────────────────────────────────────────────────
    AUDIT_LOG_ENABLED: bool = True

    # ── Logging ──────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
