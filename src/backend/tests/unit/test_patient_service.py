"""
Unit tests for the Patient Service.

Tests cover:
  - Patient creation with validation
  - Patient retrieval by ID and MRN
  - Patient update with partial data
  - Search with filters (name, DOB, MRN)
  - Duplicate detection logic
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Module under test -- imported with mocks for DB dependencies
# ---------------------------------------------------------------------------


class TestPatientServiceCreate:
    """Tests for PatientService.create_patient()."""

    @pytest.mark.asyncio
    async def test_create_patient_success(self, sample_patient_data):
        """Creating a patient with valid data returns a patient with an ID."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        service = PatientService(mock_session)

        with patch.object(service, "_check_duplicate", return_value=None):
            patient = await service.create_patient(sample_patient_data)

        assert patient is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_patient_missing_required_field(self):
        """Omitting a required field raises a validation error."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        service = PatientService(mock_session)

        incomplete_data = {
            "first_name": "Jane",
            # missing last_name, date_of_birth, gender
        }

        with pytest.raises((ValueError, KeyError)):
            await service.create_patient(incomplete_data)

    @pytest.mark.asyncio
    async def test_create_patient_invalid_date_of_birth(self, sample_patient_data):
        """A future date of birth is rejected."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        service = PatientService(mock_session)

        sample_patient_data["date_of_birth"] = "2099-01-01"

        with pytest.raises(ValueError, match="date_of_birth"):
            await service.create_patient(sample_patient_data)


class TestPatientServiceGet:
    """Tests for PatientService.get_patient() and get_patient_by_mrn()."""

    @pytest.mark.asyncio
    async def test_get_patient_by_id_found(self):
        """Retrieving an existing patient by ID returns the patient."""
        from app.services.patient_service import PatientService

        patient_id = uuid.uuid4()
        mock_patient = MagicMock()
        mock_patient.id = patient_id
        mock_patient.first_name = "Jane"
        mock_patient.last_name = "Doe"

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        result = await service.get_patient(patient_id)

        assert result is not None
        assert result.id == patient_id

    @pytest.mark.asyncio
    async def test_get_patient_by_id_not_found(self):
        """Requesting a non-existent patient ID returns None."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        result = await service.get_patient(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_patient_by_mrn(self):
        """Retrieving a patient by MRN returns the correct patient."""
        from app.services.patient_service import PatientService

        mock_patient = MagicMock()
        mock_patient.mrn = "MRN-ABC12345"

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_patient
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        result = await service.get_patient_by_mrn("MRN-ABC12345")

        assert result is not None
        assert result.mrn == "MRN-ABC12345"


class TestPatientServiceUpdate:
    """Tests for PatientService.update_patient()."""

    @pytest.mark.asyncio
    async def test_update_patient_partial_data(self):
        """Updating a patient with partial data only modifies provided fields."""
        from app.services.patient_service import PatientService

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

        service = PatientService(mock_session)
        updated = await service.update_patient(patient_id, {"phone": "+15559999999"})

        assert updated.phone == "+15559999999"
        # first_name should remain unchanged
        assert updated.first_name == "Jane"

    @pytest.mark.asyncio
    async def test_update_nonexistent_patient_raises(self):
        """Updating a non-existent patient raises an error."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)

        with pytest.raises(ValueError, match="not found"):
            await service.update_patient(uuid.uuid4(), {"phone": "+15559999999"})


class TestPatientServiceSearch:
    """Tests for PatientService.search_patients()."""

    @pytest.mark.asyncio
    async def test_search_by_last_name(self):
        """Searching by last name returns matching patients."""
        from app.services.patient_service import PatientService

        mock_patients = [MagicMock(last_name="Doe"), MagicMock(last_name="Doe")]

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_patients
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        results = await service.search_patients(last_name="Doe")

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_with_multiple_filters(self):
        """Combining search filters narrows results correctly."""
        from app.services.patient_service import PatientService

        mock_patient = MagicMock(
            first_name="Jane",
            last_name="Doe",
            date_of_birth=date(1985, 6, 15),
        )

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_patient]
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        results = await service.search_patients(
            last_name="Doe",
            date_of_birth="1985-06-15",
        )

        assert len(results) == 1
        assert results[0].first_name == "Jane"

    @pytest.mark.asyncio
    async def test_search_returns_empty_for_no_match(self):
        """Search with no matches returns an empty list."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        results = await service.search_patients(last_name="Nonexistent")

        assert results == []


class TestPatientDuplicateDetection:
    """Tests for duplicate patient detection logic."""

    @pytest.mark.asyncio
    async def test_exact_duplicate_detected(self, sample_patient_data):
        """An exact match on name + DOB + SSN is flagged as a duplicate."""
        from app.services.patient_service import PatientService

        existing_patient = MagicMock()
        existing_patient.first_name = "Jane"
        existing_patient.last_name = "Doe"
        existing_patient.date_of_birth = date(1985, 6, 15)

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [existing_patient]
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        duplicates = await service._check_duplicate(sample_patient_data)

        assert duplicates is not None
        assert len(duplicates) >= 1

    @pytest.mark.asyncio
    async def test_no_duplicate_for_unique_patient(self, sample_patient_data):
        """A patient with unique demographics has no duplicates."""
        from app.services.patient_service import PatientService

        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        service = PatientService(mock_session)
        duplicates = await service._check_duplicate(sample_patient_data)

        assert duplicates is None or len(duplicates) == 0
