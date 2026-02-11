"""Import all Pydantic schemas."""

from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
)
from app.schemas.condition import ConditionCreate, ConditionResponse
from app.schemas.encounter import EncounterCreate, EncounterResponse, EncounterUpdate
from app.schemas.fhir import (
    Bundle,
    CapabilityStatement,
    FHIRCondition,
    FHIREncounter,
    FHIRObservation,
    FHIRPatient,
)
from app.schemas.medication import MedicationRequestCreate, MedicationRequestResponse
from app.schemas.observation import ObservationCreate, ObservationResponse
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate
from app.schemas.patient import PatientCreate, PatientList, PatientResponse, PatientUpdate
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "AppointmentCreate",
    "AppointmentResponse",
    "AppointmentUpdate",
    "Bundle",
    "CapabilityStatement",
    "ConditionCreate",
    "ConditionResponse",
    "EncounterCreate",
    "EncounterResponse",
    "EncounterUpdate",
    "FHIRCondition",
    "FHIREncounter",
    "FHIRObservation",
    "FHIRPatient",
    "LoginRequest",
    "MedicationRequestCreate",
    "MedicationRequestResponse",
    "ObservationCreate",
    "ObservationResponse",
    "OrderCreate",
    "OrderResponse",
    "OrderUpdate",
    "PatientCreate",
    "PatientList",
    "PatientResponse",
    "PatientUpdate",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
]
