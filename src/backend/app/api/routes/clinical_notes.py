"""
Clinical Notes CRUD routes with signing workflow.

GET    /clinical-notes             - List clinical notes
GET    /clinical-notes/{id}        - Get a single clinical note
POST   /clinical-notes             - Create a clinical note
PUT    /clinical-notes/{id}        - Update a clinical note
POST   /clinical-notes/{id}/sign   - Sign a clinical note
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.clinical_note import ClinicalNote
from app.schemas.clinical_note import (
    ClinicalNoteCreate,
    ClinicalNoteResponse,
    ClinicalNoteUpdate,
)

router = APIRouter(prefix="/clinical-notes", tags=["Clinical Notes"])

# Roles authorized to access psychotherapy notes per HIPAA 164.508(a)(2)
_PSYCHOTHERAPY_AUTHORIZED_ROLES = frozenset({"admin", "psychiatrist", "psychologist"})


def _encrypt_content(content: str) -> tuple[bytes, str]:
    """Encrypt note content using Fernet and return (encrypted_bytes, content_hash).

    The SHA-256 hash is computed on the plaintext for integrity verification
    before encryption.  The encrypted bytes are stored as BYTEA in the database.
    """
    from app.utils.encryption import _get_fernet

    content_bytes = content.encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    fernet = _get_fernet()
    encrypted = fernet.encrypt(content_bytes)
    return encrypted, content_hash


def _decrypt_content(encrypted: bytes | None) -> str | None:
    """Decrypt note content using Fernet."""
    if encrypted is None:
        return None
    from app.utils.encryption import _get_fernet

    fernet = _get_fernet()
    return fernet.decrypt(encrypted).decode("utf-8")


@router.get("", response_model=List[ClinicalNoteResponse], summary="List clinical notes")
async def list_clinical_notes(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    patient_id: uuid.UUID | None = Query(None),
    encounter_id: uuid.UUID | None = Query(None),
    note_type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ClinicalNoteResponse]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(ClinicalNote).where(ClinicalNote.tenant_id == tenant_id)

    # Filter out psychotherapy notes unless user has appropriate role
    if current_user.role not in _PSYCHOTHERAPY_AUTHORIZED_ROLES:
        stmt = stmt.where(ClinicalNote.is_psychotherapy_note == False)

    if patient_id:
        stmt = stmt.where(ClinicalNote.patient_id == patient_id)
    if encounter_id:
        stmt = stmt.where(ClinicalNote.encounter_id == encounter_id)
    if note_type:
        stmt = stmt.where(ClinicalNote.note_type == note_type)
    if status_filter:
        stmt = stmt.where(ClinicalNote.status == status_filter)

    stmt = stmt.order_by(ClinicalNote.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(stmt)
    return [ClinicalNoteResponse.model_validate(n) for n in result.scalars().all()]


@router.get("/{note_id}", response_model=ClinicalNoteResponse, summary="Get clinical note")
async def get_clinical_note(
    note_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalNoteResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(ClinicalNote).where(
        ClinicalNote.id == note_id,
        ClinicalNote.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical note not found")

    # Psychotherapy notes require special authorization (HIPAA 164.508(a)(2))
    if note.is_psychotherapy_note and current_user.role not in _PSYCHOTHERAPY_AUTHORIZED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Psychotherapy notes require specific authorization per HIPAA 164.508(a)(2)",
        )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="clinical_note",
        resource_id=note_id,
        details={"is_psychotherapy_note": note.is_psychotherapy_note},
    )

    return ClinicalNoteResponse.model_validate(note)


@router.post(
    "",
    response_model=ClinicalNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a clinical note",
)
async def create_clinical_note(
    payload: ClinicalNoteCreate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalNoteResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    user_id = uuid.UUID(current_user.sub)

    encrypted_content, content_hash = _encrypt_content(payload.content)

    note = ClinicalNote(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        patient_id=payload.patient_id,
        encounter_id=payload.encounter_id,
        note_type=payload.note_type,
        status="in-progress",
        author_id=user_id,
        content_encrypted=encrypted_content,
        content_hash=content_hash,
        is_psychotherapy_note=payload.is_psychotherapy_note,
        is_42cfr_part2=payload.is_42cfr_part2,
        created_by=user_id,
    )
    db.add(note)
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="create",
        resource_type="clinical_note",
        resource_id=note.id,
        details={
            "note_type": payload.note_type,
            "is_psychotherapy_note": payload.is_psychotherapy_note,
        },
    )

    return ClinicalNoteResponse.model_validate(note)


@router.put(
    "/{note_id}",
    response_model=ClinicalNoteResponse,
    summary="Update a clinical note",
)
async def update_clinical_note(
    note_id: uuid.UUID,
    payload: ClinicalNoteUpdate,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalNoteResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(ClinicalNote).where(
        ClinicalNote.id == note_id,
        ClinicalNote.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical note not found")

    if note.status == "signed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot edit a signed note. Create an amendment instead.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "content" in update_data:
        encrypted_content, content_hash = _encrypt_content(update_data.pop("content"))
        note.content_encrypted = encrypted_content
        note.content_hash = content_hash

    for field, value in update_data.items():
        setattr(note, field, value)
    note.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="update",
        resource_type="clinical_note",
        resource_id=note_id,
    )

    return ClinicalNoteResponse.model_validate(note)


@router.post(
    "/{note_id}/sign",
    response_model=ClinicalNoteResponse,
    summary="Sign a clinical note",
)
async def sign_clinical_note(
    note_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClinicalNoteResponse:
    tenant_id = uuid.UUID(current_user.tenant_id)
    user_id = uuid.UUID(current_user.sub)

    stmt = select(ClinicalNote).where(
        ClinicalNote.id == note_id,
        ClinicalNote.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinical note not found")

    if note.status == "signed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Note is already signed",
        )

    # Only the author or an admin can sign
    if note.author_id != user_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the note author or an admin can sign this note",
        )

    note.status = "signed"
    note.signed_at = datetime.now(timezone.utc)
    note.signed_by = user_id
    note.version += 1
    await db.flush()

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        action="sign",
        resource_type="clinical_note",
        resource_id=note_id,
    )

    return ClinicalNoteResponse.model_validate(note)
