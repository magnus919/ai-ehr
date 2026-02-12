"""
Audit logging middleware.

Captures request-level metadata (IP, user-agent, path, method) for every
authenticated request that touches a PHI-related endpoint and writes an
audit log entry.
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings
from app.core.database import (
    _validate_schema_name,
    async_session_factory,
    tenant_context,
)
from app.core.security import decode_token

logger = logging.getLogger(__name__)

# Resource paths that involve PHI and must be audit-logged
_PHI_PREFIXES = (
    "/api/v1/patients",
    "/api/v1/encounters",
    "/api/v1/orders",
    "/api/v1/appointments",
    "/api/v1/allergies",
    "/api/v1/clinical-notes",
    "/api/v1/observations",
    "/api/v1/conditions",
    "/api/v1/immunizations",
    "/api/v1/consents",
    "/fhir/Patient",
    "/fhir/Observation",
    "/fhir/Condition",
    "/fhir/Encounter",
)

_METHOD_TO_ACTION = {
    "GET": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Write an audit log entry for every PHI-related request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not settings.AUDIT_LOG_ENABLED:
            return await call_next(request)

        path = request.url.path
        is_phi = any(path.startswith(p) for p in _PHI_PREFIXES)

        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = round((time.monotonic() - start) * 1000)

        if not is_phi:
            return response

        # Best-effort audit log; failures here must not break the request.
        try:
            await self._write_audit(request, response, path, elapsed_ms)
        except Exception:
            logger.exception(
                "Failed to write audit log entry for %s %s", request.method, path
            )

        return response

    async def _write_audit(
        self,
        request: Request,
        response: Response,
        path: str,
        elapsed_ms: int,
    ) -> None:
        from app.models.audit_log import AuditLog  # noqa: WPS433

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(token)
        except Exception:
            return

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if not user_id or not tenant_id:
            return

        # Determine resource type from path
        resource_type = "unknown"
        for prefix in _PHI_PREFIXES:
            if path.startswith(prefix):
                resource_type = prefix.rstrip("/").rsplit("/", 1)[-1].lower()
                break

        action = _METHOD_TO_ACTION.get(request.method, "other")

        ip = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent")

        async with async_session_factory() as session:
            from sqlalchemy import text

            schema = _validate_schema_name(tenant_context.get())
            await session.execute(text(f"SET search_path TO {schema}, public"))

            entry = AuditLog(
                id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                user_id=uuid.UUID(user_id),
                action=action,
                resource_type=resource_type,
                resource_id=None,
                details={
                    "path": path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "elapsed_ms": elapsed_ms,
                },
                ip_address=ip,
                user_agent=user_agent,
            )
            session.add(entry)
            await session.commit()
