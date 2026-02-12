"""
Encounter CRUD routes with nested observations and conditions.

GET    /encounters              - List encounters
GET    /encounters/{id}         - Get encounter with nested resources
POST   /encounters              - Create an encounter
PUT    /encounters/{id}         - Update an encounter
GET    /encounters/{id}/observations - List observations for an encounter
POST   /encounters/{id}/observations - Add an observation
GET    /encounters/{id}/conditions   - List conditions for an encounter
POST   /encounters/{id}/conditions   - Add a condition
POST   /encounters/{id}/medications  - Add a medication request
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
from app.models.encounter import Encounter
from app.models.medication import MedicationRequest
from app.models.observation import Observation
from app.schemas.condition import ConditionCreate, ConditionResponse
from app.schemas.encounter import EncounterCreate, EncounterResponse, EncounterUpdate
from app.schemas.medication import MedicationRequestCreate, MedicationRequestResponse
from app.schemas.observation import ObservationCreate, ObservationResponse

router = APIRouter(prefix="/encounters", tags=["Encounters"])


# ── Helpers ──────────────────────────────────────────────────────────────

async def _get_encounter(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    encounter_id: uuid.UUID,
) -> Encounter:
    stmt = select(Encounter).where(
        Encounter.id == encounter_id,
        Encounter.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    enc = result.scalar_one_or_none()
    if not enc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Encounter not found")
    return enc


# ── Encounter CRUD ───────────────────────────────────────────────────────

@router.get("", response_model=List[EncounterResponse], summary="List encounters")
async def list_encounters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[EncounterResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Encounter).where(Encounter.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Encounter.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Encounter.status == status_filter)
    stmt = stmt.order_by(Encounter.start_time.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [EncounterResponse.model_validate(e) for e in result.scalars().all()]


@router.get("/{encounter_id}", response_model=EncounterResponse, summary="Get encounter")
async def get_encounter(
    encounter_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EncounterResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    enc = await _get_encounter(db, tenant_id, encounter_id)

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="encounter",
        resource_id=encounter_id,
    )

    return EncounterResponse.model_validate(enc)


@router.post(
    "",
    response_model=EncounterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an encounter",
)
async def create_encounter(
    payload: EncounterCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EncounterResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    enc = Encounter(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(),
    )
    db.add(enc)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="encounter",
        resource_id=enc.id,
    )

    return EncounterResponse.model_validate(enc)


@router.put("/{encounter_id}", response_model=EncounterResponse, summary="Update encounter")
async def update_encounter(
    encounter_id: uuid.UUID,
    payload: EncounterUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EncounterResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    enc = await _get_encounter(db, tenant_id, encounter_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(enc, field, value)
    enc.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="encounter",
        resource_id=encounter_id,
    )

    return EncounterResponse.model_validate(enc)


# ── Nested: Observations ────────────────────────────────────────────────

@router.get(
    "/{encounter_id}/observations",
    response_model=List[ObservationResponse],
    summary="List observations for encounter",
)
async def encounter_observations(
    encounter_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ObservationResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await _get_encounter(db, tenant_id, encounter_id)

    stmt = select(Observation).where(
        Observation.tenant_id == tenant_id,
        Observation.encounter_id == encounter_id,
    )
    result = await db.execute(stmt)
    return [ObservationResponse.model_validate(o) for o in result.scalars().all()]


@router.post(
    "/{encounter_id}/observations",
    response_model=ObservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add observation to encounter",
)
async def create_observation(
    encounter_id: uuid.UUID,
    payload: ObservationCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ObservationResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await _get_encounter(db, tenant_id, encounter_id)

    obs = Observation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        encounter_id=encounter_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(exclude={"encounter_id"}),
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


# ── Nested: Conditions ──────────────────────────────────────────────────

@router.get(
    "/{encounter_id}/conditions",
    response_model=List[ConditionResponse],
    summary="List conditions for encounter",
)
async def encounter_conditions(
    encounter_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConditionResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await _get_encounter(db, tenant_id, encounter_id)

    stmt = select(Condition).where(
        Condition.tenant_id == tenant_id,
        Condition.encounter_id == encounter_id,
    )
    result = await db.execute(stmt)
    return [ConditionResponse.model_validate(c) for c in result.scalars().all()]


@router.post(
    "/{encounter_id}/conditions",
    response_model=ConditionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add condition to encounter",
)
async def create_condition(
    encounter_id: uuid.UUID,
    payload: ConditionCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConditionResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await _get_encounter(db, tenant_id, encounter_id)

    cond = Condition(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        encounter_id=encounter_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(exclude={"encounter_id"}),
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


# ── Nested: Medications ─────────────────────────────────────────────────

@router.post(
    "/{encounter_id}/medications",
    response_model=MedicationRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add medication request to encounter",
)
async def create_medication_request(
    encounter_id: uuid.UUID,
    payload: MedicationRequestCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MedicationRequestResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    await _get_encounter(db, tenant_id, encounter_id)

    med = MedicationRequest(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        encounter_id=encounter_id,
        created_by=uuid.UUID(current_user.sub),
        **payload.model_dump(exclude={"encounter_id"}),
    )
    db.add(med)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="medication_request",
        resource_id=med.id,
    )

    return MedicationRequestResponse.model_validate(med)
