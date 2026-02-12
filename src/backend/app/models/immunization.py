"""Immunization ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.patient import Patient


class Immunization(Base):
    __tablename__ = "immunizations"

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
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="completed"
    )  # completed, entered-in-error, not-done
    vaccine_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    vaccine_code_system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="CVX"
    )
    vaccine_display: Mapped[str] = mapped_column(String(255), nullable=False)
    occurrence_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    site_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    route_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    dose_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    performer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
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
        return f"<Immunization {self.vaccine_code} {self.vaccine_display}>"
