"""Pydantic schemas for MedicationRequest resources."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MedicationRequestCreate(BaseModel):
    """Schema for creating a medication request."""

    patient_id: UUID
    encounter_id: Optional[UUID] = None
    medication_code: str = Field(..., max_length=20)
    medication_display: str = Field(..., max_length=255)
    dosage: Optional[str] = Field(None, max_length=200)
    frequency: Optional[str] = Field(None, max_length=100)
    route: Optional[str] = Field(
        None, pattern=r"^(oral|IV|IM|subcutaneous|topical|inhalation|rectal|ophthalmic|otic|nasal|transdermal)$"
    )
    status: str = Field(
        "active",
        pattern=r"^(active|on-hold|cancelled|completed|stopped)$",
    )
    prescriber_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    refills: int = Field(0, ge=0, le=99)


class MedicationRequestResponse(BaseModel):
    """Schema returned for a single medication request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    medication_code: str
    medication_display: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    status: str
    prescriber_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    refills: int
    created_at: datetime
