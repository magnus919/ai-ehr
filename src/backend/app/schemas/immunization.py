"""Pydantic schemas for Immunization resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImmunizationCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    status: str = Field(
        "completed",
        pattern=r"^(completed|entered-in-error|not-done)$",
    )
    vaccine_code: str = Field(..., max_length=20)
    vaccine_code_system: str = Field("CVX", max_length=50)
    vaccine_display: str = Field(..., max_length=255)
    occurrence_datetime: datetime
    lot_number: Optional[str] = Field(None, max_length=50)
    site_code: Optional[str] = Field(None, max_length=30)
    route_code: Optional[str] = Field(None, max_length=30)
    dose_quantity: Optional[float] = None
    performer_id: Optional[UUID] = None
    note: Optional[str] = None


class ImmunizationUpdate(BaseModel):
    status: Optional[str] = Field(
        None,
        pattern=r"^(completed|entered-in-error|not-done)$",
    )
    lot_number: Optional[str] = Field(None, max_length=50)
    note: Optional[str] = None


class ImmunizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    status: str
    vaccine_code: str
    vaccine_code_system: str
    vaccine_display: str
    occurrence_datetime: datetime
    lot_number: Optional[str] = None
    site_code: Optional[str] = None
    route_code: Optional[str] = None
    dose_quantity: Optional[float] = None
    performer_id: Optional[UUID] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int
