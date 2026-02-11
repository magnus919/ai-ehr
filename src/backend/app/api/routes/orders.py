"""
Order CRUD routes with drug interaction checking.

GET    /orders                       - List orders
GET    /orders/{id}                  - Get a single order
POST   /orders                       - Create an order
PUT    /orders/{id}                  - Update an order
POST   /orders/drug-interaction-check - Check for drug interactions
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.medication import MedicationRequest
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[OrderResponse], summary="List orders")
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    order_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[OrderResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Order).where(Order.tenant_id == tenant_id)
    if patient_id:
        stmt = stmt.where(Order.patient_id == patient_id)
    if order_type:
        stmt = stmt.where(Order.order_type == order_type)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    stmt = stmt.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [OrderResponse.model_validate(o) for o in result.scalars().all()]


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order")
async def get_order(
    order_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="order",
        resource_id=order_id,
    )

    return OrderResponse.model_validate(order)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an order",
)
async def create_order(
    payload: OrderCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    order = Order(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        **payload.model_dump(),
    )
    db.add(order)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="create",
        resource_type="order",
        resource_id=order.id,
    )

    return OrderResponse.model_validate(order)


@router.put("/{order_id}", response_model=OrderResponse, summary="Update an order")
async def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OrderResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Order).where(Order.id == order_id, Order.tenant_id == tenant_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="order",
        resource_id=order_id,
    )

    return OrderResponse.model_validate(order)


# ── Drug Interaction Check ───────────────────────────────────────────────

class DrugInteractionRequest(OrderCreate):
    """Extends OrderCreate with a list of current medications for checking."""
    pass


class DrugInteractionResult(OrderCreate):
    """Result of a drug interaction check."""
    pass


@router.post(
    "/drug-interaction-check",
    summary="Check for drug interactions",
    response_model=Dict[str, Any],
)
async def drug_interaction_check(
    patient_id: uuid.UUID = Query(...),
    medication_code: str = Query(..., description="Code of the new medication to check"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Check a proposed medication against a patient's active medications.

    This is a simplified implementation.  In production this would integrate
    with an external drug interaction database (e.g. RxNorm, FDB, Medi-Span).
    """
    tenant_id = uuid.UUID(current_user.tenant_id)

    # Fetch active medications for the patient
    stmt = select(MedicationRequest).where(
        MedicationRequest.tenant_id == tenant_id,
        MedicationRequest.patient_id == patient_id,
        MedicationRequest.status == "active",
    )
    result = await db.execute(stmt)
    active_meds = result.scalars().all()

    # Simplified interaction check – flag if the same medication is already
    # prescribed (duplicate therapy).  A real implementation would call out
    # to a drug-drug interaction API.
    interactions: List[Dict[str, Any]] = []
    for med in active_meds:
        if med.medication_code == medication_code:
            interactions.append(
                {
                    "severity": "warning",
                    "type": "duplicate-therapy",
                    "description": (
                        f"Patient already has an active prescription for "
                        f"{med.medication_display} ({med.medication_code})"
                    ),
                    "existing_medication": {
                        "code": med.medication_code,
                        "display": med.medication_display,
                        "dosage": med.dosage,
                    },
                }
            )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="drug_interaction_check",
        details={
            "patient_id": str(patient_id),
            "medication_code": medication_code,
            "interactions_found": len(interactions),
        },
    )

    return {
        "patient_id": str(patient_id),
        "medication_code": medication_code,
        "interactions": interactions,
        "has_interactions": len(interactions) > 0,
    }
