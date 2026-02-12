"""
OpenMedRecord - FastAPI application entry point.

Configures CORS, security headers, audit/tenant middleware, routers,
health-check endpoint, and startup/shutdown lifecycle events.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.middleware.audit import AuditMiddleware
from app.api.middleware.tenant import TenantMiddleware
from app.api.routes import (
    allergies,
    appointments,
    audit_logs,
    auth,
    clinical_notes,
    conditions,
    consents,
    encounters,
    fhir,
    immunizations,
    observations,
    orders,
    patients,
    users,
)
from app.core.config import settings
from app.core.database import dispose_engine, init_db


# ── Lifespan ─────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown hooks."""
    # Startup: ensure database tables exist
    await init_db()
    yield
    # Shutdown: close connection pool
    await dispose_engine()


# ── Application ──────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Open-source Electronic Health Record system.  "
        "Provides REST and FHIR R4 APIs for clinical data management."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


# ── Middleware (order matters: outermost runs first) ─────────────────────

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# 2. Security headers
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=63072000; includeSubDomains; preload"
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# 3. Request timing / rate-limit headers
@app.middleware("http")
async def timing_middleware(request: Request, call_next) -> Response:
    start = time.monotonic()
    response = await call_next(request)
    elapsed = round((time.monotonic() - start) * 1000, 2)
    response.headers["X-Request-Time-Ms"] = str(elapsed)
    response.headers["X-RateLimit-Limit"] = settings.RATE_LIMIT_DEFAULT
    return response


# 4. Tenant resolution (must run before route handlers)
app.add_middleware(TenantMiddleware)

# 5. Audit logging
app.add_middleware(AuditMiddleware)


# ── Routers ──────────────────────────────────────────────────────────────

API_V1 = "/api/v1"

app.include_router(auth.router, prefix=API_V1)
app.include_router(patients.router, prefix=API_V1)
app.include_router(encounters.router, prefix=API_V1)
app.include_router(orders.router, prefix=API_V1)
app.include_router(appointments.router, prefix=API_V1)
app.include_router(allergies.router, prefix=API_V1)
app.include_router(observations.router, prefix=API_V1)
app.include_router(conditions.router, prefix=API_V1)
app.include_router(clinical_notes.router, prefix=API_V1)
app.include_router(immunizations.router, prefix=API_V1)
app.include_router(users.router, prefix=API_V1)
app.include_router(consents.router, prefix=API_V1)
app.include_router(audit_logs.router, prefix=API_V1)
app.include_router(fhir.router)  # FHIR routes live at /fhir/*


# ── Health check ─────────────────────────────────────────────────────────


@app.get("/health", tags=["Infrastructure"], summary="Health check")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "fhir_metadata": "/fhir/metadata",
    }
