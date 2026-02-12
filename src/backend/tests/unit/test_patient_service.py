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
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


class TestPatientServiceCreate:
    """Tests for create_patient() standalone function."""

    @pytest.mark.asyncio
    async def test_create_patient_success(self):
        """Creating a patient with valid data returns a PatientResponse."""
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

        # Mock database session
        mock_session = AsyncMock()

        # Mock the duplicate check query (returns no duplicates)
        mock_result_mrn = AsyncMock()
        mock_result_mrn.scalar_one_or_none.return_value = None

        mock_result_name = AsyncMock()
        mock_result_name.scalar_one_or_none.return_value = None

        # First call checks MRN, second checks name+DOB
        mock_session.execute.side_effect = [mock_result_mrn, mock_result_name]

        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await create_patient(mock_session, tenant_id, patient_data)

        # Should call add and flush
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

        # Result should be a PatientResponse (returned from model_validate)
        assert result is not None

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

        mock_patient = MagicMock()
        mock_patient.id = patient_id
        mock_patient.first_name = "Jane"
        mock_patient.last_name = "Doe"

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result

        result = await get_patient(mock_session, tenant_id, patient_id)

        # Should return a PatientResponse (model_validate is called)
        assert result is not None

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

        mock_patient = MagicMock()
        mock_patient.id = patient_id
        mock_patient.first_name = "Jane"
        mock_patient.last_name = "Doe"
        mock_patient.phone = "+15551234567"

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result
        mock_session.flush = AsyncMock()

        update_data = PatientUpdate(phone="+15559999999")
        await update_patient(mock_session, tenant_id, patient_id, update_data)

        # Phone should be updated on the mock patient
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
            MagicMock(id=uuid.uuid4(), first_name="Jane", last_name="Doe"),
            MagicMock(id=uuid.uuid4(), first_name="John", last_name="Smith"),
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
            MagicMock(id=uuid.uuid4(), last_name="Doe"),
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

        mock_patient = MagicMock()
        mock_patient.id = patient_id
        mock_patient.active = True

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
