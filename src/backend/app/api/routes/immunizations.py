"""
Immunization CRUD routes.

GET    /immunizations         - List immunizations
GET    /immunizations/{id}    - Get a single immunization
POST   /immunizations         - Record an immunization
PUT    /immunizations/{id}    - Update an immunization
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.immunization import Immunization
from app.schemas.immunization import (
    ImmunizationCreate,
    ImmunizationResponse,
    ImmunizationUpdate,
)

router = APIRouter(prefix="/immunizations", tags=["Immunizations"])


@router.get("", response_model=List[ImmunizationResponse], summary="List immunizations")
async def list_immunizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    vaccine_code: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ImmunizationResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Immunization).where(Immunization.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Immunization.patient_id == patient_id)
    if vaccine_code:
        stmt = stmt.where(Immunization.vaccine_code == vaccine_code)
    stmt = stmt.order_by(Immunization.occurrence_datetime.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [ImmunizationResponse.model_validate(i) for i in result.scalars().all()]


@router.get("/{immunization_id}", response_model=ImmunizationResponse, summary="Get immunization")
async def get_immunization(
    immunization_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImmunizationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Immunization).where(
        Immunization.id == immunization_id,
        Immunization.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    imm = result.scalar_one_or_none()
    if not imm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Immunization not found")

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="immunization",
        resource_id=immunization_id,
    )

    return ImmunizationResponse.model_validate(imm)


@router.post(
    "",
    response_model=ImmunizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an immunization",
)
async def create_immunization(
    payload: ImmunizationCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImmunizationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    imm = Immunization(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(),
    )
    db.add(imm)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="immunization",
        resource_id=imm.id,
    )

    return ImmunizationResponse.model_validate(imm)


@router.put(
    "/{immunization_id}",
    response_model=ImmunizationResponse,
    summary="Update an immunization",
)
async def update_immunization(
    immunization_id: uuid.UUID,
    payload: ImmunizationUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImmunizationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Immunization).where(
        Immunization.id == immunization_id,
        Immunization.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    imm = result.scalar_one_or_none()
    if not imm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Immunization not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(imm, field, value)
    imm.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="immunization",
        resource_id=immunization_id,
    )

    return ImmunizationResponse.model_validate(imm)
