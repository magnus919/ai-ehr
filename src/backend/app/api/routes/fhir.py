"""
FHIR R4 facade endpoints.

GET  /fhir/metadata         - CapabilityStatement
GET  /fhir/Patient           - Search patients (FHIR Bundle)
GET  /fhir/Patient/{id}      - Read a single patient (FHIR Patient)
GET  /fhir/Observation       - Search observations (FHIR Bundle)
GET  /fhir/Condition         - Search conditions (FHIR Bundle)
GET  /fhir/Encounter         - Search encounters (FHIR Bundle)

All responses conform to the FHIR R4 JSON representation.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import record_audit
from app.core.config import settings
from app.core.database import get_db
from app.core.security import TokenPayload, get_current_user
from app.models.condition import Condition
from app.models.encounter import Encounter
from app.models.observation import Observation
from app.models.patient import Patient
from app.schemas.fhir import CapabilityStatement, CapabilityStatementRest
from app.services.fhir_service import (
    build_bundle,
    condition_to_fhir,
    encounter_to_fhir,
    observation_to_fhir,
    patient_to_fhir,
)

router = APIRouter(prefix="/fhir", tags=["FHIR R4"])


def _base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")


# ── CapabilityStatement ──────────────────────────────────────────────────

@router.get("/metadata", response_model=CapabilityStatement, summary="FHIR CapabilityStatement")
async def capability_statement() -> CapabilityStatement:
    """Return the server's FHIR CapabilityStatement (no auth required)."""

    resources = []
    for rtype in ("Patient", "Observation", "Condition", "Encounter"):
        resources.append(
            {
                "type": rtype,
                "interaction": [
                    {"code": "read"},
                    {"code": "search-type"},
                ],
                "searchParam": _search_params_for(rtype),
            }
        )

    return CapabilityStatement(
        status="active",
        date=datetime.utcnow().date().isoformat(),
        kind="instance",
        software={"name": settings.APP_NAME, "version": settings.APP_VERSION},
        fhirVersion="4.0.1",
        format=["json"],
        rest=[CapabilityStatementRest(mode="server", resource=resources)],
    )


def _search_params_for(resource_type: str) -> list[dict]:
    """Return FHIR-style search parameter declarations per resource."""
    common = [{"name": "_id", "type": "token"}]
    mapping = {
        "Patient": [
            {"name": "name", "type": "string"},
            {"name": "family", "type": "string"},
            {"name": "given", "type": "string"},
            {"name": "birthdate", "type": "date"},
            {"name": "gender", "type": "token"},
            {"name": "identifier", "type": "token"},
        ],
        "Observation": [
            {"name": "patient", "type": "reference"},
            {"name": "code", "type": "token"},
            {"name": "date", "type": "date"},
            {"name": "status", "type": "token"},
        ],
        "Condition": [
            {"name": "patient", "type": "reference"},
            {"name": "code", "type": "token"},
            {"name": "clinical-status", "type": "token"},
        ],
        "Encounter": [
            {"name": "patient", "type": "reference"},
            {"name": "status", "type": "token"},
            {"name": "date", "type": "date"},
        ],
    }
    return common + mapping.get(resource_type, [])


# ── Patient ──────────────────────────────────────────────────────────────

@router.get("/Patient", summary="Search patients (FHIR)")
async def search_patients(
    request: Request,
    name: Optional[str] = Query(None),
    family: Optional[str] = Query(None),
    given: Optional[str] = Query(None),
    birthdate: Optional[date] = Query(None),
    gender: Optional[str] = Query(None),
    identifier: Optional[str] = Query(None),
    _count: int = Query(20, alias="_count", ge=1, le=100),
    _offset: int = Query(0, alias="_offset", ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Patient).where(Patient.tenant_id == tenant_id, Patient.active.is_(True))

    if name:
        term = f"%{name.lower()}%"
        stmt = stmt.where(
            func.lower(Patient.first_name).like(term)
            | func.lower(Patient.last_name).like(term)
        )
    if family:
        stmt = stmt.where(func.lower(Patient.last_name) == family.lower())
    if given:
        stmt = stmt.where(func.lower(Patient.first_name) == given.lower())
    if birthdate:
        stmt = stmt.where(Patient.dob == birthdate)
    if gender:
        stmt = stmt.where(Patient.gender == gender)
    if identifier:
        stmt = stmt.where(Patient.mrn == identifier)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset(_offset).limit(_count)
    result = await db.execute(stmt)
    patients = result.scalars().all()

    fhir_patients = [patient_to_fhir(p) for p in patients]
    bundle = build_bundle(
        fhir_patients, total, "Patient", _base_url(request), page=_offset, page_size=_count
    )

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="fhir_patient_search",
        details={"total": total},
    )

    return bundle.model_dump(exclude_none=True)


@router.get("/Patient/{patient_id}", summary="Read patient (FHIR)")
async def read_patient(
    patient_id: uuid.UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Patient).where(Patient.id == patient_id, Patient.tenant_id == tenant_id)
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    await record_audit(
        db,
        tenant_id=tenant_id,
        user_id=uuid.UUID(current_user.sub),
        action="read",
        resource_type="fhir_patient",
        resource_id=patient_id,
    )

    return patient_to_fhir(patient).model_dump(exclude_none=True)


# ── Observation ──────────────────────────────────────────────────────────

@router.get("/Observation", summary="Search observations (FHIR)")
async def search_observations(
    request: Request,
    patient: Optional[uuid.UUID] = Query(None),
    code: Optional[str] = Query(None),
    date_param: Optional[date] = Query(None, alias="date"),
    status_param: Optional[str] = Query(None, alias="status"),
    _count: int = Query(20, alias="_count", ge=1, le=100),
    _offset: int = Query(0, alias="_offset", ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Observation).where(Observation.tenant_id == tenant_id)

    if patient:
        stmt = stmt.where(Observation.patient_id == patient)
    if code:
        stmt = stmt.where(Observation.code == code)
    if date_param:
        stmt = stmt.where(func.date(Observation.effective_date) == date_param)
    if status_param:
        stmt = stmt.where(Observation.status == status_param)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset(_offset).limit(_count)
    result = await db.execute(stmt)
    observations = result.scalars().all()

    fhir_obs = [observation_to_fhir(o) for o in observations]
    bundle = build_bundle(
        fhir_obs, total, "Observation", _base_url(request), page=_offset, page_size=_count
    )
    return bundle.model_dump(exclude_none=True)


# ── Condition ────────────────────────────────────────────────────────────

@router.get("/Condition", summary="Search conditions (FHIR)")
async def search_conditions(
    request: Request,
    patient: Optional[uuid.UUID] = Query(None),
    code: Optional[str] = Query(None),
    clinical_status: Optional[str] = Query(None, alias="clinical-status"),
    _count: int = Query(20, alias="_count", ge=1, le=100),
    _offset: int = Query(0, alias="_offset", ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Condition).where(Condition.tenant_id == tenant_id)

    if patient:
        stmt = stmt.where(Condition.patient_id == patient)
    if code:
        stmt = stmt.where(Condition.code == code)
    if clinical_status:
        stmt = stmt.where(Condition.clinical_status == clinical_status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset(_offset).limit(_count)
    result = await db.execute(stmt)
    conditions = result.scalars().all()

    fhir_conds = [condition_to_fhir(c) for c in conditions]
    bundle = build_bundle(
        fhir_conds, total, "Condition", _base_url(request), page=_offset, page_size=_count
    )
    return bundle.model_dump(exclude_none=True)


# ── Encounter ────────────────────────────────────────────────────────────

@router.get("/Encounter", summary="Search encounters (FHIR)")
async def search_encounters(
    request: Request,
    patient: Optional[uuid.UUID] = Query(None),
    status_param: Optional[str] = Query(None, alias="status"),
    date_param: Optional[date] = Query(None, alias="date"),
    _count: int = Query(20, alias="_count", ge=1, le=100),
    _offset: int = Query(0, alias="_offset", ge=0),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    tenant_id = uuid.UUID(current_user.tenant_id)
    stmt = select(Encounter).where(Encounter.tenant_id == tenant_id)

    if patient:
        stmt = stmt.where(Encounter.patient_id == patient)
    if status_param:
        stmt = stmt.where(Encounter.status == status_param)
    if date_param:
        stmt = stmt.where(func.date(Encounter.start_time) == date_param)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.offset(_offset).limit(_count)
    result = await db.execute(stmt)
    encounters = result.scalars().all()

    fhir_encs = [encounter_to_fhir(e) for e in encounters]
    bundle = build_bundle(
        fhir_encs, total, "Encounter", _base_url(request), page=_offset, page_size=_count
    )
    return bundle.model_dump(exclude_none=True)
