"""Pydantic schemas for Patient resources."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientCreate(BaseModel):
    """Schema for creating a new patient."""

    mrn: str = Field(..., min_length=4, max_length=20, examples=["MRN-001234"])
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    dob: date
    gender: str = Field(..., pattern=r"^(male|female|other|unknown)$")
    ssn: Optional[str] = Field(
        None, pattern=r"^\d{3}-\d{2}-\d{4}$", description="Will be encrypted at rest"
    )
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    insurance_data: Optional[Dict[str, Any]] = None


class PatientUpdate(BaseModel):
    """Schema for updating an existing patient.  All fields optional."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    dob: Optional[date] = None
    gender: Optional[str] = Field(None, pattern=r"^(male|female|other|unknown)$")
    ssn: Optional[str] = Field(None, pattern=r"^\d{3}-\d{2}-\d{4}$")
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    insurance_data: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class PatientResponse(BaseModel):
    """Schema returned for a single patient."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    mrn: str
    first_name: str
    last_name: str
    dob: date
    gender: str
    address: Optional[Dict[str, Any]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_data: Optional[Dict[str, Any]] = None
    active: bool
    created_at: datetime
    updated_at: datetime


class PatientList(BaseModel):
    """Paginated list of patients."""

    items: List[PatientResponse]
    total: int
    page: int
    page_size: int
    pages: int
