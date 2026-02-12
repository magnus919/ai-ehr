"""ClinicalNote ORM model for clinical documentation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.patient import Patient


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("encounters.id"), nullable=True, index=True
    )
    note_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # progress, soap, h_and_p, discharge, procedure, consultation
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="in-progress"
    )  # in-progress, completed, signed, amended, entered-in-error
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    content_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_psychotherapy_note: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_42cfr_part2: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    signed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    patient: Mapped["Patient"] = relationship("Patient", lazy="selectin")
    encounter: Mapped["Encounter | None"] = relationship("Encounter", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ClinicalNote {self.id} type={self.note_type} status={self.status}>"
