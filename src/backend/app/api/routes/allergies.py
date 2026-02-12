"""
AllergyIntolerance CRUD routes.

GET    /allergies             - List allergies (filterable by patient)
GET    /allergies/{id}        - Get a single allergy
POST   /allergies             - Create an allergy record
PUT    /allergies/{id}        - Update an allergy record
DELETE /allergies/{id}        - Deactivate an allergy record
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
from app.models.allergy_intolerance import AllergyIntolerance
from app.schemas.allergy_intolerance import (
    AllergyIntoleranceCreate,
    AllergyIntoleranceResponse,
    AllergyIntoleranceUpdate,
)

router = APIRouter(prefix="/allergies", tags=["Allergies"])


@router.get(
    "", response_model=List[AllergyIntoleranceResponse], summary="List allergies"
)
async def list_allergies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    clinical_status: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[AllergyIntoleranceResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(AllergyIntolerance).where(AllergyIntolerance.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(AllergyIntolerance.patient_id == patient_id)
    if clinical_status:
        stmt = stmt.where(AllergyIntolerance.clinical_status == clinical_status)
    stmt = (
        stmt.order_by(AllergyIntolerance.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    return [
        AllergyIntoleranceResponse.model_validate(a) for a in result.scalars().all()
    ]


@router.get(
    "/{allergy_id}", response_model=AllergyIntoleranceResponse, summary="Get allergy"
)
async def get_allergy(
    allergy_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AllergyIntoleranceResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(AllergyIntolerance).where(
        AllergyIntolerance.id == allergy_id,
        AllergyIntolerance.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    allergy = result.scalar_one_or_none()
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found"
        )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="allergy_intolerance",
        resource_id=allergy_id,
    )

    return AllergyIntoleranceResponse.model_validate(allergy)


@router.post(
    "",
    response_model=AllergyIntoleranceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create allergy record",
)
async def create_allergy(
    payload: AllergyIntoleranceCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AllergyIntoleranceResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    allergy = AllergyIntolerance(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(),
    )
    db.add(allergy)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="allergy_intolerance",
        resource_id=allergy.id,
    )

    return AllergyIntoleranceResponse.model_validate(allergy)


@router.put(
    "/{allergy_id}",
    response_model=AllergyIntoleranceResponse,
    summary="Update allergy record",
)
async def update_allergy(
    allergy_id: uuid.UUID,
    payload: AllergyIntoleranceUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AllergyIntoleranceResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(AllergyIntolerance).where(
        AllergyIntolerance.id == allergy_id,
        AllergyIntolerance.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    allergy = result.scalar_one_or_none()
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(allergy, field, value)
    allergy.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="allergy_intolerance",
        resource_id=allergy_id,
    )

    return AllergyIntoleranceResponse.model_validate(allergy)


@router.delete(
    "/{allergy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate allergy record",
)
async def deactivate_allergy(
    allergy_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(AllergyIntolerance).where(
        AllergyIntolerance.id == allergy_id,
        AllergyIntolerance.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    allergy = result.scalar_one_or_none()
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Allergy not found"
        )

    allergy.clinical_status = "inactive"
    allergy.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="delete",
        resource_type="allergy_intolerance",
        resource_id=allergy_id,
    )
