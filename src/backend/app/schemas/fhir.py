"""
FHIR R4 resource schemas.

These Pydantic models represent a subset of the HL7 FHIR R4 specification
used by the OpenMedRecord FHIR facade.  They are intentionally simplified
compared to the full specification but are structurally compliant with
FHIR R4 JSON serialisation rules.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ── Shared datatypes ─────────────────────────────────────────────────────

class FHIRCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FHIRCodeableConcept(BaseModel):
    coding: List[FHIRCoding] = []
    text: Optional[str] = None


class FHIRReference(BaseModel):
    reference: Optional[str] = None
    display: Optional[str] = None


class FHIRPeriod(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class FHIRIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None


class FHIRHumanName(BaseModel):
    use: Optional[str] = "official"
    family: Optional[str] = None
    given: List[str] = []


class FHIRAddress(BaseModel):
    use: Optional[str] = None
    line: List[str] = []
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None
    country: Optional[str] = None


class FHIRContactPoint(BaseModel):
    system: Optional[str] = None  # phone, email, fax
    value: Optional[str] = None
    use: Optional[str] = None  # home, work, mobile


class FHIRQuantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = "http://unitsofmeasure.org"
    code: Optional[str] = None


# ── Resources ────────────────────────────────────────────────────────────

class FHIRPatient(BaseModel):
    resourceType: Literal["Patient"] = "Patient"
    id: Optional[str] = None
    identifier: List[FHIRIdentifier] = []
    active: Optional[bool] = True
    name: List[FHIRHumanName] = []
    telecom: List[FHIRContactPoint] = []
    gender: Optional[str] = None  # male | female | other | unknown
    birthDate: Optional[date] = None
    address: List[FHIRAddress] = []


class FHIRObservation(BaseModel):
    resourceType: Literal["Observation"] = "Observation"
    id: Optional[str] = None
    status: str = "final"
    category: List[FHIRCodeableConcept] = []
    code: FHIRCodeableConcept = FHIRCodeableConcept()
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    effectiveDateTime: Optional[datetime] = None
    valueQuantity: Optional[FHIRQuantity] = None
    valueString: Optional[str] = None
    performer: List[FHIRReference] = []


class FHIRCondition(BaseModel):
    resourceType: Literal["Condition"] = "Condition"
    id: Optional[str] = None
    clinicalStatus: Optional[FHIRCodeableConcept] = None
    verificationStatus: Optional[FHIRCodeableConcept] = None
    code: FHIRCodeableConcept = FHIRCodeableConcept()
    subject: Optional[FHIRReference] = None
    encounter: Optional[FHIRReference] = None
    onsetDateTime: Optional[date] = None
    abatementDateTime: Optional[date] = None
    recorder: Optional[FHIRReference] = None


class FHIREncounter(BaseModel):
    resourceType: Literal["Encounter"] = "Encounter"
    id: Optional[str] = None
    status: str = "planned"
    class_field: Optional[FHIRCoding] = Field(None, alias="class")
    type: List[FHIRCodeableConcept] = []
    subject: Optional[FHIRReference] = None
    participant: List[Dict[str, Any]] = []
    period: Optional[FHIRPeriod] = None
    reasonCode: List[FHIRCodeableConcept] = []
    location: List[Dict[str, Any]] = []

    model_config = {"populate_by_name": True}


class FHIRBundleEntry(BaseModel):
    fullUrl: Optional[str] = None
    resource: Optional[Dict[str, Any]] = None
    search: Optional[Dict[str, Any]] = None


class FHIRBundleLink(BaseModel):
    relation: str
    url: str


class Bundle(BaseModel):
    """FHIR R4 Bundle (searchset)."""

    resourceType: Literal["Bundle"] = "Bundle"
    id: Optional[str] = None
    type: str = "searchset"
    total: Optional[int] = None
    link: List[FHIRBundleLink] = []
    entry: List[FHIRBundleEntry] = []


class CapabilityStatementRest(BaseModel):
    mode: str = "server"
    resource: List[Dict[str, Any]] = []


class CapabilityStatement(BaseModel):
    """Simplified FHIR R4 CapabilityStatement."""

    resourceType: Literal["CapabilityStatement"] = "CapabilityStatement"
    status: str = "active"
    date: Optional[str] = None
    kind: str = "instance"
    software: Dict[str, str] = {"name": "OpenMedRecord", "version": "0.1.0"}
    fhirVersion: str = "4.0.1"
    format: List[str] = ["json"]
    rest: List[CapabilityStatementRest] = []
