"""Import all ORM models so that Alembic and ``Base.metadata`` see them."""

from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.condition import Condition
from app.models.encounter import Encounter
from app.models.medication import MedicationRequest
from app.models.observation import Observation
from app.models.order import Order
from app.models.patient import Patient
from app.models.user import User

__all__ = [
    "Appointment",
    "AuditLog",
    "Condition",
    "Encounter",
    "MedicationRequest",
    "Observation",
    "Order",
    "Patient",
    "User",
]
