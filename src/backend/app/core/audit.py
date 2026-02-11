"""
Audit logging module for PHI access tracking.

Every access to Protected Health Information (PHI) is recorded in an
append-only audit_log table.  The ``record_audit`` helper can be called
explicitly from route handlers, and the ``AuditMiddleware`` captures
request-level metadata automatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


async def record_audit(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    """Insert an immutable audit log entry.

    This function imports the AuditLog model lazily to avoid circular
    imports at module load time.
    """
    if not settings.AUDIT_LOG_ENABLED:
        return

    from app.models.audit_log import AuditLog  # noqa: WPS433

    stmt = insert(AuditLog).values(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        timestamp=datetime.now(timezone.utc),
    )
    await db.execute(stmt)
