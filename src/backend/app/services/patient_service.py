"""
Patient business logic: CRUD, search, and duplicate detection.
"""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.schemas.patient import (
    PatientCreate,
    PatientList,
    PatientResponse,
    PatientUpdate,
)
from app.utils.encryption import encrypt_value


async def create_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    payload: PatientCreate,
) -> PatientResponse:
    """Create a new patient, encrypting SSN at rest."""

    # Duplicate detection: same MRN within the tenant
    existing = await db.execute(
        select(Patient).where(
            Patient.tenant_id == tenant_id,
            Patient.mrn == payload.mrn,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with MRN {payload.mrn} already exists",
        )

    # Check for potential duplicates by name + DOB
    dup_check = await db.execute(
        select(Patient).where(
            Patient.tenant_id == tenant_id,
            func.lower(Patient.first_name) == payload.first_name.lower(),
            func.lower(Patient.last_name) == payload.last_name.lower(),
            Patient.dob == payload.dob,
        )
    )
    potential_dup = dup_check.scalar_one_or_none()
    if potential_dup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Potential duplicate patient found: "
                f"{potential_dup.first_name} {potential_dup.last_name} "
                f"(MRN {potential_dup.mrn}). "
                f"Use the existing record or provide a distinct MRN."
            ),
        )

    patient = Patient(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        mrn=payload.mrn,
        first_name=payload.first_name,
        last_name=payload.last_name,
        dob=payload.dob,
        gender=payload.gender,
        ssn_encrypted=encrypt_value(payload.ssn) if payload.ssn else None,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        insurance_data=payload.insurance_data,
    )
    db.add(patient)
    await db.flush()
    return PatientResponse.model_validate(patient)


async def get_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> PatientResponse:
    """Fetch a single patient by ID."""

    stmt = select(Patient).where(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    return PatientResponse.model_validate(patient)


async def list_patients(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    active_only: bool = True,
) -> PatientList:
    """Return a paginated list of patients for the tenant."""

    base = select(Patient).where(Patient.tenant_id == tenant_id)
    if active_only:
        base = base.where(Patient.active.is_(True))

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Page
    stmt = (
        base.order_by(Patient.last_name, Patient.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    patients = result.scalars().all()

    return PatientList(
        items=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )


async def update_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
    payload: PatientUpdate,
) -> PatientResponse:
    """Update an existing patient."""

    stmt = select(Patient).where(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Handle SSN encryption
    if "ssn" in update_data:
        ssn = update_data.pop("ssn")
        patient.ssn_encrypted = encrypt_value(ssn) if ssn else None

    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.flush()
    return PatientResponse.model_validate(patient)


async def delete_patient(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    patient_id: uuid.UUID,
) -> None:
    """Soft-delete a patient (set active=False)."""

    stmt = select(Patient).where(
        Patient.id == patient_id,
        Patient.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient.active = False
    await db.flush()


async def search_patients(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    query: str,
    page: int = 1,
    page_size: int = 20,
) -> PatientList:
    """Search patients by name, MRN, email, or phone."""

    search_term = f"%{query.lower()}%"

    base = select(Patient).where(
        Patient.tenant_id == tenant_id,
        Patient.active.is_(True),
        or_(
            func.lower(Patient.first_name).like(search_term),
            func.lower(Patient.last_name).like(search_term),
            Patient.mrn.ilike(search_term),
            Patient.email.ilike(search_term),
            Patient.phone.ilike(search_term),
        ),
    )

    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base.order_by(Patient.last_name, Patient.first_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    patients = result.scalars().all()

    return PatientList(
        items=[PatientResponse.model_validate(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
