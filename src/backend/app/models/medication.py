"""MedicationRequest ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.patient import Patient


class MedicationRequest(Base):
    __tablename__ = "medication_requests"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("encounters.id"), nullable=True, index=True
    )
    medication_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    medication_display: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str | None] = mapped_column(String(200), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # oral, IV, IM, topical, etc.
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # active, on-hold, cancelled, completed, stopped
    prescriber_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    refills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
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
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="medication_requests", lazy="selectin"
    )
    encounter: Mapped["Encounter | None"] = relationship(
        "Encounter", back_populates="medication_requests", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<MedicationRequest {self.medication_code} {self.medication_display}>"
