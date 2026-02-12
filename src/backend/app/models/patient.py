"""Patient ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.condition import Condition
    from app.models.encounter import Encounter
    from app.models.medication import MedicationRequest
    from app.models.observation import Observation
    from app.models.order import Order


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    mrn: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # male, female, other, unknown
    sex_assigned_at_birth: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender_identity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sexual_orientation: Mapped[str | None] = mapped_column(String(50), nullable=True)
    race: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(String(35), nullable=True, default="en")
    ssn_hmac: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    ssn_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    preferred_pharmacy_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    fhir_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    insurance_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
    encounters: Mapped[list["Encounter"]] = relationship(
        "Encounter", back_populates="patient", lazy="selectin"
    )
    observations: Mapped[list["Observation"]] = relationship(
        "Observation", back_populates="patient", lazy="selectin"
    )
    conditions: Mapped[list["Condition"]] = relationship(
        "Condition", back_populates="patient", lazy="selectin"
    )
    medication_requests: Mapped[list["MedicationRequest"]] = relationship(
        "MedicationRequest", back_populates="patient", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="patient", lazy="selectin"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="patient", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Patient {self.mrn} {self.last_name}, {self.first_name}>"
