"""
Unit tests for the Patient Service.

Tests cover:
  - Patient creation with validation and duplicate detection
  - Patient retrieval by ID
  - Patient update with partial data
  - Patient list and search
  - Error handling for not found cases
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def _make_mock_patient(**overrides):
    """Create a MagicMock with all fields required by PatientResponse.model_validate."""
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "mrn": "MRN-TEST",
        "first_name": "Test",
        "last_name": "Patient",
        "dob": date(1990, 1, 1),
        "gender": "other",
        "sex_assigned_at_birth": None,
        "gender_identity": None,
        "sexual_orientation": None,
        "race": None,
        "ethnicity": None,
        "preferred_name": None,
        "preferred_language": "en",
        "emergency_contact": None,
        "address": None,
        "phone": None,
        "email": None,
        "insurance_data": None,
        "active": True,
        "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "version": 1,
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestPatientServiceCreate:
    """Tests for create_patient() standalone function."""

    @pytest.mark.asyncio
    async def test_create_patient_success(self):
        """Creating a patient with valid data calls add, flush, and returns a response."""
        from app.schemas.patient import PatientCreate
        from app.services.patient_service import create_patient

        tenant_id = uuid.uuid4()
        patient_data = PatientCreate(
            mrn="MRN-12345",
            first_name="Jane",
            last_name="Doe",
            dob=date(1985, 6, 15),
            gender="female",
            ssn="123-45-6789",
        )

        mock_session = AsyncMock()

        mock_result_mrn = AsyncMock()
        mock_result_mrn.scalar_one_or_none.return_value = None

        mock_result_name = AsyncMock()
        mock_result_name.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [mock_result_mrn, mock_result_name]
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        # Patch PatientResponse.model_validate — the ORM object lacks timestamp
        # defaults because no real DB session triggers the INSERT defaults.
        fake_response = MagicMock()
        fake_response.mrn = patient_data.mrn
        fake_response.first_name = patient_data.first_name
        with patch(
            "app.services.patient_service.PatientResponse"
        ) as MockResponse:
            MockResponse.model_validate.return_value = fake_response
            result = await create_patient(mock_session, tenant_id, patient_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
        assert result is not None
        assert result.mrn == "MRN-12345"
        assert result.first_name == "Jane"

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_mrn_raises(self):
        """Creating a patient with duplicate MRN raises HTTPException 409."""
        from app.schemas.patient import PatientCreate
        from app.services.patient_service import create_patient

        tenant_id = uuid.uuid4()
        patient_data = PatientCreate(
            mrn="MRN-DUP",
            first_name="Jane",
            last_name="Doe",
            dob=date(1985, 6, 15),
            gender="female",
        )

        # Mock database session
        mock_session = AsyncMock()

        # Mock existing patient with same MRN
        existing_patient = MagicMock()
        existing_patient.mrn = "MRN-DUP"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_patient
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await create_patient(mock_session, tenant_id, patient_data)

        assert exc_info.value.status_code == 409
        assert "MRN" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_name_dob_raises(self):
        """Creating a patient with duplicate name+DOB raises HTTPException 409."""
        from app.schemas.patient import PatientCreate
        from app.services.patient_service import create_patient

        tenant_id = uuid.uuid4()
        patient_data = PatientCreate(
            mrn="MRN-NEW",
            first_name="Jane",
            last_name="Doe",
            dob=date(1985, 6, 15),
            gender="female",
        )

        # Mock database session
        mock_session = AsyncMock()

        # MRN check passes (no duplicate)
        mock_result_mrn = AsyncMock()
        mock_result_mrn.scalar_one_or_none.return_value = None

        # Name+DOB check finds duplicate
        existing_patient = MagicMock()
        existing_patient.first_name = "Jane"
        existing_patient.last_name = "Doe"
        existing_patient.mrn = "MRN-OLD"

        mock_result_name = AsyncMock()
        mock_result_name.scalar_one_or_none.return_value = existing_patient

        mock_session.execute.side_effect = [mock_result_mrn, mock_result_name]

        with pytest.raises(HTTPException) as exc_info:
            await create_patient(mock_session, tenant_id, patient_data)

        assert exc_info.value.status_code == 409
        assert "duplicate" in exc_info.value.detail.lower()


class TestPatientServiceGet:
    """Tests for get_patient() standalone function."""

    @pytest.mark.asyncio
    async def test_get_patient_by_id_found(self):
        """Retrieving an existing patient by ID returns PatientResponse."""
        from app.services.patient_service import get_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_patient = _make_mock_patient(
            id=patient_id, tenant_id=tenant_id, first_name="Jane", last_name="Doe"
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result

        result = await get_patient(mock_session, tenant_id, patient_id)

        assert result is not None
        assert result.id == patient_id
        assert result.first_name == "Jane"

    @pytest.mark.asyncio
    async def test_get_patient_by_id_not_found_raises(self):
        """Requesting a non-existent patient ID raises HTTPException 404."""
        from app.services.patient_service import get_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await get_patient(mock_session, tenant_id, patient_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestPatientServiceUpdate:
    """Tests for update_patient() standalone function."""

    @pytest.mark.asyncio
    async def test_update_patient_partial_data(self):
        """Updating a patient with partial data only modifies provided fields."""
        from app.schemas.patient import PatientUpdate
        from app.services.patient_service import update_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_patient = _make_mock_patient(
            id=patient_id,
            tenant_id=tenant_id,
            first_name="Jane",
            last_name="Doe",
            phone="+15551234567",
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()

        update_data = PatientUpdate(phone="+15559999999")
        result = await update_patient(mock_session, tenant_id, patient_id, update_data)

        assert result is not None
        assert mock_patient.phone == "+15559999999"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_nonexistent_patient_raises(self):
        """Updating a non-existent patient raises HTTPException 404."""
        from app.schemas.patient import PatientUpdate
        from app.services.patient_service import update_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        update_data = PatientUpdate(phone="+15559999999")

        with pytest.raises(HTTPException) as exc_info:
            await update_patient(mock_session, tenant_id, patient_id, update_data)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestPatientServiceList:
    """Tests for list_patients() standalone function."""

    @pytest.mark.asyncio
    async def test_list_patients_returns_paginated_results(self):
        """Listing patients returns a PatientList with pagination metadata."""
        from app.services.patient_service import list_patients

        tenant_id = uuid.uuid4()

        mock_patients = [
            _make_mock_patient(
                tenant_id=tenant_id, first_name="Jane", last_name="Doe", mrn="MRN-001"
            ),
            _make_mock_patient(
                tenant_id=tenant_id, first_name="John", last_name="Smith", mrn="MRN-002"
            ),
        ]

        mock_session = AsyncMock()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 2

        # Mock select query
        mock_select_result = AsyncMock()
        mock_select_result.scalars.return_value.all.return_value = mock_patients

        mock_session.execute.side_effect = [mock_count_result, mock_select_result]

        result = await list_patients(mock_session, tenant_id, page=1, page_size=20)

        assert result.total == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_list_patients_empty(self):
        """Listing patients with no results returns empty PatientList."""
        from app.services.patient_service import list_patients

        tenant_id = uuid.uuid4()

        mock_session = AsyncMock()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0

        # Mock select query
        mock_select_result = AsyncMock()
        mock_select_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_select_result]

        result = await list_patients(mock_session, tenant_id, page=1, page_size=20)

        assert result.total == 0
        assert len(result.items) == 0


class TestPatientServiceSearch:
    """Tests for search_patients() standalone function."""

    @pytest.mark.asyncio
    async def test_search_by_query_string(self):
        """Searching by query string returns matching patients."""
        from app.services.patient_service import search_patients

        tenant_id = uuid.uuid4()

        mock_patients = [
            _make_mock_patient(tenant_id=tenant_id, last_name="Doe"),
        ]

        mock_session = AsyncMock()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 1

        # Mock select query
        mock_select_result = AsyncMock()
        mock_select_result.scalars.return_value.all.return_value = mock_patients

        mock_session.execute.side_effect = [mock_count_result, mock_select_result]

        result = await search_patients(
            mock_session, tenant_id, query="Doe", page=1, page_size=20
        )

        assert result.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_search_returns_empty_for_no_match(self):
        """Search with no matches returns an empty PatientList."""
        from app.services.patient_service import search_patients

        tenant_id = uuid.uuid4()

        mock_session = AsyncMock()

        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar.return_value = 0

        # Mock select query
        mock_select_result = AsyncMock()
        mock_select_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_count_result, mock_select_result]

        result = await search_patients(
            mock_session, tenant_id, query="Nonexistent", page=1, page_size=20
        )

        assert result.total == 0
        assert len(result.items) == 0


class TestPatientServiceDelete:
    """Tests for delete_patient() standalone function."""

    @pytest.mark.asyncio
    async def test_delete_patient_soft_deletes(self):
        """Deleting a patient sets active=False (soft delete)."""
        from app.services.patient_service import delete_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_patient = _make_mock_patient(id=patient_id, tenant_id=tenant_id, active=True)

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()

        await delete_patient(mock_session, tenant_id, patient_id)

        # Should set active=False
        assert mock_patient.active is False
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_patient_raises(self):
        """Deleting a non-existent patient raises HTTPException 404."""
        from app.services.patient_service import delete_patient

        tenant_id = uuid.uuid4()
        patient_id = uuid.uuid4()

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await delete_patient(mock_session, tenant_id, patient_id)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()
