"""Pydantic schemas for Appointment resources."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppointmentCreate(BaseModel):
    """Schema for creating an appointment."""

    patient_id: UUID
    practitioner_id: UUID
    start_time: datetime
    end_time: datetime
    status: str = Field(
        "booked",
        pattern=r"^(proposed|booked|arrived|fulfilled|cancelled|noshow)$",
    )
    appointment_type: str = Field(
        "routine",
        pattern=r"^(routine|followup|walkin|emergency)$",
    )
    reason: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_times(self) -> "AppointmentCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(proposed|booked|arrived|fulfilled|cancelled|noshow)$",
    )
    reason: Optional[str] = None
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Schema returned for a single appointment."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    practitioner_id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    appointment_type: str
    reason: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
