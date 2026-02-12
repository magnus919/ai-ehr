"""Observation ORM model (vital signs, lab results, etc.)."""

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


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id"), nullable=False, index=True
    )
    encounter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("encounters.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    code_system: Mapped[str] = mapped_column(
        String(50), nullable=False, default="LOINC"
    )
    display: Mapped[str] = mapped_column(String(255), nullable=False)
    value_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="numeric"
    )  # numeric, string, boolean, dateTime
    value_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_numeric: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    effective_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="final"
    )  # registered, preliminary, final, amended, cancelled
    performer_id: Mapped[uuid.UUID | None] = mapped_column(
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
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="observations", lazy="selectin"
    )
    encounter: Mapped["Encounter | None"] = relationship(
        "Encounter", back_populates="observations", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Observation {self.code} {self.display}>"
