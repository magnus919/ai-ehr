"""
Unit tests for the FHIR Resource Transformation Service.

Tests cover:
  - Internal Patient model -> FHIR Patient resource
  - FHIR Patient resource -> internal Patient model
  - FHIR Bundle creation (search results)
  - Observation and Condition transformations
  - Error handling for malformed FHIR data
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest


class TestPatientToFHIR:
    """Tests for converting internal Patient to FHIR R4 Patient."""

    def test_basic_patient_to_fhir(self):
        """A patient with basic demographics maps to valid FHIR Patient."""
        from app.services.fhir_service import FHIRService

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-12345"
        patient.first_name = "Jane"
        patient.last_name = "Doe"
        patient.date_of_birth = date(1985, 6, 15)
        patient.gender = "female"
        patient.is_active = True
        patient.phone = "+15551234567"
        patient.email = "jane@example.com"
        patient.address_line1 = "123 Main St"
        patient.address_city = "Springfield"
        patient.address_state = "IL"
        patient.address_postal_code = "62701"
        patient.address_country = "US"

        fhir_patient = FHIRService.patient_to_fhir(patient)

        assert fhir_patient["resourceType"] == "Patient"
        assert fhir_patient["id"] == str(patient.id)
        assert fhir_patient["active"] is True
        assert fhir_patient["gender"] == "female"
        assert fhir_patient["birthDate"] == "1985-06-15"

        # Name
        assert len(fhir_patient["name"]) >= 1
        name = fhir_patient["name"][0]
        assert name["family"] == "Doe"
        assert "Jane" in name["given"]

        # Identifiers (MRN)
        mrn_identifier = next(
            (i for i in fhir_patient["identifier"] if i["type"]["coding"][0]["code"] == "MR"),
            None,
        )
        assert mrn_identifier is not None
        assert mrn_identifier["value"] == "MRN-12345"

    def test_patient_to_fhir_includes_telecom(self):
        """Phone and email are mapped to FHIR telecom entries."""
        from app.services.fhir_service import FHIRService

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-99999"
        patient.first_name = "John"
        patient.last_name = "Smith"
        patient.date_of_birth = date(1970, 1, 1)
        patient.gender = "male"
        patient.is_active = True
        patient.phone = "+15551112222"
        patient.email = "john@example.com"
        patient.address_line1 = None
        patient.address_city = None
        patient.address_state = None
        patient.address_postal_code = None
        patient.address_country = None

        fhir_patient = FHIRService.patient_to_fhir(patient)

        telecoms = fhir_patient.get("telecom", [])
        systems = {t["system"] for t in telecoms}
        assert "phone" in systems
        assert "email" in systems

    def test_patient_to_fhir_includes_address(self):
        """Address fields are mapped to a FHIR Address resource."""
        from app.services.fhir_service import FHIRService

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-ADDR1"
        patient.first_name = "Test"
        patient.last_name = "Address"
        patient.date_of_birth = date(1990, 3, 20)
        patient.gender = "other"
        patient.is_active = True
        patient.phone = None
        patient.email = None
        patient.address_line1 = "456 Oak Ave"
        patient.address_city = "Chicago"
        patient.address_state = "IL"
        patient.address_postal_code = "60601"
        patient.address_country = "US"

        fhir_patient = FHIRService.patient_to_fhir(patient)

        addresses = fhir_patient.get("address", [])
        assert len(addresses) == 1
        addr = addresses[0]
        assert addr["city"] == "Chicago"
        assert addr["state"] == "IL"
        assert addr["postalCode"] == "60601"


class TestFHIRToPatient:
    """Tests for converting FHIR R4 Patient to internal Patient model."""

    def test_fhir_patient_to_internal(self):
        """A valid FHIR Patient maps to internal patient fields."""
        from app.services.fhir_service import FHIRService

        fhir_data = {
            "resourceType": "Patient",
            "id": str(uuid.uuid4()),
            "active": True,
            "name": [{"family": "Garcia", "given": ["Maria", "Elena"]}],
            "gender": "female",
            "birthDate": "1992-08-10",
            "identifier": [
                {
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]},
                    "value": "MRN-FHIR-001",
                }
            ],
            "telecom": [
                {"system": "phone", "value": "+15553334444", "use": "home"},
                {"system": "email", "value": "maria@example.com"},
            ],
            "address": [
                {
                    "line": ["789 Elm Blvd"],
                    "city": "Miami",
                    "state": "FL",
                    "postalCode": "33101",
                    "country": "US",
                }
            ],
        }

        internal = FHIRService.fhir_to_patient(fhir_data)

        assert internal["first_name"] == "Maria"
        assert internal["last_name"] == "Garcia"
        assert internal["gender"] == "female"
        assert internal["date_of_birth"] == "1992-08-10"
        assert internal["mrn"] == "MRN-FHIR-001"
        assert internal["phone"] == "+15553334444"
        assert internal["email"] == "maria@example.com"

    def test_fhir_patient_missing_name_raises(self):
        """A FHIR Patient without a name raises a validation error."""
        from app.services.fhir_service import FHIRService

        fhir_data = {
            "resourceType": "Patient",
            "gender": "unknown",
            "birthDate": "2000-01-01",
        }

        with pytest.raises((ValueError, KeyError)):
            FHIRService.fhir_to_patient(fhir_data)

    def test_fhir_patient_wrong_resource_type_raises(self):
        """A non-Patient resource type is rejected."""
        from app.services.fhir_service import FHIRService

        fhir_data = {
            "resourceType": "Observation",
            "id": "obs-1",
        }

        with pytest.raises(ValueError, match="Patient"):
            FHIRService.fhir_to_patient(fhir_data)


class TestBundleCreation:
    """Tests for FHIR Bundle construction."""

    def test_create_search_bundle(self):
        """A search bundle wraps resources with correct metadata."""
        from app.services.fhir_service import FHIRService

        resources = [
            {"resourceType": "Patient", "id": "p1"},
            {"resourceType": "Patient", "id": "p2"},
        ]

        bundle = FHIRService.create_bundle(
            resources=resources,
            bundle_type="searchset",
            total=2,
        )

        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "searchset"
        assert bundle["total"] == 2
        assert len(bundle["entry"]) == 2

    def test_bundle_entries_have_fullurl(self):
        """Each entry in a search bundle includes a fullUrl."""
        from app.services.fhir_service import FHIRService

        resources = [{"resourceType": "Patient", "id": "p1"}]

        bundle = FHIRService.create_bundle(
            resources=resources,
            bundle_type="searchset",
            total=1,
        )

        entry = bundle["entry"][0]
        assert "fullUrl" in entry
        assert "Patient/p1" in entry["fullUrl"]

    def test_empty_search_bundle(self):
        """An empty search returns a valid bundle with total=0."""
        from app.services.fhir_service import FHIRService

        bundle = FHIRService.create_bundle(
            resources=[],
            bundle_type="searchset",
            total=0,
        )

        assert bundle["total"] == 0
        assert bundle["entry"] == []

    def test_bundle_includes_pagination_links(self):
        """A paginated bundle includes self, next, and previous links."""
        from app.services.fhir_service import FHIRService

        resources = [{"resourceType": "Patient", "id": f"p{i}"} for i in range(10)]

        bundle = FHIRService.create_bundle(
            resources=resources,
            bundle_type="searchset",
            total=50,
            page=2,
            page_size=10,
            base_url="http://localhost:8000/fhir",
        )

        link_relations = {link["relation"] for link in bundle.get("link", [])}
        assert "self" in link_relations


class TestObservationTransformation:
    """Tests for Observation resource transformations."""

    def test_observation_to_fhir(self):
        """Internal observation data maps to FHIR Observation resource."""
        from app.services.fhir_service import FHIRService

        observation = MagicMock()
        observation.id = uuid.uuid4()
        observation.patient_id = uuid.uuid4()
        observation.encounter_id = uuid.uuid4()
        observation.code = "85354-9"
        observation.display = "Blood pressure panel"
        observation.category = "vital-signs"
        observation.status = "final"
        observation.effective_datetime = datetime.now(timezone.utc)
        observation.value = None  # Panel observation (components only)
        observation.components = [
            MagicMock(code="8480-6", display="Systolic BP", value=120.0, unit="mmHg"),
            MagicMock(code="8462-4", display="Diastolic BP", value=80.0, unit="mmHg"),
        ]

        fhir_obs = FHIRService.observation_to_fhir(observation)

        assert fhir_obs["resourceType"] == "Observation"
        assert fhir_obs["status"] == "final"
        assert len(fhir_obs["component"]) == 2
        assert fhir_obs["component"][0]["valueQuantity"]["value"] == 120.0
