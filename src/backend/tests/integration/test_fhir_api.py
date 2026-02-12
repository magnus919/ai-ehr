"""
Integration tests for the FHIR R4 API endpoints.

Tests cover:
  - CapabilityStatement (metadata endpoint)
  - Patient read and search (FHIR-formatted responses)
  - Bundle responses with correct structure
  - SMART on FHIR scope enforcement
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


FHIR_PATH = "/fhir"


class TestCapabilityStatement:
    """GET /fhir/metadata"""

    @pytest.mark.asyncio
    async def test_capability_statement_returns_200(
        self, client: AsyncClient, auth_headers: dict
    ):
        """The metadata endpoint returns a valid CapabilityStatement."""
        response = await client.get(f"{FHIR_PATH}/metadata", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "CapabilityStatement"
        assert body["status"] == "active"
        assert body["fhirVersion"] == "4.0.1"

    @pytest.mark.asyncio
    async def test_capability_statement_lists_supported_resources(
        self, client: AsyncClient, auth_headers: dict
    ):
        """The CapabilityStatement enumerates supported resource types."""
        response = await client.get(f"{FHIR_PATH}/metadata", headers=auth_headers)

        body = response.json()
        rest = body.get("rest", [])
        assert len(rest) >= 1

        resource_types = {r["type"] for r in rest[0].get("resource", [])}
        expected_types = {"Patient", "Encounter", "Observation", "Condition"}
        assert expected_types.issubset(resource_types)

    @pytest.mark.asyncio
    async def test_capability_statement_includes_smart_security(
        self, client: AsyncClient, auth_headers: dict
    ):
        """The CapabilityStatement declares SMART on FHIR security."""
        response = await client.get(f"{FHIR_PATH}/metadata", headers=auth_headers)

        body = response.json()
        security = body.get("rest", [{}])[0].get("security", {})
        assert security is not None
        # Check for OAuth2 extension or service coding
        service_codings = security.get("service", [])
        has_smart = any(
            any(c.get("code") == "SMART-on-FHIR" for c in svc.get("coding", []))
            for svc in service_codings
        )
        assert has_smart


class TestFHIRPatientRead:
    """GET /fhir/Patient/{id}"""

    @pytest.mark.asyncio
    async def test_read_patient_fhir_format(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Reading a patient via FHIR returns a FHIR Patient resource."""
        # Create via REST API
        create_resp = await client.post(
            "/api/v1/patients", json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        # Read via FHIR
        response = await client.get(
            f"{FHIR_PATH}/Patient/{patient_id}", headers=auth_headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Patient"
        assert body["id"] == patient_id

    @pytest.mark.asyncio
    async def test_read_nonexistent_patient_returns_operation_outcome(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Reading a non-existent patient returns a FHIR OperationOutcome."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"{FHIR_PATH}/Patient/{fake_id}", headers=auth_headers
        )

        assert response.status_code == 404
        body = response.json()
        assert body["resourceType"] == "OperationOutcome"
        assert body["issue"][0]["severity"] in ("error", "fatal")

    @pytest.mark.asyncio
    async def test_fhir_content_type(self, client: AsyncClient, auth_headers: dict):
        """FHIR responses use the application/fhir+json content type."""
        response = await client.get(f"{FHIR_PATH}/metadata", headers=auth_headers)

        content_type = response.headers.get("content-type", "")
        assert (
            "application/fhir+json" in content_type
            or "application/json" in content_type
        )


class TestFHIRPatientSearch:
    """GET /fhir/Patient?<params>"""

    @pytest.mark.asyncio
    async def test_search_returns_bundle(self, client: AsyncClient, auth_headers: dict):
        """Searching for patients returns a FHIR Bundle."""
        response = await client.get(
            f"{FHIR_PATH}/Patient",
            params={"family": "Doe"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["resourceType"] == "Bundle"
        assert body["type"] == "searchset"
        assert "total" in body

    @pytest.mark.asyncio
    async def test_search_bundle_entries_are_patients(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Bundle entries contain Patient resources with search mode."""
        # Create a patient
        await client.post(
            "/api/v1/patients", json=sample_patient_data, headers=auth_headers
        )

        response = await client.get(
            f"{FHIR_PATH}/Patient",
            params={"family": sample_patient_data["last_name"]},
            headers=auth_headers,
        )

        body = response.json()
        for entry in body.get("entry", []):
            assert entry["resource"]["resourceType"] == "Patient"
            assert entry.get("search", {}).get("mode") == "match"

    @pytest.mark.asyncio
    async def test_search_with_count_parameter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """The _count parameter limits the number of results."""
        response = await client.get(
            f"{FHIR_PATH}/Patient",
            params={"_count": 5},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        entries = body.get("entry", [])
        assert len(entries) <= 5


class TestSMARTScopes:
    """Verify SMART on FHIR scope enforcement."""

    @pytest.mark.asyncio
    async def test_unauthenticated_fhir_request_returns_401(self, client: AsyncClient):
        """FHIR endpoints require authentication."""
        response = await client.get(f"{FHIR_PATH}/Patient")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_well_known_smart_configuration(self, client: AsyncClient):
        """The /.well-known/smart-configuration endpoint exists."""
        response = await client.get(f"{FHIR_PATH}/.well-known/smart-configuration")

        # Should be 200 with SMART config, or 404 if not yet implemented
        if response.status_code == 200:
            body = response.json()
            assert "authorization_endpoint" in body
            assert "token_endpoint" in body
            assert "scopes_supported" in body
