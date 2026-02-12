"""Pydantic schemas for Role and Permission resources."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_type: str
    operation: str
    description: Optional[str] = None


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_system_role: bool = False
    permission_ids: List[UUID] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[UUID]] = None


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    is_system_role: bool
    permissions: List[PermissionResponse] = []
    created_at: datetime
    updated_at: datetime


class UserRoleAssign(BaseModel):
    role_id: UUID


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    role_id: UUID
    assigned_at: datetime
    assigned_by: Optional[UUID] = None
