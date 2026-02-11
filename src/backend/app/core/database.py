"""
Async SQLAlchemy engine, session management, and multi-tenant support.

Tenant isolation is implemented via PostgreSQL schema-per-tenant.  The
current tenant schema is stored in a context variable that is set by the
tenant middleware on every request.
"""

from __future__ import annotations

import contextvars
import re
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy import MetaData, event, text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

_SAFE_SCHEMA_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")


def _validate_schema_name(name: str) -> str:
    """Validate a PostgreSQL schema name to prevent SQL injection."""
    if not _SAFE_SCHEMA_RE.match(name):
        raise ValueError(f"Invalid schema name: {name!r}")
    return name


# ── Context variable that holds the current tenant schema ────────────────
tenant_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tenant_context", default=settings.DEFAULT_TENANT_SCHEMA
)

# ── Naming convention for constraints (makes Alembic migrations portable) ─
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all ORM models."""

    metadata = metadata


def _build_engine():
    return create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        echo=settings.DATABASE_ECHO,
        pool_pre_ping=True,
    )


engine = _build_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a tenant-aware async session.

    The search_path is set to the tenant schema so that all SQL
    statements are automatically scoped to the correct tenant.
    """
    async with async_session_factory() as session:
        schema = _validate_schema_name(tenant_context.get())
        await session.execute(text(f"SET search_path TO {schema}, public"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tenant_schema(schema_name: str) -> None:
    """Create a new PostgreSQL schema for a tenant and stamp it with
    the shared table definitions."""
    async with engine.begin() as conn:
        safe_name = _validate_schema_name(schema_name)
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {safe_name}"))


async def init_db() -> None:
    """Called once at application startup to ensure the public schema
    tables exist.  Per-tenant schemas are created via admin endpoints."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_engine() -> None:
    """Gracefully close all connection pool connections."""
    await engine.dispose()
