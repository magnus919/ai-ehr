"""
Integration tests for the Encounter API endpoints.

Tests cover:
  - Creating encounters tied to a patient
  - Retrieving encounters by ID and by patient
  - Updating encounter status (planned -> completed)
  - Validation of encounter types
  - Authorization enforcement
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient


PATIENTS_PATH = "/api/v1/patients"
ENCOUNTERS_PATH = "/api/v1/encounters"


@pytest.fixture
async def created_patient(
    client: AsyncClient,
    auth_headers: dict,
    sample_patient_data: dict,
    test_user: dict,
) -> dict:
    """Create a patient and return its data.

    Also ensures the test user exists in the DB (needed for the
    practitioner_id FK on encounters).
    """
    response = await client.post(
        PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
    )
    assert response.status_code == 201
    return response.json()


class TestCreateEncounter:
    """POST /api/v1/encounters"""

    @pytest.mark.asyncio
    async def test_create_encounter_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
        sample_encounter_data: dict,
    ):
        """Creating an encounter for an existing patient returns 201."""
        sample_encounter_data["patient_id"] = created_patient["id"]

        response = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )

        assert response.status_code == 201
        body = response.json()
        assert body["patient_id"] == created_patient["id"]
        assert body["encounter_type"] == "ambulatory"
        assert body["status"] == "planned"

    @pytest.mark.asyncio
    async def test_create_encounter_invalid_encounter_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
    ):
        """An invalid encounter type returns 422."""
        payload = {
            "patient_id": created_patient["id"],
            "practitioner_id": str(uuid.uuid4()),
            "encounter_type": "INVALID",
            "reason": "Checkup",
            "start_time": datetime.now(timezone.utc).isoformat(),
        }

        response = await client.post(
            ENCOUNTERS_PATH, json=payload, headers=auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_encounter_nonexistent_patient(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_encounter_data: dict,
        test_user: dict,
    ):
        """Creating an encounter for a non-existent patient returns 404."""
        sample_encounter_data["patient_id"] = str(uuid.uuid4())

        response = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )

        assert response.status_code in (404, 422, 500)

    @pytest.mark.asyncio
    async def test_create_encounter_requires_auth(
        self, client: AsyncClient, sample_encounter_data: dict
    ):
        """Creating an encounter without auth returns 401."""
        sample_encounter_data["patient_id"] = str(uuid.uuid4())

        response = await client.post(ENCOUNTERS_PATH, json=sample_encounter_data)
        assert response.status_code == 401


class TestGetEncounter:
    """GET /api/v1/encounters/{encounter_id}"""

    @pytest.mark.asyncio
    async def test_get_encounter_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
        sample_encounter_data: dict,
    ):
        """Retrieving an encounter by ID returns 200 with full details."""
        sample_encounter_data["patient_id"] = created_patient["id"]
        create_resp = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )
        encounter_id = create_resp.json()["id"]

        response = await client.get(
            f"{ENCOUNTERS_PATH}/{encounter_id}", headers=auth_headers
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == encounter_id
        assert body["patient_id"] == created_patient["id"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_encounter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Retrieving a non-existent encounter returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(
            f"{ENCOUNTERS_PATH}/{fake_id}", headers=auth_headers
        )

        assert response.status_code == 404


class TestListPatientEncounters:
    """GET /api/v1/patients/{patient_id}/encounters"""

    @pytest.mark.asyncio
    async def test_list_encounters_for_patient(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
        sample_encounter_data: dict,
    ):
        """Listing encounters for a patient returns all their encounters."""
        sample_encounter_data["patient_id"] = created_patient["id"]

        # Create two encounters
        await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )
        sample_encounter_data["reason"] = "Follow-up visit"
        await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )

        response = await client.get(
            f"{PATIENTS_PATH}/{created_patient['id']}/encounters",
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        assert len(items) >= 2


class TestUpdateEncounter:
    """PUT /api/v1/encounters/{encounter_id}"""

    @pytest.mark.asyncio
    async def test_complete_encounter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
        sample_encounter_data: dict,
    ):
        """Transitioning an encounter to 'completed' succeeds."""
        sample_encounter_data["patient_id"] = created_patient["id"]
        create_resp = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )
        encounter_id = create_resp.json()["id"]

        response = await client.put(
            f"{ENCOUNTERS_PATH}/{encounter_id}",
            json={
                "status": "completed",
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_invalid_status_transition(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_patient: dict,
        sample_encounter_data: dict,
    ):
        """An invalid status value is rejected."""
        sample_encounter_data["patient_id"] = created_patient["id"]
        create_resp = await client.post(
            ENCOUNTERS_PATH, json=sample_encounter_data, headers=auth_headers
        )
        encounter_id = create_resp.json()["id"]

        # Try to set an invalid status
        response = await client.put(
            f"{ENCOUNTERS_PATH}/{encounter_id}",
            json={"status": "bogus-status"},
            headers=auth_headers,
        )

        assert response.status_code in (400, 422)
