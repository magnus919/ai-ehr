"""Order (lab, imaging, referral) ORM model."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.encounter import Encounter
    from app.models.patient import Patient


class Order(Base):
    __tablename__ = "orders"

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
    order_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # lab, imaging, referral
    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    display: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active"
    )  # draft, active, completed, cancelled
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="routine"
    )  # routine, urgent, stat, asap
    ordering_provider_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(
        "Patient", back_populates="orders", lazy="selectin"
    )
    encounter: Mapped["Encounter | None"] = relationship(
        "Encounter", back_populates="orders", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Order {self.order_type} {self.code} {self.display}>"
