"""
Appointment CRUD routes with scheduling logic.

GET    /appointments             - List appointments
GET    /appointments/{id}        - Get a single appointment
POST   /appointments             - Book an appointment (with overlap detection)
PUT    /appointments/{id}        - Update an appointment
DELETE /appointments/{id}        - Cancel an appointment
GET    /appointments/availability - Check practitioner availability
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)

router = APIRouter(prefix="/appointments", tags=["Appointments"])


# ── Helpers ──────────────────────────────────────────────────────────────

async def _check_overlap(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    practitioner_id: uuid.UUID,
    start_time: datetime,
    end_time: datetime,
    exclude_id: uuid.UUID | None = None,
) -> None:
    """Raise 409 if the proposed time slot overlaps an existing appointment."""
    stmt = select(Appointment).where(
        Appointment.tenant_id == tenant_id,
        Appointment.practitioner_id == practitioner_id,
        Appointment.status.in_(["proposed", "booked", "arrived"]),
        # Overlap condition: existing.start < new.end AND existing.end > new.start
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
    )
    if exclude_id:
        stmt = stmt.where(Appointment.id != exclude_id)

    result = await db.execute(stmt)
    conflict = result.scalar_one_or_none()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Time slot conflicts with existing appointment "
                f"{conflict.id} ({conflict.start_time} - {conflict.end_time})"
            ),
        )


# ── CRUD ─────────────────────────────────────────────────────────────────

@router.get("", response_model=List[AppointmentResponse], summary="List appointments")
async def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    practitioner_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AppointmentResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Appointment).where(Appointment.tenant_id == tenant_id)

    if patient_id:
        stmt = stmt.where(Appointment.patient_id == patient_id)
    if practitioner_id:
        stmt = stmt.where(Appointment.practitioner_id == practitioner_id)
    if status_filter:
        stmt = stmt.where(Appointment.status == status_filter)
    if from_date:
        stmt = stmt.where(Appointment.start_time >= from_date)
    if to_date:
        stmt = stmt.where(Appointment.end_time <= to_date)

    stmt = stmt.order_by(Appointment.start_time).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    return [AppointmentResponse.model_validate(a) for a in result.scalars().all()]


@router.get(
    "/availability",
    summary="Check practitioner availability",
)
async def check_availability(
    practitioner_id: uuid.UUID = Query(...),
    date: datetime = Query(..., description="Date to check (time portion ignored)"),
    slot_duration_minutes: int = Query(30, ge=15, le=120),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Return available time slots for a practitioner on a given date.

    Assumes a working day of 08:00 - 17:00.  In production this would
    consult the practitioner's schedule/calendar.
    """
    tenant_id = uuid.UUID(current_user.tenant_id)
    day_start = date.replace(hour=8, minute=0, second=0, microsecond=0)
    day_end = date.replace(hour=17, minute=0, second=0, microsecond=0)

    # Fetch booked appointments for that day
    stmt = select(Appointment).where(
        Appointment.tenant_id == tenant_id,
        Appointment.practitioner_id == practitioner_id,
        Appointment.status.in_(["proposed", "booked", "arrived"]),
        Appointment.start_time >= day_start,
        Appointment.end_time <= day_end,
    ).order_by(Appointment.start_time)
    result = await db.execute(stmt)
    booked = result.scalars().all()

    # Build free slots
    slot_delta = timedelta(minutes=slot_duration_minutes)
    available_slots = []
    cursor = day_start

    booked_ranges = [(a.start_time, a.end_time) for a in booked]

    while cursor + slot_delta <= day_end:
        slot_end = cursor + slot_delta
        is_free = True
        for bs, be in booked_ranges:
            if cursor < be and slot_end > bs:
                is_free = False
                break
        if is_free:
            available_slots.append(
                {
                    "start": cursor.isoformat(),
                    "end": slot_end.isoformat(),
                }
            )
        cursor += slot_delta

    return {
        "practitioner_id": str(practitioner_id),
        "date": date.date().isoformat(),
        "slot_duration_minutes": slot_duration_minutes,
        "available_slots": available_slots,
    }


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment",
)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="appointment",
        resource_id=appointment_id,
    )

    return AppointmentResponse.model_validate(appt)


@router.post(
    "",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book an appointment",
)
async def create_appointment(
    payload: AppointmentCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)

    # Check for scheduling conflicts
    await _check_overlap(
        db, tenant_id, payload.practitioner_id, payload.start_time, payload.end_time
    )

    appt = Appointment(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        **payload.model_dump(),
    )
    db.add(appt)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="appointment",
        resource_id=appt.id,
    )

    return AppointmentResponse.model_validate(appt)


@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update an appointment",
)
async def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AppointmentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If times are being changed, re-check for overlap
    new_start = update_data.get("start_time", appt.start_time)
    new_end = update_data.get("end_time", appt.end_time)
    if "start_time" in update_data or "end_time" in update_data:
        await _check_overlap(
            db, tenant_id, appt.practitioner_id, new_start, new_end,
            exclude_id=appointment_id,
        )

    for field, value in update_data.items():
        setattr(appt, field, value)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="appointment",
        resource_id=appointment_id,
    )

    return AppointmentResponse.model_validate(appt)


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel an appointment",
)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    appt = result.scalar_one_or_none()
    if not appt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    appt.status = "cancelled"
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="delete",
        resource_type="appointment",
        resource_id=appointment_id,
    )
