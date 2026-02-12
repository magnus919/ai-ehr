"""
FHIR R4 resource transformation service.

Converts internal ORM models to FHIR R4 JSON representations and vice
versa.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from app.models.condition import Condition
from app.models.encounter import Encounter
from app.models.observation import Observation
from app.models.patient import Patient
from app.schemas.fhir import (
    Bundle,
    FHIRAddress,
    FHIRBundleEntry,
    FHIRBundleLink,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRCondition,
    FHIRContactPoint,
    FHIREncounter,
    FHIRHumanName,
    FHIRIdentifier,
    FHIRObservation,
    FHIRPatient,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
)


# ── Patient ──────────────────────────────────────────────────────────────


def patient_to_fhir(patient: Patient) -> FHIRPatient:
    """Convert an internal Patient model to a FHIR R4 Patient resource."""

    telecom: list[FHIRContactPoint] = []
    if patient.phone:
        telecom.append(
            FHIRContactPoint(system="phone", value=patient.phone, use="home")
        )
    if patient.email:
        telecom.append(FHIRContactPoint(system="email", value=patient.email))

    address_list: list[FHIRAddress] = []
    if patient.address:
        a = patient.address
        address_list.append(
            FHIRAddress(
                use=a.get("use", "home"),
                line=a.get("line", []),
                city=a.get("city"),
                state=a.get("state"),
                postalCode=a.get("postalCode"),
                country=a.get("country"),
            )
        )

    return FHIRPatient(
        id=str(patient.id),
        identifier=[
            FHIRIdentifier(system="urn:oid:openmedrecord:mrn", value=patient.mrn)
        ],
        active=patient.active,
        name=[
            FHIRHumanName(
                use="official",
                family=patient.last_name,
                given=[patient.first_name],
            )
        ],
        telecom=telecom,
        gender=patient.gender,
        birthDate=patient.dob,
        address=address_list,
    )


def fhir_to_patient_data(fhir: FHIRPatient) -> Dict[str, Any]:
    """Extract internal patient fields from a FHIR Patient resource."""

    data: Dict[str, Any] = {}
    data["gender"] = fhir.gender

    if fhir.birthDate:
        data["dob"] = fhir.birthDate

    if fhir.name:
        name = fhir.name[0]
        data["last_name"] = name.family or ""
        data["first_name"] = name.given[0] if name.given else ""

    if fhir.identifier:
        for ident in fhir.identifier:
            if ident.system and "mrn" in ident.system.lower():
                data["mrn"] = ident.value

    if fhir.telecom:
        for tc in fhir.telecom:
            if tc.system == "phone":
                data["phone"] = tc.value
            elif tc.system == "email":
                data["email"] = tc.value

    if fhir.address:
        a = fhir.address[0]
        data["address"] = {
            "use": a.use,
            "line": a.line,
            "city": a.city,
            "state": a.state,
            "postalCode": a.postalCode,
            "country": a.country,
        }

    data["active"] = fhir.active if fhir.active is not None else True
    return data


# ── Observation ──────────────────────────────────────────────────────────


def observation_to_fhir(obs: Observation) -> FHIRObservation:
    """Convert an internal Observation model to FHIR R4."""

    value_quantity = None
    value_string = None
    if obs.value_type == "numeric" and obs.value_numeric is not None:
        value_quantity = FHIRQuantity(value=obs.value_numeric, unit=obs.unit)
    elif obs.value_string:
        value_string = obs.value_string

    subject_ref = FHIRReference(reference=f"Patient/{obs.patient_id}")
    encounter_ref = (
        FHIRReference(reference=f"Encounter/{obs.encounter_id}")
        if obs.encounter_id
        else None
    )

    return FHIRObservation(
        id=str(obs.id),
        status=obs.status,
        code=FHIRCodeableConcept(
            coding=[
                FHIRCoding(system=obs.code_system, code=obs.code, display=obs.display)
            ],
            text=obs.display,
        ),
        subject=subject_ref,
        encounter=encounter_ref,
        effectiveDateTime=obs.effective_date,
        valueQuantity=value_quantity,
        valueString=value_string,
    )


# ── Condition ────────────────────────────────────────────────────────────


def condition_to_fhir(cond: Condition) -> FHIRCondition:
    """Convert an internal Condition model to FHIR R4."""

    return FHIRCondition(
        id=str(cond.id),
        clinicalStatus=FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/condition-clinical",
                    code=cond.clinical_status,
                )
            ]
        ),
        verificationStatus=FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    code=cond.verification_status,
                )
            ]
        ),
        code=FHIRCodeableConcept(
            coding=[
                FHIRCoding(
                    system=cond.code_system, code=cond.code, display=cond.display
                )
            ],
            text=cond.display,
        ),
        subject=FHIRReference(reference=f"Patient/{cond.patient_id}"),
        encounter=(
            FHIRReference(reference=f"Encounter/{cond.encounter_id}")
            if cond.encounter_id
            else None
        ),
        onsetDateTime=cond.onset_date,
        abatementDateTime=cond.abatement_date,
    )


# ── Encounter ────────────────────────────────────────────────────────────


def encounter_to_fhir(enc: Encounter) -> FHIREncounter:
    """Convert an internal Encounter model to FHIR R4."""

    return FHIREncounter(
        id=str(enc.id),
        status=enc.status,
        **{
            "class": FHIRCoding(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code=enc.encounter_type,
                display=enc.encounter_type,
            )
        },
        type=[
            FHIRCodeableConcept(
                coding=[FHIRCoding(code=enc.encounter_type, display=enc.encounter_type)]
            )
        ],
        subject=FHIRReference(reference=f"Patient/{enc.patient_id}"),
        participant=[
            {
                "individual": {
                    "reference": f"Practitioner/{enc.practitioner_id}",
                }
            }
        ],
        period=FHIRPeriod(start=enc.start_time, end=enc.end_time),
        reasonCode=([FHIRCodeableConcept(text=enc.reason)] if enc.reason else []),
        location=([{"location": {"display": enc.location}}] if enc.location else []),
    )


# ── Bundle helpers ───────────────────────────────────────────────────────


def build_bundle(
    resources: List[Any],
    total: int,
    resource_type: str,
    base_url: str,
    page: int = 1,
    page_size: int = 20,
) -> Bundle:
    """Wrap a list of FHIR resources in a searchset Bundle."""

    entries = [
        FHIRBundleEntry(
            fullUrl=f"{base_url}/fhir/{resource_type}/{r.id}",
            resource=r.model_dump(by_alias=True, exclude_none=True),
            search={"mode": "match"},
        )
        for r in resources
    ]

    links = [
        FHIRBundleLink(
            relation="self",
            url=f"{base_url}/fhir/{resource_type}?_offset={page}&_count={page_size}",
        )
    ]

    return Bundle(
        id=str(uuid.uuid4()),
        type="searchset",
        total=total,
        link=links,
        entry=entries,
    )
