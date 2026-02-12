"""
Audit log query routes (read-only, admin access).

GET    /audit-logs - Query audit logs with filters
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import TokenPayload, require_role
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogList, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogList,
    summary="Query audit logs",
    dependencies=[Depends(require_role("admin"))],
)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: uuid.UUID | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    current_user: TokenPayload = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> AuditLogList:
    tenant_id = uuid.UUID(current_user.tenant_id)
    base = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

    if user_id:
        base = base.where(AuditLog.user_id == user_id)
    if action:
        base = base.where(AuditLog.action == action)
    if resource_type:
        base = base.where(AuditLog.resource_type == resource_type)
    if resource_id:
        base = base.where(AuditLog.resource_id == resource_id)
    if from_date:
        base = base.where(AuditLog.timestamp >= from_date)
    if to_date:
        base = base.where(AuditLog.timestamp <= to_date)

    # Count total
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Fetch page
    stmt = base.order_by(AuditLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    items = [AuditLogResponse.model_validate(a) for a in result.scalars().all()]

    return AuditLogList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
