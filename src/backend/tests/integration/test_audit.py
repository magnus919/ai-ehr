"""
Integration tests for audit logging.

Verifies that:
  - All PHI access events are logged
  - Audit log entries contain required fields
  - Audit logs are immutable (cannot be modified or deleted)
  - Audit log search and filtering works correctly
"""

from __future__ import annotations

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient


PATIENTS_PATH = "/api/v1/patients"
AUDIT_PATH = "/api/v1/audit-logs"


class TestPHIAccessAuditLogging:
    """Verify that all PHI access events create audit log entries."""

    @pytest.mark.asyncio
    async def test_patient_creation_is_audited(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Creating a patient generates an audit log entry."""
        # Create a patient
        create_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        assert create_resp.status_code == 201
        patient_id = create_resp.json()["id"]

        # Query audit logs for the creation event (resource_type is lowercase
        # in the route handler's record_audit call)
        audit_resp = await client.get(
            AUDIT_PATH,
            params={
                "resource_type": "patient",
                "action": "create",
            },
            headers=auth_headers,
        )

        assert audit_resp.status_code == 200
        entries = audit_resp.json()
        items = entries.get("items", entries) if isinstance(entries, dict) else entries
        assert len(items) >= 1

        entry = items[0]
        assert entry["resource_type"] == "patient"
        assert entry["action"] == "create"

    @pytest.mark.asyncio
    async def test_patient_read_is_audited(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Reading a patient record generates an audit log entry."""
        # Create
        create_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        # Read
        await client.get(f"{PATIENTS_PATH}/{patient_id}", headers=auth_headers)

        # Check audit
        audit_resp = await client.get(
            AUDIT_PATH,
            params={
                "resource_type": "patient",
                "action": "read",
            },
            headers=auth_headers,
        )

        assert audit_resp.status_code == 200
        entries = audit_resp.json()
        items = entries.get("items", entries) if isinstance(entries, dict) else entries
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_patient_update_is_audited(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Updating a patient record generates an audit log entry."""
        # Create
        create_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        patient_id = create_resp.json()["id"]

        # Update
        await client.put(
            f"{PATIENTS_PATH}/{patient_id}",
            json={"phone": "+15550001111"},
            headers=auth_headers,
        )

        # Check audit
        audit_resp = await client.get(
            AUDIT_PATH,
            params={
                "resource_type": "patient",
                "action": "update",
            },
            headers=auth_headers,
        )

        assert audit_resp.status_code == 200
        entries = audit_resp.json()
        items = entries.get("items", entries) if isinstance(entries, dict) else entries
        assert len(items) >= 1


class TestAuditLogFields:
    """Verify audit log entries contain all required fields."""

    @pytest.mark.asyncio
    async def test_audit_entry_has_required_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Each audit entry includes timestamp, user, action, resource."""
        # Generate an audit event
        create_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        assert create_resp.status_code == 201

        audit_resp = await client.get(
            AUDIT_PATH,
            params={"resource_type": "patient"},
            headers=auth_headers,
        )

        entries = audit_resp.json()
        items = entries.get("items", entries) if isinstance(entries, dict) else entries

        for entry in items:
            assert "timestamp" in entry, "Missing timestamp"
            assert "user_id" in entry, "Missing user_id"
            assert "action" in entry, "Missing action"
            assert "resource_type" in entry, "Missing resource_type"

    @pytest.mark.asyncio
    async def test_audit_entry_timestamps_are_utc(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_patient_data: dict,
    ):
        """Audit timestamps are in UTC ISO-8601 format."""
        create_resp = await client.post(
            PATIENTS_PATH, json=sample_patient_data, headers=auth_headers
        )
        assert create_resp.status_code == 201

        audit_resp = await client.get(
            AUDIT_PATH,
            params={"resource_type": "patient"},
            headers=auth_headers,
        )

        entries = audit_resp.json()
        items = entries.get("items", entries) if isinstance(entries, dict) else entries

        for entry in items:
            ts = entry["timestamp"]
            # Should be parseable as ISO 8601
            parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            assert parsed.tzinfo is not None


class TestAuditLogImmutability:
    """Verify that audit logs cannot be modified or deleted."""

    @pytest.mark.asyncio
    async def test_audit_logs_cannot_be_deleted(
        self, client: AsyncClient, auth_headers: dict
    ):
        """DELETE on audit entries returns 404 or 405 (no such route)."""
        response = await client.delete(
            f"{AUDIT_PATH}/{uuid.uuid4()}", headers=auth_headers
        )
        assert response.status_code in (403, 404, 405)

    @pytest.mark.asyncio
    async def test_audit_logs_cannot_be_updated(
        self, client: AsyncClient, auth_headers: dict
    ):
        """PUT on audit entries returns 404 or 405 (no such route)."""
        response = await client.put(
            f"{AUDIT_PATH}/{uuid.uuid4()}",
            json={"action": "tampered"},
            headers=auth_headers,
        )
        assert response.status_code in (403, 404, 405)

    @pytest.mark.asyncio
    async def test_audit_endpoint_requires_auth(self, client: AsyncClient):
        """Accessing audit logs without authentication returns 401."""
        response = await client.get(AUDIT_PATH)
        assert response.status_code in (401, 403)


class TestAuditLogSearch:
    """Verify audit log search and filtering capabilities."""

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client: AsyncClient, auth_headers: dict):
        """Audit logs can be filtered by date range."""
        response = await client.get(
            AUDIT_PATH,
            params={
                "from_date": "2024-01-01T00:00:00Z",
                "to_date": "2099-12-31T23:59:59Z",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_user(self, client: AsyncClient, auth_headers: dict):
        """Audit logs can be filtered by user ID."""
        response = await client.get(
            AUDIT_PATH,
            params={"user_id": str(uuid.uuid4())},
            headers=auth_headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_filter_by_resource_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Audit logs can be filtered by resource type."""
        response = await client.get(
            AUDIT_PATH,
            params={"resource_type": "patient"},
            headers=auth_headers,
        )

        assert response.status_code == 200
