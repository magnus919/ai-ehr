"""
Patient CRUD routes.

GET    /patients             - List patients (paginated)
GET    /patients/search      - Search patients by name/MRN/email/phone
GET    /patients/{id}        - Get a single patient
POST   /patients             - Create a patient
PUT    /patients/{id}        - Update a patient
DELETE /patients/{id}        - Soft-delete a patient
GET    /patients/{id}/encounters - List encounters for a patient
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.encounter import Encounter
from app.schemas.encounter import EncounterResponse
from app.schemas.patient import (
    PatientCreate,
    PatientList,
    PatientResponse,
    PatientUpdate,
)
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "",
    response_model=PatientList,
    summary="List patients",
)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(True),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientList:
    tenant_id = uuid.UUID(current_user.tenant_id)
    return await patient_service.list_patients(
        db, tenant_id, page=page, page_size=page_size, active_only=active_only
    )


@router.get(
    "/search",
    response_model=PatientList,
    summary="Search patients",
)
async def search_patients(
    q: str = Query(..., min_length=1, description="Search term"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientList:
    tenant_id = uuid.UUID(current_user.tenant_id)
    return await patient_service.search_patients(
        db, tenant_id, query=q, page=page, page_size=page_size
    )


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get a patient by ID",
)
async def get_patient(
    patient_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="patient",
        resource_id=patient_id,
    )

    return await patient_service.get_patient(db, tenant_id, patient_id)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a patient",
)
async def create_patient(
    payload: PatientCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    result = await patient_service.create_patient(db, tenant_id, payload)

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="patient",
        resource_id=result.id,
    )

    return result


@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update a patient",
)
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PatientResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    result = await patient_service.update_patient(db, tenant_id, patient_id, payload)

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="patient",
        resource_id=patient_id,
    )

    return result


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a patient",
)
async def delete_patient(
    patient_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await patient_service.delete_patient(db, tenant_id, patient_id)

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="delete",
        resource_type="patient",
        resource_id=patient_id,
    )


@router.get(
    "/{patient_id}/encounters",
    response_model=List[EncounterResponse],
    summary="List encounters for a patient",
)
async def patient_encounters(
    patient_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[EncounterResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)

    # Verify patient exists in this tenant
    await patient_service.get_patient(db, tenant_id, patient_id)

    stmt = (
        select(Encounter)
        .where(
            Encounter.tenant_id == tenant_id,
            Encounter.patient_id == patient_id,
        )
        .order_by(Encounter.start_time.desc())
    )
    result = await db.execute(stmt)
    encounters = result.scalars().all()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="encounter",
        details={"patient_id": str(patient_id), "count": len(encounters)},
    )

    return [EncounterResponse.model_validate(e) for e in encounters]
