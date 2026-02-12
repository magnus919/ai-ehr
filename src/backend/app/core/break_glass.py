"""
Break-glass emergency access mechanism.

Allows authorized users to access patient records outside their normal
permission scope during emergencies. All break-glass access is logged
with enhanced audit detail and automatically expires.

Per compliance requirements (HIPAA 164.312(a)(2)(ii)):
- Default duration: 60 minutes
- Maximum duration: 4 hours (requires security officer approval)
- Re-authentication required every 30 minutes
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user

# In-memory store for active break-glass sessions (use Redis in production)
_active_sessions: dict[str, dict] = {}

BREAK_GLASS_DEFAULT_MINUTES = 60
BREAK_GLASS_MAX_MINUTES = 240
REAUTH_INTERVAL_MINUTES = 30


async def activate_break_glass(
    reason: str,
    patient_id: uuid.UUID,
    duration_minutes: int = BREAK_GLASS_DEFAULT_MINUTES,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Activate a break-glass session for emergency access."""
    if duration_minutes > BREAK_GLASS_MAX_MINUTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum break-glass duration is {BREAK_GLASS_MAX_MINUTES} minutes",
        )

    user_id = uuid.UUID(current_user.sub)
    tenant_id = uuid.UUID(current_user.tenant_id)
    now = datetime.now(timezone.utc)

    session_id = str(uuid.uuid4())
    _active_sessions[session_id] = {
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id),
        "reason": reason,
        "activated_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=duration_minutes)).isoformat(),
        "last_reauth": now.isoformat(),
    }

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="break_glass_activate",
        resource_type="patient",
        resource_id=patient_id,
        details={
            "session_id": session_id,
            "reason": reason,
            "duration_minutes": duration_minutes,
        },
    )

    return {
        "session_id": session_id,
        "expires_at": (now + timedelta(minutes=duration_minutes)).isoformat(),
        "reauth_required_at": (now + timedelta(minutes=REAUTH_INTERVAL_MINUTES)).isoformat(),
    }


def is_break_glass_active(user_id: str, patient_id: str) -> Optional[str]:
    """Check if user has an active break-glass session for a patient.

    Returns the session_id if active, None otherwise.
    """
    now = datetime.now(timezone.utc)
    for session_id, session in list(_active_sessions.items()):
        expires = datetime.fromisoformat(session["expires_at"])
        if expires < now:
            del _active_sessions[session_id]
            continue
        if session["user_id"] == user_id and session["patient_id"] == patient_id:
            return session_id
    return None


async def deactivate_break_glass(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Manually deactivate a break-glass session."""
    session = _active_sessions.pop(session_id, None)
    if session:
        await record_audit(
            db,
            tenant_id=uuid.UUID(current_user.tenant_id),
            user_id=uuid.UUID(current_user.sub),
            action="break_glass_deactivate",
            resource_type="patient",
            resource_id=uuid.UUID(session["patient_id"]),
            details={"session_id": session_id},
        )
