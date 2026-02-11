"""Pydantic schemas for Condition resources."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConditionCreate(BaseModel):
    """Schema for creating a condition."""

    patient_id: UUID
    encounter_id: Optional[UUID] = None
    code: str = Field(..., max_length=20)
    code_system: str = Field("ICD-10", max_length=50)
    display: str = Field(..., max_length=255)
    clinical_status: str = Field(
        "active",
        pattern=r"^(active|recurrence|relapse|inactive|remission|resolved)$",
    )
    verification_status: str = Field(
        "confirmed",
        pattern=r"^(unconfirmed|provisional|differential|confirmed|refuted)$",
    )
    onset_date: Optional[date] = None
    abatement_date: Optional[date] = None
    recorder_id: Optional[UUID] = None


class ConditionResponse(BaseModel):
    """Schema returned for a single condition."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    code: str
    code_system: str
    display: str
    clinical_status: str
    verification_status: str
    onset_date: Optional[date] = None
    abatement_date: Optional[date] = None
    recorder_id: Optional[UUID] = None
    created_at: datetime
