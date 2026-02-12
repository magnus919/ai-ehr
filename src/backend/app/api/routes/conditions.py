"""
Standalone Condition (diagnosis) routes.

GET    /conditions           - List/search conditions
GET    /conditions/{id}      - Get a single condition
POST   /conditions           - Create a condition
PUT    /conditions/{id}      - Update a condition
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
from app.models.condition import Condition
from app.schemas.condition import ConditionCreate, ConditionResponse, ConditionUpdate

router = APIRouter(prefix="/conditions", tags=["Conditions"])


@router.get("", response_model=List[ConditionResponse], summary="List conditions")
async def list_conditions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    clinical_status: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConditionResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Condition).where(Condition.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Condition.patient_id == patient_id)
    if clinical_status:
        stmt = stmt.where(Condition.clinical_status == clinical_status)
    stmt = (
        stmt.order_by(Condition.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    return [ConditionResponse.model_validate(c) for c in result.scalars().all()]


@router.get(
    "/{condition_id}", response_model=ConditionResponse, summary="Get condition"
)
async def get_condition(
    condition_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConditionResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Condition).where(
        Condition.id == condition_id,
        Condition.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    cond = result.scalar_one_or_none()
    if not cond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found"
        )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="condition",
        resource_id=condition_id,
    )

    return ConditionResponse.model_validate(cond)


@router.post(
    "",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a condition",
)
async def create_condition(
    payload: ConditionCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConditionResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    cond = Condition(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(),
    )
    db.add(cond)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="condition",
        resource_id=cond.id,
    )

    return ConditionResponse.model_validate(cond)


@router.put(
    "/{condition_id}",
    response_model=ConditionResponse,
    summary="Update a condition",
)
async def update_condition(
    condition_id: uuid.UUID,
    payload: ConditionUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConditionResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Condition).where(
        Condition.id == condition_id,
        Condition.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    cond = result.scalar_one_or_none()
    if not cond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found"
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cond, field, value)
    cond.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="condition",
        resource_id=condition_id,
    )

    return ConditionResponse.model_validate(cond)
