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

# ---------------------------------------------------------------------------
# Database engine & session fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = settings.DATABASE_URL

_test_engine_kwargs: dict = {"echo": False}
if not TEST_DATABASE_URL.startswith("sqlite"):
    _test_engine_kwargs.update(pool_size=5, max_overflow=5, pool_pre_ping=True)
_test_engine = create_async_engine(TEST_DATABASE_URL, **_test_engine_kwargs)

_test_session_factory = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_database():
    """Create all tables at session start; drop them at session end."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional database session that rolls back after each test."""
    async with _test_engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        # Set schema search path to public for tests
        await session.execute(text("SET search_path TO public"))
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


# ---------------------------------------------------------------------------
# FastAPI test client
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient backed by the real FastAPI app, using the test DB session."""
    # Lazy import to avoid circular imports and ensure settings are patched
    from app.main import app  # type: ignore[import-untyped]

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------

TEST_USER_EMAIL = "test.clinician@openmedrecord.health"
TEST_USER_PASSWORD = "Test!Passw0rd#2024"
TEST_USER_ID = str(uuid.uuid4())


@pytest.fixture
def test_user_data() -> dict:
    """Raw data for creating a test user."""
    return {
        "id": TEST_USER_ID,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "first_name": "Test",
        "last_name": "Clinician",
        "role": "practitioner",
        "npi": "1234567893",
        "is_active": True,
        "tenant_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
        "date_of_birth": "1985-06-15",
        "gender": "female",
        "mrn": f"MRN-{uuid.uuid4().hex[:8].upper()}",
        "ssn_last_four": "1234",
        "email": "jane.doe@example.com",
        "phone": "+15551234567",
        "address": {
            "line1": "123 Main Street",
            "line2": "Apt 4B",
            "city": "Springfield",
            "state": "IL",
            "postal_code": "62701",
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
        "class_code": "AMB",
        "type_code": "office-visit",
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


# ---------------------------------------------------------------------------
# Cleanup fixture (for integration tests that need real DB writes)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def cleanup_tables(db_session: AsyncSession):
    """Truncate all tables after the test (use sparingly)."""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))
    await db_session.commit()
