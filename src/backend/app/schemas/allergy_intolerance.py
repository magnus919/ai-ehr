"""Pydantic schemas for AllergyIntolerance resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AllergyIntoleranceCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    clinical_status: str = Field("active", pattern=r"^(active|inactive|resolved)$")
    verification_status: str = Field(
        "confirmed",
        pattern=r"^(unconfirmed|presumed|confirmed|refuted|entered-in-error)$",
    )
    type: str = Field("allergy", pattern=r"^(allergy|intolerance)$")
    category: Optional[List[str]] = None
    criticality: Optional[str] = Field(None, pattern=r"^(low|high|unable-to-assess)$")
    code_system: str = Field("SNOMED-CT", max_length=50)
    code: str = Field(..., max_length=20)
    code_display: str = Field(..., max_length=255)
    onset_datetime: Optional[datetime] = None
    recorder_id: Optional[UUID] = None
    note: Optional[str] = None
    reaction: Optional[Dict[str, Any]] = None


class AllergyIntoleranceUpdate(BaseModel):
    clinical_status: Optional[str] = Field(
        None, pattern=r"^(active|inactive|resolved)$"
    )
    verification_status: Optional[str] = Field(
        None,
        pattern=r"^(unconfirmed|presumed|confirmed|refuted|entered-in-error)$",
    )
    criticality: Optional[str] = Field(None, pattern=r"^(low|high|unable-to-assess)$")
    note: Optional[str] = None
    reaction: Optional[Dict[str, Any]] = None


class AllergyIntoleranceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    clinical_status: str
    verification_status: str
    type: str
    category: Optional[List[str]] = None
    criticality: Optional[str] = None
    code_system: str
    code: str
    code_display: str
    onset_datetime: Optional[datetime] = None
    recorded_date: datetime
    recorder_id: Optional[UUID] = None
    note: Optional[str] = None
    reaction: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    version: int
