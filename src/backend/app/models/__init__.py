"""Import all ORM models so that Alembic and ``Base.metadata`` see them."""

from app.models.allergy_intolerance import AllergyIntolerance
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.clinical_note import ClinicalNote
from app.models.condition import Condition
from app.models.consent import Consent
from app.models.encounter import Encounter
from app.models.immunization import Immunization
from app.models.medication import MedicationRequest
from app.models.observation import Observation
from app.models.order import Order
from app.models.patient import Patient
from app.models.role import Permission, Role, UserRole
from app.models.user import User

__all__ = [
    "AllergyIntolerance",
    "Appointment",
    "AuditLog",
    "ClinicalNote",
    "Condition",
    "Consent",
    "Encounter",
    "Immunization",
    "MedicationRequest",
    "Observation",
    "Order",
    "Patient",
    "Permission",
    "Role",
    "User",
    "UserRole",
]
