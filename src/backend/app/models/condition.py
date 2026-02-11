"""Condition (diagnosis) ORM model."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Condition(Base):
    __tablename__ = "conditions"

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
        String(50), nullable=False, default="ICD-10"
    )
    display: Mapped[str] = mapped_column(String(255), nullable=False)
    clinical_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # active, recurrence, relapse, inactive, remission, resolved
    verification_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="confirmed"
    )  # unconfirmed, provisional, differential, confirmed, refuted
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    abatement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recorder_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="conditions", lazy="selectin"
    )
    encounter: Mapped["Encounter | None"] = relationship(
        "Encounter", back_populates="conditions", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Condition {self.code} {self.display}>"
