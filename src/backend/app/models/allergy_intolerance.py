"""AllergyIntolerance ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.patient import Patient


class AllergyIntolerance(Base):
    __tablename__ = "allergy_intolerances"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("encounters.id"), nullable=True
    )
    clinical_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # active, inactive, resolved
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="confirmed"
    )  # unconfirmed, presumed, confirmed, refuted, entered-in-error
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="allergy"
    )  # allergy, intolerance
    category: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(30)), nullable=True
    )  # food, medication, environment, biologic
    criticality: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # low, high, unable-to-assess
    code_system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="SNOMED-CT"
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_display: Mapped[str] = mapped_column(String(255), nullable=False)
    onset_datetime: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    recorded_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    recorder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reaction: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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
        return f"<AllergyIntolerance {self.code} {self.code_display}>"
