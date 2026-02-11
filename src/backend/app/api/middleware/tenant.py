"""
Multi-tenant middleware.

Extracts the ``tenant_id`` claim from the JWT bearer token and sets the
``tenant_context`` context variable so that all downstream database
operations are automatically scoped to the correct PostgreSQL schema.

Unauthenticated routes (e.g. /health, /api/v1/auth/*) are allowed through
without a tenant context.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.database import tenant_context
from app.core.security import decode_token

# Paths that do not require tenant resolution
_PUBLIC_PREFIXES = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/fhir/metadata",
)


class TenantMiddleware(BaseHTTPMiddleware):
    """Set the tenant schema based on the JWT ``tenant_id`` claim."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip tenant resolution for public endpoints
        if any(path.startswith(p) for p in _PUBLIC_PREFIXES):
            tenant_context.set(settings.DEFAULT_TENANT_SCHEMA)
            return await call_next(request)

        # Try to extract tenant_id from the Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = decode_token(token)
                tid = payload.get("tenant_id", "")
                if tid:
                    # Convert the tenant UUID to a safe schema name
                    schema = f"tenant_{tid.replace('-', '_')}"
                    tenant_context.set(schema)
                else:
                    tenant_context.set(settings.DEFAULT_TENANT_SCHEMA)
            except Exception:
                tenant_context.set(settings.DEFAULT_TENANT_SCHEMA)
        else:
            tenant_context.set(settings.DEFAULT_TENANT_SCHEMA)

        response = await call_next(request)
        return response
