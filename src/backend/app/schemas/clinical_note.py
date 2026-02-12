"""Pydantic schemas for ClinicalNote resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClinicalNoteCreate(BaseModel):
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    note_type: str = Field(
        ...,
        pattern=r"^(progress|soap|h_and_p|discharge|procedure|consultation)$",
    )
    content: str = Field(
        ..., min_length=1, description="Plain text content (will be encrypted at rest)"
    )
    is_psychotherapy_note: bool = False
    is_42cfr_part2: bool = False


class ClinicalNoteUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = Field(
        None,
        pattern=r"^(in-progress|completed|amended|entered-in-error)$",
    )


class ClinicalNoteSign(BaseModel):
    """Request to sign a clinical note."""

    pass


class ClinicalNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    encounter_id: Optional[UUID] = None
    note_type: str
    status: str
    author_id: UUID
    is_psychotherapy_note: bool
    is_42cfr_part2: bool
    signed_at: Optional[datetime] = None
    signed_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    version: int
