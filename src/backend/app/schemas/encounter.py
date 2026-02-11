"""Pydantic schemas for Encounter resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EncounterCreate(BaseModel):
    """Schema for creating an encounter."""

    patient_id: UUID
    practitioner_id: UUID
    encounter_type: str = Field(
        ..., pattern=r"^(ambulatory|emergency|inpatient|virtual)$"
    )
    status: str = Field(
        "planned",
        pattern=r"^(planned|in-progress|completed|cancelled)$",
    )
    start_time: datetime
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class EncounterUpdate(BaseModel):
    """Schema for updating an encounter."""

    status: Optional[str] = Field(
        None,
        pattern=r"^(planned|in-progress|completed|cancelled)$",
    )
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class EncounterResponse(BaseModel):
    """Schema returned for a single encounter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    encounter_type: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    reason: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
