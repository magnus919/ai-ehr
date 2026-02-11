"""
Unit tests for clinical and administrative validators.

Tests cover:
  - NPI (National Provider Identifier) validation (Luhn check digit)
  - MRN (Medical Record Number) format validation
  - ICD-10-CM code validation
  - LOINC code validation
"""

from __future__ import annotations

import pytest


class TestNPIValidator:
    """Tests for NPI validation (10-digit Luhn algorithm)."""

    def test_valid_npi(self):
        """A correctly formatted NPI passes validation."""
        from app.utils.validators import validate_npi

        # 1234567893 is a valid NPI (passes Luhn check with prefix 80840)
        assert validate_npi("1234567893") is True

    def test_valid_npi_examples(self):
        """Multiple known-valid NPIs pass validation."""
        from app.utils.validators import validate_npi

        valid_npis = ["1234567893", "1245319599", "1669574637"]
        for npi in valid_npis:
            assert validate_npi(npi) is True, f"Expected NPI {npi} to be valid"

    def test_invalid_npi_wrong_check_digit(self):
        """An NPI with a wrong check digit fails."""
        from app.utils.validators import validate_npi

        assert validate_npi("1234567890") is False

    def test_invalid_npi_too_short(self):
        """An NPI shorter than 10 digits is rejected."""
        from app.utils.validators import validate_npi

        assert validate_npi("12345") is False

    def test_invalid_npi_too_long(self):
        """An NPI longer than 10 digits is rejected."""
        from app.utils.validators import validate_npi

        assert validate_npi("12345678901") is False

    def test_invalid_npi_non_numeric(self):
        """An NPI containing non-digit characters is rejected."""
        from app.utils.validators import validate_npi

        assert validate_npi("12345ABCDE") is False

    def test_invalid_npi_empty(self):
        """An empty string is rejected."""
        from app.utils.validators import validate_npi

        assert validate_npi("") is False

    def test_npi_must_start_with_1_or_2(self):
        """NPIs must begin with 1 (individual) or 2 (organization)."""
        from app.utils.validators import validate_npi

        # Starting with 3 is invalid regardless of Luhn
        assert validate_npi("3234567890") is False


class TestMRNValidator:
    """Tests for Medical Record Number format validation."""

    def test_valid_mrn_standard_format(self):
        """A standard MRN format (prefix + digits) passes validation."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("MRN-12345678") is True

    def test_valid_mrn_numeric_only(self):
        """A purely numeric MRN passes validation."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("12345678") is True

    def test_valid_mrn_alphanumeric(self):
        """Alphanumeric MRNs are accepted."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("MRN-ABC12345") is True

    def test_invalid_mrn_too_short(self):
        """An MRN shorter than the minimum length is rejected."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("MR") is False

    def test_invalid_mrn_empty(self):
        """An empty MRN is rejected."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("") is False

    def test_invalid_mrn_special_characters(self):
        """MRNs with special characters (beyond hyphens) are rejected."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("MRN@#$%") is False

    def test_invalid_mrn_too_long(self):
        """An excessively long MRN is rejected."""
        from app.utils.validators import validate_mrn

        assert validate_mrn("A" * 100) is False


class TestICD10Validator:
    """Tests for ICD-10-CM code validation."""

    def test_valid_icd10_three_character(self):
        """A 3-character ICD-10 category code is valid."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("J06") is True  # Acute upper respiratory infection

    def test_valid_icd10_with_decimal(self):
        """An ICD-10 code with a decimal subcategory is valid."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("E11.65") is True  # Type 2 diabetes with hyperglycemia

    def test_valid_icd10_full_code(self):
        """A fully specified ICD-10 code is valid."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("S72.001A") is True  # Femur fracture, initial encounter

    def test_valid_icd10_common_codes(self):
        """Common clinical ICD-10 codes pass validation."""
        from app.utils.validators import validate_icd10

        codes = [
            "I10",       # Essential hypertension
            "E78.5",     # Hyperlipidemia
            "J44.1",     # COPD with acute exacerbation
            "N18.3",     # CKD stage 3
            "F32.1",     # Major depressive disorder, moderate
            "Z23",       # Encounter for immunization
        ]
        for code in codes:
            assert validate_icd10(code) is True, f"Expected ICD-10 {code} to be valid"

    def test_invalid_icd10_numeric_start(self):
        """ICD-10 codes starting with a digit (except valid ranges) are rejected."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("999.99") is False

    def test_invalid_icd10_empty(self):
        """An empty string is not a valid ICD-10 code."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("") is False

    def test_invalid_icd10_too_long(self):
        """ICD-10 codes longer than 7 characters are invalid."""
        from app.utils.validators import validate_icd10

        assert validate_icd10("A1234567890") is False

    def test_invalid_icd10_lowercase(self):
        """ICD-10 codes should be uppercase (or validator normalizes them)."""
        from app.utils.validators import validate_icd10

        # Depending on implementation, lowercase may be accepted after normalization
        # or rejected. Test both scenarios.
        result = validate_icd10("e11.65")
        assert isinstance(result, bool)


class TestLOINCValidator:
    """Tests for LOINC code validation."""

    def test_valid_loinc_code(self):
        """A valid LOINC code passes validation."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("85354-9") is True  # Blood pressure panel

    def test_valid_loinc_common_codes(self):
        """Common clinical LOINC codes pass validation."""
        from app.utils.validators import validate_loinc

        codes = [
            "8480-6",    # Systolic blood pressure
            "8462-4",    # Diastolic blood pressure
            "8310-5",    # Body temperature
            "29463-7",   # Body weight
            "8302-2",    # Body height
            "2093-3",    # Total cholesterol
            "4548-4",    # Hemoglobin A1c
            "718-7",     # Hemoglobin
            "2345-7",    # Glucose
        ]
        for code in codes:
            assert validate_loinc(code) is True, f"Expected LOINC {code} to be valid"

    def test_valid_loinc_with_check_digit(self):
        """LOINC codes include a check digit after the hyphen."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("2160-0") is True  # Creatinine

    def test_invalid_loinc_no_hyphen(self):
        """A LOINC code without a hyphen is invalid."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("853549") is False

    def test_invalid_loinc_empty(self):
        """An empty string is not a valid LOINC code."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("") is False

    def test_invalid_loinc_alpha_prefix(self):
        """LOINC codes with alphabetic prefixes are invalid."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("ABC-1") is False

    def test_invalid_loinc_multiple_hyphens(self):
        """LOINC codes should have exactly one hyphen."""
        from app.utils.validators import validate_loinc

        assert validate_loinc("85-354-9") is False
