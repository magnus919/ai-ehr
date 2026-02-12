"""Pydantic schemas for Consent resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConsentCreate(BaseModel):
    patient_id: UUID
    scope: str = Field(
        ...,
        pattern=r"^(treatment|research|disclosure|adr|42cfr_part2)$",
    )
    category: str = Field(
        ...,
        pattern=r"^(general|substance-use|psychotherapy|research)$",
    )
    provision_type: str = Field("permit", pattern=r"^(permit|deny)$")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    policy_rule: Optional[str] = Field(None, max_length=200)
    data_scope: Optional[Dict[str, Any]] = None
    note: Optional[str] = None


class ConsentUpdate(BaseModel):
    status: Optional[str] = Field(
        None,
        pattern=r"^(draft|active|inactive|entered-in-error|rejected)$",
    )
    provision_type: Optional[str] = Field(None, pattern=r"^(permit|deny)$")
    period_end: Optional[datetime] = None
    note: Optional[str] = None


class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    status: str
    scope: str
    category: str
    provision_type: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    grantor_id: Optional[UUID] = None
    policy_rule: Optional[str] = None
    data_scope: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    version: int
