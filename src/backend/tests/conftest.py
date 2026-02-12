"""
Pytest configuration and shared fixtures for OpenMedRecord backend tests.

Provides:
  - Async test database with automatic schema creation and teardown
  - httpx AsyncClient wired to the FastAPI application
  - Test user and authentication token fixtures
  - Mock tenant context for multi-tenant isolation
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# ---------------------------------------------------------------------------
# Override settings before any app module is imported
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://openmed_test:openmed_test@localhost:5432/openmedrecord_test",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-not-for-production")
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY", "dGVzdC1mZXJuZXQta2V5LW5vdC1mb3ItcHJvZA=="
)
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from app.core.config import settings  # noqa: E402
from app.core.database import Base, get_db, tenant_context  # noqa: E402

import app.models  # noqa: E402, F401 – ensure all ORM models register with Base

# ---------------------------------------------------------------------------
# Database engine & session fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = settings.DATABASE_URL

# Engine and session factory are created lazily inside the session-scoped
# fixture so that the asyncpg connection pool is bound to the pytest-asyncio
# event loop (not to whatever loop exists at import time).
_test_engine = None
_test_session_factory = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_database():
    """Create engine + tables at session start; drop them at session end."""
    global _test_engine, _test_session_factory

    # Dispose the production engine that was created at module-import time
    # (before the pytest-asyncio event loop existed).  Any connections it
    # already holds would be bound to the wrong loop.
    import app.core.database as _db_mod

    await _db_mod.engine.dispose()

    engine_kwargs: dict = {"echo": False}
    if not TEST_DATABASE_URL.startswith("sqlite"):
        # NullPool avoids connection-reuse issues with BaseHTTPMiddleware
        # (which spawns separate tasks via call_next).  Each DB operation
        # creates a fresh asyncpg connection bound to the current loop.
        engine_kwargs["poolclass"] = NullPool
    _test_engine = create_async_engine(TEST_DATABASE_URL, **engine_kwargs)
    _test_session_factory = async_sessionmaker(
        bind=_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    # Replace the production engine/factory at the module level so that
    # any code that uses the module globals gets the test engine.
    _db_mod.engine = _test_engine
    _db_mod.async_session_factory = _test_session_factory

    # The audit middleware imports async_session_factory by name, so we must
    # also patch its local reference at session start.
    import app.api.middleware.audit as _audit_mod

    _audit_mod.async_session_factory = _test_session_factory

    # Only create/drop tables for real database (PostgreSQL).
    # Unit tests use SQLite with mocks and don't need actual tables;
    # some models use PostgreSQL-specific types (JSONB, ARRAY) that
    # SQLite cannot handle.
    _is_sqlite = TEST_DATABASE_URL.startswith("sqlite")

    if not _is_sqlite:
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    if not _is_sqlite:
        async with _test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await _test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _cleanup_tables():
    """Clear all tables after each test for isolation."""
    yield
    # SQLite unit tests use mocks and don't need DB cleanup
    if TEST_DATABASE_URL.startswith("sqlite"):
        return
    table_names = ", ".join(
        f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables)
    )
    if table_names:
        async with _test_engine.begin() as conn:
            await conn.execute(text(f"TRUNCATE TABLE {table_names} CASCADE"))


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for direct test use (setup/verification).

    For unit tests: used via dependency override in the client fixture.
    For integration tests: used for direct DB setup (e.g. creating test users).
    """
    async with _test_session_factory() as session:
        if not TEST_DATABASE_URL.startswith("sqlite"):
            await session.execute(text("SET search_path TO public"))
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient backed by the real FastAPI app.

    For unit tests (SQLite), overrides get_db with the test session.
    For integration tests (PostgreSQL), patches the app's DB module to use
    the test engine so each request gets its own session (avoids asyncpg
    cross-task connection sharing issues with BaseHTTPMiddleware).
    """
    import app.api.middleware.audit as audit_mod
    import app.api.middleware.tenant as tenant_mod
    import app.core.database as db_module
    from app.main import app  # type: ignore[import-untyped]

    _orig_prefixes = tenant_mod._PUBLIC_PREFIXES
    _orig_audit_factory = audit_mod.async_session_factory

    if TEST_DATABASE_URL.startswith("sqlite"):
        # Unit tests: override get_db to yield the shared test session
        async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
            yield db_session

        app.dependency_overrides[get_db] = _override_get_db
    else:
        # Integration tests: patch the DB module so the app creates its own
        # sessions from the test engine (each request gets a fresh session,
        # avoiding asyncpg cross-task issues with BaseHTTPMiddleware).
        db_module.engine = _test_engine
        db_module.async_session_factory = _test_session_factory
        # The audit middleware imports async_session_factory directly, so we
        # must also patch its local reference.
        audit_mod.async_session_factory = _test_session_factory
        # All paths use the public schema in integration tests (no tenant
        # schemas are created in the test DB).
        tenant_mod._PUBLIC_PREFIXES = ("/",)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    tenant_mod._PUBLIC_PREFIXES = _orig_prefixes
    audit_mod.async_session_factory = _orig_audit_factory


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------

TEST_USER_EMAIL = "test.clinician@openmedrecord.health"
TEST_USER_PASSWORD = "Test!Passw0rd#2024"
TEST_USER_ID = str(uuid.uuid4())
TEST_TENANT_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


@pytest.fixture
def test_user_data() -> dict:
    """Raw data for creating a test user."""
    return {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "first_name": "Test",
        "last_name": "Clinician",
        "role": "admin",
        "npi": "1234567893",
        "is_active": True,
        "tenant_id": TEST_TENANT_ID,
    }


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_data: dict) -> dict:
    """Create a test user in the database and return user data with ID."""
    from app.core.security import hash_password  # noqa: E402
    from app.models.user import User  # noqa: E402

    # Create user directly using the User model
    user = User(
        id=uuid.UUID(test_user_data["id"]),
        tenant_id=uuid.UUID(test_user_data["tenant_id"]),
        email=test_user_data["email"],
        hashed_password=hash_password(test_user_data["password"]),
        first_name=test_user_data["first_name"],
        last_name=test_user_data["last_name"],
        role=test_user_data["role"],
        npi=test_user_data.get("npi"),
        is_active=test_user_data["is_active"],
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.commit()
    return {**test_user_data, "id": str(user.id)}


@pytest.fixture
def auth_token(test_user_data: dict) -> str:
    """Generate a valid JWT access token for the test user."""
    from app.core.security import create_access_token  # noqa: E402

    return create_access_token(
        user_id=uuid.UUID(test_user_data["id"]),
        tenant_id=uuid.UUID(test_user_data["tenant_id"]),
        role=test_user_data["role"],
        extra={"email": test_user_data["email"]},
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """HTTP headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ---------------------------------------------------------------------------
# Multi-tenancy
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_tenant():
    """Set the tenant context for the duration of a test."""
    token = tenant_context.set("test_tenant")
    yield "test_tenant"
    tenant_context.reset(token)


# ---------------------------------------------------------------------------
# Sample data factories
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_patient_data() -> dict:
    """Valid patient registration payload."""
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": "1985-06-15",
        "gender": "female",
        "mrn": f"MRN-{uuid.uuid4().hex[:8].upper()}",
        "email": "jane.doe@example.com",
        "phone": "+15551234567",
        "address": {
            "line": ["123 Main Street", "Apt 4B"],
            "city": "Springfield",
            "state": "IL",
            "postalCode": "62701",
            "country": "US",
        },
        "emergency_contact": {
            "name": "John Doe",
            "relationship": "spouse",
            "phone": "+15559876543",
        },
    }


@pytest.fixture
def sample_encounter_data() -> dict:
    """Valid encounter creation payload."""
    return {
        "encounter_type": "ambulatory",
        "practitioner_id": TEST_USER_ID,
        "reason": "Annual physical examination",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "location": "Main Campus - Room 204",
    }


@pytest.fixture
def sample_observation_data() -> dict:
    """Valid vital signs observation payload."""
    return {
        "code": "85354-9",
        "display": "Blood pressure panel",
        "category": "vital-signs",
        "components": [
            {
                "code": "8480-6",
                "display": "Systolic blood pressure",
                "value": 120,
                "unit": "mmHg",
            },
            {
                "code": "8462-4",
                "display": "Diastolic blood pressure",
                "value": 80,
                "unit": "mmHg",
            },
        ],
        "effective_datetime": datetime.now(timezone.utc).isoformat(),
        "status": "final",
    }
