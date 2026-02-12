"""
Standalone Observation routes (vitals, lab results).

GET    /observations         - List/search observations
GET    /observations/{id}    - Get a single observation
POST   /observations         - Create an observation
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
from app.models.observation import Observation
from app.schemas.observation import ObservationCreate, ObservationResponse

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get("", response_model=List[ObservationResponse], summary="List observations")
async def list_observations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    code: str | None = Query(None, description="LOINC code filter"),
    status_filter: str | None = Query(None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ObservationResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Observation).where(Observation.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Observation.patient_id == patient_id)
    if code:
        stmt = stmt.where(Observation.code == code)
    if status_filter:
        stmt = stmt.where(Observation.status == status_filter)
    stmt = (
        stmt.order_by(Observation.effective_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(stmt)
    return [ObservationResponse.model_validate(o) for o in result.scalars().all()]


@router.get(
    "/{observation_id}", response_model=ObservationResponse, summary="Get observation"
)
async def get_observation(
    observation_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ObservationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Observation).where(
        Observation.id == observation_id,
        Observation.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    obs = result.scalar_one_or_none()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found"
        )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="observation",
        resource_id=observation_id,
    )

    return ObservationResponse.model_validate(obs)


@router.post(
    "",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an observation",
)
async def create_observation(
    payload: ObservationCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ObservationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    obs = Observation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(),
    )
    db.add(obs)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="observation",
        resource_id=obs.id,
    )

    return ObservationResponse.model_validate(obs)
