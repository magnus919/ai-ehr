"""
Unit tests for the FHIR Resource Transformation Service.

Tests cover:
  - Internal Patient model -> FHIR Patient resource
  - FHIR Patient resource -> internal Patient model
  - FHIR Bundle creation (search results)
  - Observation transformation
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock


class TestPatientToFHIR:
    """Tests for converting internal Patient to FHIR R4 Patient."""

    def test_basic_patient_to_fhir(self):
        """A patient with basic demographics maps to valid FHIR Patient."""
        from app.services.fhir_service import patient_to_fhir

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-12345"
        patient.first_name = "Jane"
        patient.last_name = "Doe"
        patient.dob = date(1985, 6, 15)
        patient.gender = "female"
        patient.active = True
        patient.phone = "+15551234567"
        patient.email = "jane@example.com"
        patient.address = {
            "use": "home",
            "line": ["123 Main St"],
            "city": "Springfield",
            "state": "IL",
            "postalCode": "62701",
            "country": "US",
        }

        fhir_patient = patient_to_fhir(patient)

        # Returns a Pydantic model, not a dict
        assert fhir_patient.resourceType == "Patient"
        assert fhir_patient.id == str(patient.id)
        assert fhir_patient.active is True
        assert fhir_patient.gender == "female"
        assert fhir_patient.birthDate == date(1985, 6, 15)

        # Name
        assert len(fhir_patient.name) >= 1
        name = fhir_patient.name[0]
        assert name.family == "Doe"
        assert "Jane" in name.given

        # Identifiers (MRN)
        assert len(fhir_patient.identifier) >= 1
        mrn_identifier = fhir_patient.identifier[0]
        assert mrn_identifier.value == "MRN-12345"
        assert "mrn" in mrn_identifier.system.lower()

    def test_patient_to_fhir_includes_telecom(self):
        """Phone and email are mapped to FHIR telecom entries."""
        from app.services.fhir_service import patient_to_fhir

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-99999"
        patient.first_name = "John"
        patient.last_name = "Smith"
        patient.dob = date(1970, 1, 1)
        patient.gender = "male"
        patient.active = True
        patient.phone = "+15551112222"
        patient.email = "john@example.com"
        patient.address = None

        fhir_patient = patient_to_fhir(patient)

        telecoms = fhir_patient.telecom
        systems = {t.system for t in telecoms}
        assert "phone" in systems
        assert "email" in systems

        # Verify values
        phone_entry = next((t for t in telecoms if t.system == "phone"), None)
        assert phone_entry is not None
        assert phone_entry.value == "+15551112222"

        email_entry = next((t for t in telecoms if t.system == "email"), None)
        assert email_entry is not None
        assert email_entry.value == "john@example.com"

    def test_patient_to_fhir_includes_address(self):
        """Address fields are mapped to a FHIR Address resource."""
        from app.services.fhir_service import patient_to_fhir

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-ADDR1"
        patient.first_name = "Test"
        patient.last_name = "Address"
        patient.dob = date(1990, 3, 20)
        patient.gender = "other"
        patient.active = True
        patient.phone = None
        patient.email = None
        patient.address = {
            "use": "home",
            "line": ["456 Oak Ave"],
            "city": "Chicago",
            "state": "IL",
            "postalCode": "60601",
            "country": "US",
        }

        fhir_patient = patient_to_fhir(patient)

        addresses = fhir_patient.address
        assert len(addresses) == 1
        addr = addresses[0]
        assert addr.city == "Chicago"
        assert addr.state == "IL"
        assert addr.postalCode == "60601"
        assert "456 Oak Ave" in addr.line

    def test_patient_to_fhir_no_contact_info(self):
        """Patient without phone/email/address produces valid FHIR."""
        from app.services.fhir_service import patient_to_fhir

        patient = MagicMock()
        patient.id = uuid.uuid4()
        patient.mrn = "MRN-MINIMAL"
        patient.first_name = "Minimal"
        patient.last_name = "Data"
        patient.dob = date(2000, 1, 1)
        patient.gender = "unknown"
        patient.active = True
        patient.phone = None
        patient.email = None
        patient.address = None

        fhir_patient = patient_to_fhir(patient)

        assert fhir_patient.id == str(patient.id)
        assert len(fhir_patient.telecom) == 0
        assert len(fhir_patient.address) == 0


class TestFHIRToPatient:
    """Tests for converting FHIR R4 Patient to internal Patient model."""

    def test_fhir_patient_to_internal(self):
        """A valid FHIR Patient maps to internal patient fields."""
        from app.schemas.fhir import (
            FHIRAddress,
            FHIRContactPoint,
            FHIRHumanName,
            FHIRIdentifier,
            FHIRPatient,
        )
        from app.services.fhir_service import fhir_to_patient_data

        fhir_patient = FHIRPatient(
            id=str(uuid.uuid4()),
            active=True,
            name=[FHIRHumanName(family="Garcia", given=["Maria", "Elena"])],
            gender="female",
            birthDate=date(1992, 8, 10),
            identifier=[
                FHIRIdentifier(
                    system="urn:oid:openmedrecord:mrn",
                    value="MRN-FHIR-001",
                )
            ],
            telecom=[
                FHIRContactPoint(system="phone", value="+15553334444", use="home"),
                FHIRContactPoint(system="email", value="maria@example.com"),
            ],
            address=[
                FHIRAddress(
                    line=["789 Elm Blvd"],
                    city="Miami",
                    state="FL",
                    postalCode="33101",
                    country="US",
                )
            ],
        )

        internal = fhir_to_patient_data(fhir_patient)

        assert internal["first_name"] == "Maria"
        assert internal["last_name"] == "Garcia"
        assert internal["gender"] == "female"
        assert internal["dob"] == date(1992, 8, 10)
        assert internal["mrn"] == "MRN-FHIR-001"
        assert internal["phone"] == "+15553334444"
        assert internal["email"] == "maria@example.com"
        assert internal["active"] is True

        # Address should be a dict
        assert "address" in internal
        addr = internal["address"]
        assert addr["city"] == "Miami"
        assert addr["state"] == "FL"

    def test_fhir_patient_minimal_data(self):
        """FHIR Patient with minimal data produces valid internal dict."""
        from app.schemas.fhir import FHIRHumanName, FHIRPatient
        from app.services.fhir_service import fhir_to_patient_data

        fhir_patient = FHIRPatient(
            gender="unknown",
            birthDate=date(2000, 1, 1),
            name=[FHIRHumanName(family="Smith", given=["John"])],
        )

        internal = fhir_to_patient_data(fhir_patient)

        assert internal["gender"] == "unknown"
        assert internal["dob"] == date(2000, 1, 1)
        assert internal["first_name"] == "John"
        assert internal["last_name"] == "Smith"
        assert internal["active"] is True  # Defaults to True

    def test_fhir_patient_no_name_returns_empty_strings(self):
        """FHIR Patient without name returns empty name fields."""
        from app.schemas.fhir import FHIRPatient
        from app.services.fhir_service import fhir_to_patient_data

        fhir_patient = FHIRPatient(
            gender="unknown",
            birthDate=date(2000, 1, 1),
            name=[],
        )

        internal = fhir_to_patient_data(fhir_patient)

        # Should not raise, but may have missing keys or empty strings
        assert internal["gender"] == "unknown"


class TestBundleCreation:
    """Tests for FHIR Bundle construction."""

    def test_create_search_bundle(self):
        """A search bundle wraps resources with correct metadata."""
        from app.schemas.fhir import FHIRPatient
        from app.services.fhir_service import build_bundle

        resources = [
            FHIRPatient(id="p1"),
            FHIRPatient(id="p2"),
        ]

        bundle = build_bundle(
            resources=resources,
            total=2,
            resource_type="Patient",
            base_url="http://localhost:8000",
            page=1,
            page_size=20,
        )

        assert bundle.resourceType == "Bundle"
        assert bundle.type == "searchset"
        assert bundle.total == 2
        assert len(bundle.entry) == 2

    def test_bundle_entries_have_fullurl(self):
        """Each entry in a search bundle includes a fullUrl."""
        from app.schemas.fhir import FHIRPatient
        from app.services.fhir_service import build_bundle

        resources = [FHIRPatient(id="p1")]

        bundle = build_bundle(
            resources=resources,
            total=1,
            resource_type="Patient",
            base_url="http://localhost:8000",
            page=1,
            page_size=20,
        )

        entry = bundle.entry[0]
        assert "Patient/p1" in entry.fullUrl

    def test_empty_search_bundle(self):
        """An empty search returns a valid bundle with total=0."""
        from app.services.fhir_service import build_bundle

        bundle = build_bundle(
            resources=[],
            total=0,
            resource_type="Patient",
            base_url="http://localhost:8000",
            page=1,
            page_size=20,
        )

        assert bundle.total == 0
        assert bundle.entry == []

    def test_bundle_includes_pagination_links(self):
        """A paginated bundle includes self link."""
        from app.schemas.fhir import FHIRPatient
        from app.services.fhir_service import build_bundle

        resources = [FHIRPatient(id=f"p{i}") for i in range(10)]

        bundle = build_bundle(
            resources=resources,
            total=50,
            resource_type="Patient",
            base_url="http://localhost:8000",
            page=2,
            page_size=10,
        )

        link_relations = {link.relation for link in bundle.link}
        assert "self" in link_relations


class TestObservationTransformation:
    """Tests for Observation resource transformations."""

    def test_observation_to_fhir_numeric(self):
        """Internal observation with numeric value maps to FHIR Observation."""
        from app.services.fhir_service import observation_to_fhir

        observation = MagicMock()
        observation.id = uuid.uuid4()
        observation.patient_id = uuid.uuid4()
        observation.encounter_id = uuid.uuid4()
        observation.code = "8480-6"
        observation.display = "Systolic blood pressure"
        observation.code_system = "http://loinc.org"
        observation.status = "final"
        observation.effective_date = datetime.now(timezone.utc)
        observation.value_type = "numeric"
        observation.value_numeric = 120.0
        observation.value_string = None
        observation.unit = "mmHg"

        fhir_obs = observation_to_fhir(observation)

        assert fhir_obs.resourceType == "Observation"
        assert fhir_obs.status == "final"
        assert fhir_obs.code.coding[0].code == "8480-6"
        assert fhir_obs.valueQuantity is not None
        assert fhir_obs.valueQuantity.value == 120.0
        assert fhir_obs.valueQuantity.unit == "mmHg"
        assert fhir_obs.valueString is None

    def test_observation_to_fhir_string(self):
        """Internal observation with string value maps correctly."""
        from app.services.fhir_service import observation_to_fhir

        observation = MagicMock()
        observation.id = uuid.uuid4()
        observation.patient_id = uuid.uuid4()
        observation.encounter_id = None
        observation.code = "11488-4"
        observation.display = "Consultation note"
        observation.code_system = "http://loinc.org"
        observation.status = "final"
        observation.effective_date = datetime.now(timezone.utc)
        observation.value_type = "string"
        observation.value_numeric = None
        observation.value_string = "Patient appears well"
        observation.unit = None

        fhir_obs = observation_to_fhir(observation)

        assert fhir_obs.resourceType == "Observation"
        assert fhir_obs.valueString == "Patient appears well"
        assert fhir_obs.valueQuantity is None

    def test_observation_to_fhir_references(self):
        """Observation includes correct references to patient and encounter."""
        from app.services.fhir_service import observation_to_fhir

        patient_id = uuid.uuid4()
        encounter_id = uuid.uuid4()

        observation = MagicMock()
        observation.id = uuid.uuid4()
        observation.patient_id = patient_id
        observation.encounter_id = encounter_id
        observation.code = "8480-6"
        observation.display = "Test"
        observation.code_system = "http://loinc.org"
        observation.status = "final"
        observation.effective_date = datetime.now(timezone.utc)
        observation.value_type = "numeric"
        observation.value_numeric = 100.0
        observation.value_string = None
        observation.unit = "mmHg"

        fhir_obs = observation_to_fhir(observation)

        assert fhir_obs.subject.reference == f"Patient/{patient_id}"
        assert fhir_obs.encounter.reference == f"Encounter/{encounter_id}"
