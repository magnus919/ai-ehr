"""Pydantic schemas for Observation resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ObservationCreate(BaseModel):
    """Schema for creating an observation."""

    patient_id: UUID
    encounter_id: Optional[UUID] = None
    code: str = Field(..., max_length=20)
    code_system: str = Field("LOINC", max_length=50)
    display: str = Field(..., max_length=255)
    value_type: str = Field(
        "numeric", pattern=r"^(numeric|string|boolean|dateTime)$"
    )
    value_string: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=50)
    effective_date: datetime
    status: str = Field(
        "final",
        pattern=r"^(registered|preliminary|final|amended|cancelled)$",
    )
    performer_id: Optional[UUID] = None


class ObservationResponse(BaseModel):
    """Schema returned for a single observation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    code: str
    code_system: str
    display: str
    value_type: str
    value_string: Optional[str] = None
    value_numeric: Optional[float] = None
    unit: Optional[str] = None
    effective_date: datetime
    status: str
    performer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    version: int
