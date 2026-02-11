"""Pydantic schemas for Order resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderCreate(BaseModel):
    """Schema for creating an order."""

    patient_id: UUID
    encounter_id: Optional[UUID] = None
    order_type: str = Field(..., pattern=r"^(lab|imaging|referral)$")
    code: str = Field(..., max_length=20)
    display: str = Field(..., max_length=255)
    status: str = Field(
        "active", pattern=r"^(draft|active|completed|cancelled)$"
    )
    priority: str = Field(
        "routine", pattern=r"^(routine|urgent|stat|asap)$"
    )
    ordering_provider_id: Optional[UUID] = None
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    """Schema for updating an order."""

    status: Optional[str] = Field(
        None, pattern=r"^(draft|active|completed|cancelled)$"
    )
    priority: Optional[str] = Field(
        None, pattern=r"^(routine|urgent|stat|asap)$"
    )
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    """Schema returned for a single order."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    order_type: str
    code: str
    display: str
    status: str
    priority: str
    ordering_provider_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
