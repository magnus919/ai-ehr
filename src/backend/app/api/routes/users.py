"""
User management routes (admin operations).

GET    /users           - List users
GET    /users/{id}      - Get a user
PUT    /users/{id}      - Update a user
POST   /users/{id}/roles - Assign role to user
DELETE /users/{id}/roles/{role_id} - Remove role from user
"""

from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user, require_role
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["User Management"])

VALID_ROLES = {"admin", "practitioner", "nurse", "staff", "patient", "psychiatrist", "psychologist"}


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List users",
    dependencies=[Depends(require_role("admin"))],
)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    role: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(User).where(User.tenant_id == tenant_id)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if role:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user",
)
async def get_user(
    user_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)

    # Users can view their own profile; admins can view anyone
    if str(user_id) != current_user.sub and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own profile",
        )

    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)

    # Non-admins can only update their own profile (but not role)
    is_self = str(user_id) == current_user.sub
    if not is_self and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "role" in update_data:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change user roles",
            )
        if update_data["role"] not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Must be one of: {', '.join(sorted(VALID_ROLES))}",
            )
        if is_self:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role",
            )

    stmt = select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="user",
        resource_id=user_id,
        details={"fields_changed": list(update_data.keys())},
    )

    return UserResponse.model_validate(user)
