"""
Consent management routes.

GET    /consents              - List consents
GET    /consents/{id}         - Get a consent record
POST   /consents              - Create a consent record
PUT    /consents/{id}         - Update a consent record
POST   /consents/{id}/withdraw - Withdraw consent
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.consent import Consent
from app.schemas.consent import ConsentCreate, ConsentResponse, ConsentUpdate

router = APIRouter(prefix="/consents", tags=["Consents"])


@router.get("", response_model=List[ConsentResponse], summary="List consents")
async def list_consents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    scope: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConsentResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Consent).where(Consent.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Consent.patient_id == patient_id)
    if status_filter:
        stmt = stmt.where(Consent.status == status_filter)
    if scope:
        stmt = stmt.where(Consent.scope == scope)
    stmt = stmt.order_by(Consent.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [ConsentResponse.model_validate(c) for c in result.scalars().all()]


@router.get("/{consent_id}", response_model=ConsentResponse, summary="Get consent")
async def get_consent(
    consent_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Consent).where(
        Consent.id == consent_id,
        Consent.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="consent",
        resource_id=consent_id,
    )

    return ConsentResponse.model_validate(consent)


@router.post(
    "",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create consent record",
)
async def create_consent(
    payload: ConsentCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    user_id = uuid.UUID(current_user.sub)

    consent = Consent(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        grantor_id=user_id,
        created_by=user_id,
        **payload.model_dump(),
    )
    db.add(consent)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="create",
        resource_type="consent",
        resource_id=consent.id,
        details={"scope": payload.scope, "category": payload.category},
    )

    return ConsentResponse.model_validate(consent)


@router.put(
    "/{consent_id}",
    response_model=ConsentResponse,
    summary="Update consent record",
)
async def update_consent(
    consent_id: uuid.UUID,
    payload: ConsentUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Consent).where(
        Consent.id == consent_id,
        Consent.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(consent, field, value)
    consent.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="consent",
        resource_id=consent_id,
    )

    return ConsentResponse.model_validate(consent)


@router.post(
    "/{consent_id}/withdraw",
    response_model=ConsentResponse,
    summary="Withdraw consent",
)
async def withdraw_consent(
    consent_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Consent).where(
        Consent.id == consent_id,
        Consent.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    consent = result.scalar_one_or_none()
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")

    if consent.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consent is already withdrawn",
        )

    consent.status = "inactive"
    consent.period_end = datetime.now(timezone.utc)
    consent.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="withdraw",
        resource_type="consent",
        resource_id=consent_id,
        details={"scope": consent.scope, "category": consent.category},
    )

    return ConsentResponse.model_validate(consent)
