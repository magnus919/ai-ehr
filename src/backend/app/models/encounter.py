"""Encounter ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("patients.id"), nullable=False, index=True
    )
    practitioner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True
    )
    encounter_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # ambulatory, emergency, inpatient, virtual
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="planned"
    )  # planned, in-progress, completed, cancelled
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="encounters", lazy="selectin"
    )
    practitioner: Mapped["User"] = relationship(
        "User",
        back_populates="encounters",
        foreign_keys=[practitioner_id],
        lazy="selectin",
    )
    observations: Mapped[list["Observation"]] = relationship(
        "Observation", back_populates="encounter", lazy="selectin"
    )
    conditions: Mapped[list["Condition"]] = relationship(
        "Condition", back_populates="encounter", lazy="selectin"
    )
    medication_requests: Mapped[list["MedicationRequest"]] = relationship(
        "MedicationRequest", back_populates="encounter", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="encounter", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Encounter {self.id} type={self.encounter_type} status={self.status}>"
