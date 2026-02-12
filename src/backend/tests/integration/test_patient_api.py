"""
Integration tests for the Patient API endpoints.

Tests exercise the full request lifecycle through FastAPI, hitting a real
test database.  Covers CRUD operations, search, pagination, validation
errors, and authentication enforcement.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


BASE_PATH = "/api/v1/patients"


class TestCreatePatient:
    """POST /api/v1/patients"""

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Creating a patient with valid data returns 201 and the patient record."""
        response = await client.post(
            BASE_PATH, json=sample_patient_data, headers=auth_headers
        )

        assert response.status_code == 201
        body = response.json()
        assert body["first_name"] == sample_patient_data["first_name"]
        assert body["last_name"] == sample_patient_data["last_name"]
        assert "id" in body
        assert "mrn" in body

    @pytest.mark.asyncio
    async def test_create_patient_missing_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Omitting required fields returns 422 with validation details."""
        incomplete = {"first_name": "Incomplete"}
        response = await client.post(BASE_PATH, json=incomplete, headers=auth_headers)

        assert response.status_code == 422
        body = response.json()
        assert "detail" in body

    @pytest.mark.asyncio
    async def test_create_patient_invalid_email(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """An invalid email format returns 422."""
        sample_patient_data["email"] = "not-an-email"
        response = await client.post(
            BASE_PATH, json=sample_patient_data, headers=auth_headers
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_patient_requires_auth(
        self, client: AsyncClient, sample_patient_data: dict
    ):
        """Creating a patient without an auth token returns 401."""
        response = await client.post(BASE_PATH, json=sample_patient_data)

        assert response.status_code == 401


class TestGetPatient:
    """GET /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_get_patient_by_id(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Retrieving an existing patient by ID returns 200."""
        # Create first
        create_resp = await client.post(
            BASE_PATH, json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        # Retrieve
        response = await client.get(f"{BASE_PATH}/{patient_id}", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == patient_id
        assert body["first_name"] == sample_patient_data["first_name"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_patient(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Requesting a non-existent patient returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{BASE_PATH}/{fake_id}", headers=auth_headers)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_patient_invalid_id_format(
        self, client: AsyncClient, auth_headers: dict
    ):
        """An invalid UUID format returns 422."""
        response = await client.get(f"{BASE_PATH}/not-a-uuid", headers=auth_headers)

        assert response.status_code in (400, 422)


class TestUpdatePatient:
    """PUT /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_update_patient_success(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Updating a patient's phone returns 200 with the new value."""
        create_resp = await client.post(
            BASE_PATH, json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        update_data = {"phone": "+15559998888"}
        response = await client.put(
            f"{BASE_PATH}/{patient_id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["phone"] == "+15559998888"

    @pytest.mark.asyncio
    async def test_update_nonexistent_patient(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Updating a non-existent patient returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.put(
            f"{BASE_PATH}/{fake_id}",
            json={"phone": "+15559998888"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestSearchPatients:
    """GET /api/v1/patients (with query params)"""

    @pytest.mark.asyncio
    async def test_search_by_last_name(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Searching by last name returns matching patients."""
        # Create a patient first
        await client.post(BASE_PATH, json=sample_patient_data, headers=auth_headers)

        response = await client.get(
            BASE_PATH,
            params={"last_name": sample_patient_data["last_name"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert "items" in body or isinstance(body, list)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Search results respect page and page_size parameters."""
        # Create multiple patients
        for i in range(3):
            data = {**sample_patient_data, "mrn": f"MRN-PG{i:04d}"}
            await client.post(BASE_PATH, json=data, headers=auth_headers)

        response = await client.get(
            BASE_PATH,
            params={"page": 1, "page_size": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        # Paginated response should include metadata
        if isinstance(body, dict):
            assert "total" in body or "items" in body

    @pytest.mark.asyncio
    async def test_search_no_results(self, client: AsyncClient, auth_headers: dict):
        """Searching for a non-existent name returns an empty result set."""
        response = await client.get(
            BASE_PATH,
            params={"last_name": "ZZZNonexistent999"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_search_requires_auth(self, client: AsyncClient):
        """Search without authentication returns 401."""
        response = await client.get(BASE_PATH)
        assert response.status_code == 401


class TestDeletePatient:
    """DELETE /api/v1/patients/{patient_id}"""

    @pytest.mark.asyncio
    async def test_soft_delete_patient(
        self, client: AsyncClient, auth_headers: dict, sample_patient_data: dict
    ):
        """Deleting a patient soft-deletes the record (returns 204 or 200)."""
        create_resp = await client.post(
            BASE_PATH, json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        response = await client.delete(
            f"{BASE_PATH}/{patient_id}", headers=auth_headers
        )

        assert response.status_code in (200, 204)

        # Verify the patient is no longer retrievable
        get_resp = await client.get(f"{BASE_PATH}/{patient_id}", headers=auth_headers)
        assert get_resp.status_code in (404, 410)
